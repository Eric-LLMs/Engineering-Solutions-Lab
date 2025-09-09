import grpc
import json
import os
import sys

from app.scheduler import RemoteServer
from google.protobuf.json_format import Parse
from typing import Tuple

__dir__ = os.path.dirname(__file__)
sys.path.append(os.path.join(__dir__, '../interfaces/ct'))

from app.views import AppRequest
from comment_service_pb2 import RequestInfo, NormalRequest, NormalResponse
from comment_service_pb2_grpc import CtServiceStub

class CtService(RemoteServer):
    '''评论模型服务'''
    def __init__(self, ip, port, timeout):
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.channel = grpc.insecure_channel('{}:{}'.format(ip, port))
        self.stub = CtServiceStub(self.channel)

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

    def predict(self, sentence: str, common: AppRequest, timeout=1) -> Tuple[NormalResponse, NormalRequest]:
        '''
        predict接口
        @param sentence: 预测的句子
        @param common: 通用请求参数
        @param timeout: 超时时间
        @return predict结果
        '''
        request = NormalRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            sentence=sentence,
        )

        response = self.stub.predict(request, timeout=timeout)

        return response, request
