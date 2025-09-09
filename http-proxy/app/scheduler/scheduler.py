#!/usr/bin/env python3
# coding=utf-8
# 远程服务调度模块

from app.config import SchedulerConfig
import logging
import traceback
import uuid

from app import app
from app.common import loadModuleClass, AppRtnCode, AppException
from grpc import RpcError, StatusCode
from retrying import retry
from typing import Any, Union


class RemoteServer(object):
    '''远程服务器基类'''

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)

    def ping(self):
        '''ping，用于探活'''
        raise NotImplemented()

    def getLogId(self):
        '''
        生成日志id
        '''
        return 'logid-{}'.format(str(uuid.uuid1()))

    def __repr__(self):
        raise NotImplemented()


class Scheduler(object):
    '''调度器基类'''

    def __init__(self, name: str, **kwargs):
        '''
        @param clsname: 服务实现类名
        @param servers: 服务器信息
        '''
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)

    def registerServer(self, instance: RemoteServer):
        '''
        注册远程服务器
        @param instance: 服务器对象
        '''
        raise NotImplemented()

    def registerServer(self, row: int, instance: RemoteServer):
        '''
        注册远程服务器
        @param[in] row: 集群行号
        @param[in] instance: 服务器对象
        '''
        raise NotImplemented()

    def getOne(self) -> RemoteServer:
        '''
        随机获取一个服务器实例
        '''
        raise NotImplemented()

    def getOne(self, row: int) -> RemoteServer:
        '''
        随机获取一个服务器实例
        @param[in] row: 集群行号
        '''
        raise NotImplemented()

    def getServers(self) -> list:
        '''
        获取单集群节点所有服务器实例
        '''
        raise NotImplemented()

    def getServers(self, row) -> list:
        '''
        获取指定行集群所有服务器实例
        @param[in] row: 集群行号
        '''
        raise NotImplemented()

    def getRowsCount(self) -> int:
        '''
        获取指定集群行数
        @return 集群行数
        '''
        raise NotImplemented()

    def setUnavailable(self, instance: RemoteServer):
        '''
        设置服务器不可用
        '''
        raise NotImplemented()

    def setUnavailable(self, row: int, instance: RemoteServer):
        '''
        设置服务器不可用
        @param[in] row: 集群行号
        '''
        raise NotImplemented()

    def setAvailable(self, instance: RemoteServer):
        '''
        设置服务器可用
        '''
        raise NotImplemented()

    def setAvailable(self, row: int, instance: RemoteServer):
        '''
        设置服务器可用
        @param[in] row: 集群行号
        '''
        raise NotImplemented()

    def __repr__(self):
        return '{}:{}'.format(self.__class__.__name__, self.name)


def loadScheduler(name: str, config: SchedulerConfig) -> Union[Scheduler, None]:
    '''
    载入调度器实例
    @param name: 调度器名
    @param config: 调度器配置
    @return 调度器实例，如果载入失败，则返回None
    '''
    # 载入scheduler
    clsname = config.impl.split('.')
    c = loadModuleClass('.'.join(clsname[:-1]), clsname[-1], Scheduler)

    if c is None:
        logging.error('failed to load module class {}'.format(config['class']))
        return None

    try:
        instance = c(name, **config.args)
        return instance
    except Exception as ex:
        logging.critical('failed to load scheduler {}'.format(ex))
        return None


def loadRemoteServer(clsname):
    '''
    载入远程服务实例
    @param clsname: remote server类名
    @return 远程服务实例，如果载入失败，则返回None
    '''
    if clsname is None:
        return None

    # 载入remote server
    clsname = clsname.split('.')
    c = loadModuleClass('.'.join(clsname[:-1]), clsname[-1], RemoteServer)

    if c is None:
        logging.error(
            'failed to load module class {}'.format('.'.join(clsname)))
        return None
    else:
        return c


@retry(stop_max_attempt_number=2)
def requestScheduler(scheduler: Union[str, Scheduler], funcname: str, *args, **kwargs) -> Union[Any, None]:
    '''
    通过调度器请求服务函数
    @param scheduler: 服务调度器/调度器名
    @param funcname: 函数名
    @param args: args
    @param kwargs: kwargs
    @return 结果，如果请求失败，则返回None
    '''
    if isinstance(scheduler, str):
        scheduler = app.schedulers.get(scheduler, None)
    if not scheduler:
        app.logger.error('invalid scheduler == None')
        return None

    # 从调度器分配服务实例
    stub = scheduler.getOne()

    if stub is None:
        app.logger.warn(
            'cannot get any server from scheduler {}'.format(scheduler))
        return None

    response = None

    try:  # 请求服务的特定函数
        response = getattr(stub, funcname)(*args, **kwargs)
    except RpcError as ex:
        app.logger.error('exception during grpc')
        if ex.code() not in [StatusCode.DEADLINE_EXCEEDED]:
            # 服务不可用
            scheduler.setUnavailable(stub)

        if ex.code() == StatusCode.DEADLINE_EXCEEDED:
            raise AppException('invoke {} at {} timeout'.format(
                funcname, stub), rtncode=AppRtnCode.BACKEND_TIMEOUT)
        else:
            raise AppException('{} unavailable: {}'.format(
                stub, ex.code()), rtncode=AppRtnCode.BACKEND_UNAVAILABLE)
    except Exception as ex:
        raise AppException(traceback.format_exc(), rtncode=AppRtnCode.ERROR)
    else:
        return response


@retry(stop_max_attempt_number=2)
def requestScheduler2D(scheduler: str, funcname: str, row: int, *args, **kwargs) -> Union[Any, None]:
    '''
    通过调度器请求服务函数
    @param scheduler: 服务调度器/调度器名
    @param funcname: 函数名
    @param args: args
    @param kwargs: kwargs
    @return 结果，如果请求失败，则返回None
    '''
    if isinstance(scheduler, str):
        scheduler = app.schedulers.get(scheduler, None)
    if not scheduler:
        app.logger.error('invalid scheduler == None')
        return None

    # 从调度器分配服务实例
    stubs = scheduler.getServers(row)

    if len(stubs) <= 0:
        app.logger.warn(
            'cannot get any server from scheduler {}'.format(scheduler))
        return None

    response = None

    for col, stub in enumerate(stubs):
        try:  # 请求服务的特定函数
            response = getattr(stub, funcname)(*args, **kwargs)
        except RpcError as ex:
            app.logger.error('exception during grpc[{}][{}]'.format(row, col))
            if ex.code() not in [StatusCode.DEADLINE_EXCEEDED]:
                # 服务不可用
                scheduler.setUnavailable(row, stub)

            if ex.code() == StatusCode.DEADLINE_EXCEEDED:
                raise AppException('invoke {} at {}[{}][{}] timeout'.format(
                    funcname, stub, row, col), rtncode=AppRtnCode.BACKEND_TIMEOUT)
            else:
                raise AppException('{}[{}][{}] unavailable: {}'.format(
                    stub, row, col, ex.code()), rtncode=AppRtnCode.BACKEND_UNAVAILABLE)
        except Exception as ex:
            raise AppException(traceback.format_exc(),
                               rtncode=AppRtnCode.ERROR)
    else:
        return response
