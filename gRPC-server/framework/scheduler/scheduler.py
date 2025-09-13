# 远程服务调度器

import logging
import traceback

from framework import ErrCode, FrameworkException
from grpc import RpcError, StatusCode
from retrying import retry
from typing import Any, Union

class RemoteServer():
    '''远程服务基类'''
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)

    def ping(self):
        '''ping，用于探活'''
        raise NotImplemented()

    def __repr__(self):
        raise NotImplementedError()

class Scheduler():
    '''调度器基类'''
    def __init__(self, name: str=None, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name

    def registerServer(self, instance):
        '''
        注册服务实例
        '''
        raise NotImplementedError()

    def getOne(self):
        '''
        获取一个服务实例
        '''
        raise NotImplementedError()

    def setUnavailable(self, instance):
        '''
        设置服务器不可用
        '''
        raise NotImplemented()

    def setAvailable(self, instance):
        '''
        设置服务器可用
        '''
        raise NotImplemented()

    def __repr__(self):
        if self.name is None:
            return self.__class__.__name__
        else:
            return '{}:{}'.format(self.__class__.__name__, self.name)

@retry(stop_max_attempt_number=2)
def requestScheduler(scheduler: Scheduler, funcname: str, *args, **kwargs) -> Union[Any, None]:
    '''
    通过调度器请求服务函数
    @param scheduler: 服务调度器/调度器名
    @param funcname: 函数名
    @param args: args
    @param kwargs: kwargs
    @return 结果，如果请求失败，则返回None
    '''
    # 从调度器分配服务实例
    stub = scheduler.getOne()

    if stub is None:
        logging.warn('cannot get any server from scheduler {}'.format(scheduler))
        return None

    response = None

    try: # 请求服务的特定函数
        response = getattr(stub, funcname)(*args, **kwargs)
    except RpcError as ex:
        logging.error('exception during grpc')
        if ex.code() not in [ StatusCode.DEADLINE_EXCEEDED ]:
            # 服务不可用
            scheduler.setUnavailable(stub)

        if ex.code() == StatusCode.DEADLINE_EXCEEDED:
            raise FrameworkException('invoke {} at {} timeout'.format(funcname, stub), errcode=ErrCode.BACKEND_TIMEOUT)
        elif ex.code() == StatusCode.UNIMPLEMENTED:
            raise FrameworkException('invoke {} at {} unimplemented'.format(funcname, stub), errcode=ErrCode.BACKEND_METHOD_NOT_IMPLEMENTED)
        else:
            raise FrameworkException('{} unavailable'.format(stub), errcode=ErrCode.BACKEND_UNAVAILABLE)
    except Exception as ex:
        raise FrameworkException(traceback.format_exc(), errcode=ErrCode.FAILED)
    else:
        return response
