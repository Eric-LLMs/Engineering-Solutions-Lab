# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: comment_analyzer_service.py
@Author:
@Time: 11月 13, 2020
"""

import json
import os
import sys
import traceback

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(__dir__, '../interfaces'))
sys.path.append(os.path.abspath(os.path.join(__dir__, '../')))

from framework.security import sign
from live_comments_analysis_pb2 import RequestInfo, ResponseInfo, RtnCode
from live_comments_analysis_pb2_grpc import CommentAnalyzerServiceServicer, add_CommentAnalyzerServiceServicer_to_server
from framework.interface import GrpcInterface, GrpcService
from live_comments_analysis_pb2 import CommentAnalyzerResponse, ResponseInfo, CommentClusteringResponse
from framework import app
from google.protobuf.json_format import MessageToDict

class CommentAnalyzerService(GrpcService, CommentAnalyzerServiceServicer):
    # ak/sk 对
    AK_SK_KEYS = {
        '1585300274-4800963': 'b568HD4rPDbT3anbTrn2P4wT'
    }

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__()
        self.logger.info('{} initialized'.format(self))

    def addToGrpcInterface(self, interface: GrpcInterface):
        '''
        加入到grpc接口
        @param interface: grpc 接口
        '''
        add_CommentAnalyzerServiceServicer_to_server(self, interface.grpc)
        self.logger.info('added grpc service {} to {}'.format(self, interface))

    def beforeRequest(self, request, context, logInfo):
        '''
        请求前置处理
        '''
        self.logger.debug('REQUEST_MESSAGE: {}'.format(json.dumps(MessageToDict(request, True, True, True), ensure_ascii=False)))

        if type(request) is RequestInfo:
            requestInfo = request
        else:
            requestInfo = request.info

        if requestInfo.source != '':
            logInfo['source'] = requestInfo.source
        else:
            logInfo['source'] = '-'
        logInfo['appid'] = requestInfo.appid
        if requestInfo.logid != '':
            logInfo['logid'] = requestInfo.logid
        if requestInfo.peerip != '':
            logInfo['ip'] = requestInfo.peerip
        if requestInfo.uip != '':
            logInfo['uip'] = requestInfo.uip
        if len(requestInfo.sampleids) > 0:
            logInfo['sid'] = '[{}]'.format(','.join(requestInfo.sampleids))
        if requestInfo.access_key != '':
            logInfo['ak'] = requestInfo.access_key
        if requestInfo.signature != '':
            logInfo['sg'] = requestInfo.signature
        if requestInfo.debug:
            logInfo['debug'] = 1

    def afterRequest(self, request, context, response, logInfo):
        '''
        请求后置处理
        '''
        if response is None: # 请求发生异常
            logInfo['rt'] = -1
        else:
            if type(response) is ResponseInfo:
                logInfo['rt'] = response.code
            else:
                logInfo['rt'] = response.rtn.code

            # self.logger.debug('RESPONSE_MESSAGE: {}'.format(json.dumps(MessageToDict(response, True, True, True), ensure_ascii=False)))

    def authorize(self, ak, text, signature):
        '''
        认证授权
        @param ak: access key
        @param text: 验证用的原始文本
        @param signature: 请求包校验
        @return RtnCode
        '''
        if ak == '' or signature == '':
            self.logger.warning('invalid access key [{}] / signature [{}]'.format(ak, signature))
            return RtnCode.AUTHENTICATION_FAILED

        # 根据ak获取对应的sk
        if ak not in self.AK_SK_KEYS:
            self.logger.warning('invalid access key: {}'.format(ak))
            return RtnCode.INVALID_ACCESS_KEY
        else:
            sk = self.AK_SK_KEYS[ak]

        if signature != sign(sk, text):
            self.logger.warning('incorrect signature: {}'.format(signature))
            return RtnCode.INCORRECT_SIGNATURE

        return RtnCode.OK

    @GrpcService.grpc_interface
    def shutdown(self, request, context, logInfo):
        '''关闭服务器'''
        response = ResponseInfo()

        ip = ':'.join(context.peer().split(':')[1:-1])
        if ip not in ['127.0.0.1']:
            self.logger.warning('refuse any shutdown request not from localhost')
            response.code = RtnCode.FAIL
            return response

        # 认证
        response.code = self.authorize(request.access_key, 'shutdown:{}'.format(request.logid), request.signature)
        if response.code != RtnCode.OK:
            return response

        # 设置退出标志
        app.isexit.set()
        # 等待服务退出
        app.exited.wait()

        return response

    @GrpcService.grpc_interface
    def ping(self, request, context, logInfo):
        '''ping'''
        response = ResponseInfo()

        self.logger.debug('pong')

        return response

    @GrpcService.grpc_interface
    def query_clustering(self, request, context, logInfo):
        print(request.filename, request.queries)
        response = CommentClusteringResponse()
        queries = []
        for query in request.queries:
            queries.append(query)

        try:
            groups = app.parallel([(request.filename, queries)], ['cluster'])[0]
            print(groups)
            for group in groups:
                response.comment_clustering_response_content.append(str(group))
            response.rtn.code = RtnCode.OK
        except Exception:
            self.logger.error(traceback.format_exc())
            response.rtn.code = RtnCode.FAIL
        finally:
            return response

    @GrpcService.grpc_interface
    def get_top_similar_queries(self, request, context, logInfo):
        response = CommentAnalyzerResponse()
        try:
            groups = app.parallel([(request.query, request.threshold)], ['analyzer'])[0]
            for group in groups:
                response.comment_analyzer_response_content.append(str(group))
            response.rtn.code = RtnCode.OK
        except Exception:
            self.logger.error(traceback.format_exc())
            response.rtn.code = RtnCode.FAIL
        finally:
            return response
