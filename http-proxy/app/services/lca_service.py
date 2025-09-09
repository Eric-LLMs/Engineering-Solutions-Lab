# -*- coding: utf-8 -*-
"""
@File: lca_service.py
@Author:
@Time: 12月 16, 2020
"""

import grpc
import json
import os
import sys

from app.scheduler import RemoteServer
from google.protobuf.json_format import Parse
from typing import Tuple

__dir__ = os.path.dirname(__file__)
sys.path.append(os.path.join(__dir__, '../interfaces/lca'))

from app.views import AppRequest
from live_comments_analysis_pb2 import RequestInfo, CommentAnalyzerResponse, CommentAnalyzerRequest,CommentClusteringRequest,CommentClusteringResponse
from live_comments_analysis_pb2_grpc import CommentAnalyzerServiceStub

class LcaService(RemoteServer):
    '''评论模型服务'''
    def __init__(self, ip, port, timeout):
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.channel = grpc.insecure_channel('{}:{}'.format(ip, port))
        self.stub = CommentAnalyzerServiceStub(self.channel)

    def __repr__(self):
        return '{}:{}'.format(self.ip, self.port)

    def ping(self) -> bool:
        '''
        ping探活
        '''
        try:
            requestJson = {
                'source': 'http-proxy',
                'logid': self.getLogId(),
            }
            request = Parse(json.dumps(requestJson, ensure_ascii=False), RequestInfo())

            self.stub.ping(request, timeout=self.timeout)

            return True
        except:
            return False

    def lcasearch(self, common: AppRequest, knowledge_base: str, query: str, threshold: float, timeout=60) -> Tuple[CommentAnalyzerResponse, CommentAnalyzerRequest]:
        '''
        lcasearch接口
        @param query: 知识库名称
        @param query: 要查询的query
        @param thredshold: 查询的相似阈值
        @param common: 通用请求参数
        @param timeout: 超时时间
        @return 大于阈值的语义近似文本
        '''
        request = CommentAnalyzerRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            knowledge_base=knowledge_base,
            query=query,
            threshold=threshold,
        )

        response = self.stub.get_top_similar_queries(request, timeout=timeout)

        return response, request

    def cluster(self, common: AppRequest, filename: str, queries: list, timeout=60) -> Tuple[CommentClusteringResponse, CommentClusteringRequest]:
        '''
        cluster接口
        @param filename: 上传文件名称
        @param queries: 聚类的query列表
        @param common: 通用请求参数
        @param timeout: 超时时间
        @return 聚类结果
        '''
        request = CommentClusteringRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            filename=filename,
            queries=queries,
        )

        response = self.stub.query_clustering(request, timeout=timeout)

        return response, request

    # def cluster_queries(self, common: AppRequest, queries: list, filename: str, knowledge_base: str, timeout=60) -> Tuple[CommentClusteringResponse, CommentClusteringRequest]:
    #     '''
    #     cluster_queries接口
    #     @param common: 通用请求参数
    #     @param queries: 聚类的query列表
    #     @param filename: 提交的guid
    #     @param timeout: 超时时间
    #     @return 聚类结果
    #     '''
    #     request = CommentClusteringRequest(
    #         info=RequestInfo(
    #             source='http-proxy',
    #             logid=common.logid or self.getLogId(),
    #             debug=common.debug,
    #         ),
    #         filename=filename,
    #         queries=queries,
    #     )
    #
    #     response = self.stub.query_clustering(request, timeout=timeout)
    #
    #     return response, request