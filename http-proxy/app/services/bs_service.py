
from app.views import AppRequest
import grpc
import json
import os
import sys

from app.scheduler import RemoteServer
from google.protobuf.json_format import Parse
from typing import Tuple

__dir__ = os.path.dirname(__file__)
sys.path.append(os.path.join(__dir__, '../interfaces/bs'))

from bs_build_grpc_pb2 import BuildRequest, ReloadRequest, RemoveRequest
from bs_build_grpc_pb2_grpc import BuildGrpcStub
from bs_interface_common_pb2 import RequestInfo, ResponseInfo

class BsService(RemoteServer):
    '''bs建库服务'''

    def __init__(self, ip, port, timeout, **kwargs):
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.channel = grpc.insecure_channel('{}:{}'.format(ip, port))
        self.stub = BuildGrpcStub(self.channel)

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
            request = Parse(json.dumps(
                requestJson, ensure_ascii=False), RequestInfo())

            self.stub.ping(request, timeout=self.timeout)

            return True
        except:
            return False

    def build(self, common: AppRequest, layer: int, commands: int, typeid: int, docid: int, data: str, timeout=10) -> Tuple[BuildRequest, ResponseInfo]:
        '''
        build接口
        @param[in] common: 通用请求参数
        @param[in] layer: 集群层号
        @param[in] typeid: 文档类型id
        @param[in] docid: 文档数字id
        @param[in] data: 文档内容json串
        @param[in] commands: 命令类型:1-仅搜索建库 2-仅摘要 3-搜索摘要
        @param[in] timeout: 超时时间
        @return build结果
        '''

        request = BuildRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            type=typeid,
            id=docid,
            data=data.encode(encoding='utf-8'),
            layer=layer,
            commands=commands
        )

        response = self.stub.build(request, timeout=timeout)

        return response, request

    def clean(self, common: AppRequest, layer: int, commands: int, typeid: int, timeout=10) -> Tuple[ReloadRequest, ResponseInfo]:
        '''
        clean
        @param[in] common: 通用请求参数
        @param[in] layer: 集群层号
        @param[in] typeid: 文档类型id
        @param[in] commands: 命令类型:1-仅搜索建库 2-仅摘要 3-搜索摘要
        @param[in] timeout: 超时时间
        @return clean结果
        '''

        request = ReloadRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            type=typeid,
            layer=layer,
            commands=commands
        )

        response = self.stub.clean(request, timeout=timeout)

        return response, request

    def remove(self, common: AppRequest, layer: int, commands: int, typeid: int, docid: int, timeout=10) -> Tuple[RemoveRequest, ResponseInfo]:
        '''
        remove
        @param[in] common: 通用请求参数
        @param[in] layer: 集群层号
        @param[in] typeid: 文档类型id
        @param[in] docid: 文档数字id
        @param[in] commands: 命令类型:1-仅搜索建库 2-仅摘要 3-搜索摘要
        @param[in] timeout: 超时时间
        @return remove结果
        '''

        request = RemoveRequest(
            info=RequestInfo(
                source='http-proxy',
                logid=common.logid or self.getLogId(),
                debug=common.debug,
            ),
            type=typeid,
            layer=layer,
            commands=commands,
            docid=docid
        )

        response = self.stub.remove(request, timeout=timeout)

        return response, request
