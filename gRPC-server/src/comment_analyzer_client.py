# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: comment_analyzer_client.py
@Author:
@Time: 11月 13, 2020
"""

import os
import sys

import uuid
import grpc

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(__dir__, '../interfaces'))
sys.path.append(os.path.join(__dir__, '../framework'))

from interfaces.live_comments_analysis_pb2_grpc import CommentAnalyzerServiceStub
from interfaces.live_comments_analysis_pb2 import RequestInfo, CommentAnalyzerRequest, CommentClusteringRequest
from framework.security import sign


class CommentAnalyzerClient:
    '''ocr服务客户端封装'''
    ak = '1585300274-4800963'
    sk = 'b568HD4rPDbT3anbTrn2P4wT'

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.request_source = 'text'
        self.channel = grpc.insecure_channel('{}:{}'.format(ip, port),
            options=[
            ])
        self.stub = CommentAnalyzerServiceStub(self.channel)

    def getLogId(self):
        '''获取一个logid'''
        return 'logid-{}'.format(uuid.uuid1())

    def ping(self, source):
        logid = self.getLogId()
        self.stub.ping(RequestInfo(
            source=source,
            logid=logid,
            ), timeout=1)

    def shutdown(self, source):
        logid = self.getLogId()
        signature = sign(self.sk, 'shutdown:{}'.format(logid))
        self.stub.shutdown(RequestInfo(
            source=source,
            logid=logid,
            access_key=self.ak,
            signature=signature
        ), timeout=10)


    # def add_to_clustering_group(self, video_id, query):
    #     request = CommentAnalyzerRequest(
    #         video_id=video_id,
    #         query=query,
    #         info=RequestInfo(
    #             logid=self.getLogId(),
    #             source=self.request_source,
    #             debug=True,
    #         ),
    #     )
    #     response = self.stub.add_to_clustering_group(request, timeout=60)
    #
    #     return response

    def query_clustering(self, filename, queries:list):
        request = CommentClusteringRequest(
            filename=filename,
            queries=queries,
            info=RequestInfo(
                logid=self.getLogId(),
                source=self.request_source,
                debug=True,
            ),
        )
        response = self.stub.query_clustering(request, timeout=300)

        return response

    def get_top_similar_queries(self, query, threshold):
        request = CommentAnalyzerRequest(
            query=query,
            threshold=threshold,
            info=RequestInfo(
                logid=self.getLogId(),
                source=self.request_source,
                debug=True,
            ),
        )
        response = self.stub.get_top_similar_queries(request, timeout=60)

        return response