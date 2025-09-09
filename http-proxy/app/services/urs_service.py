import grpc
import json
import os
import sys

from app.scheduler import RemoteServer
from google.protobuf.json_format import Parse
from typing import Tuple

__dir__ = os.path.dirname(__file__)
sys.path.append(os.path.join(__dir__, '../interfaces/urs'))

from app.views import AppRequest
from urs_service_pb2 import RequestInfo, CommonRequest, CommonResponse, StringRequest
from urs_service_pb2_grpc import UrsServiceStub

class UrsService(RemoteServer):
    '''urs 服务'''
    def __init__(self, ip, port, timeout):
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.channel = grpc.insecure_channel('{}:{}'.format(ip, port))
        self.stub = UrsServiceStub(self.channel)

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

    def ocr(self, data: bytes, params: str, common: AppRequest, timeout=1) -> Tuple[CommonResponse, CommonRequest]:
        '''
        ocr接口
        @param data: 图片数据
        @param params: 参数
        @param common: 通用请求参数
        @param timeout: 超时时间
        @return ocr结果
        '''
        request = CommonRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            data=data,
            params=params,
        )

        response = self.stub.ocr(request, timeout=timeout)

        return response, request

    def mit(self, data: bytes, common: AppRequest, timeout=1) -> Tuple[CommonResponse, CommonRequest]:
        '''
        mit接口
        @param data: 图片数据
        @param common: 通用请求参数
        @param timeout: 超时时间
        @return ocr结果
        '''
        request = CommonRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            data=data,
        )

        response = self.stub.mit(request, timeout=timeout)

        return response, request

    def distiller(self, data: str, content_type: str, common: AppRequest, timeout=1) -> Tuple[CommonResponse, CommonRequest]:
        '''
        distiller接口
        @param data: 字符串
        @param content_type: distiller内容类型
        @param common: 通用请求参数
        @param timeout: 超时时间
        @return distiller结果
        '''
        request = StringRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
                appid=common.appid,
            ),
            data=data,
            params=json.dumps({
                'content_type': content_type
            }, ensure_ascii=False),
        )

        response = self.stub.distiller(request, timeout=timeout)

        return response, request
