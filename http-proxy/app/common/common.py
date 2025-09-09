#!/usr/bin/env python3
#coding=utf-8

import importlib
import logging, logging.config

from enum import Enum

class AppRtnCode(int, Enum):
    '''返回码定义'''
    OK = 0
    ERROR = 1   # 发生错误/异常

    VALIDATION_ERROR = 422  # 请求参数验证失败

    BACKEND_UNAVAILABLE = 11001 # 后端不可用
    BACKEND_TIMEOUT = 11002 # 后端超时

class AppException(Exception):
    '''APP内通用异常'''
    def __init__(self, msg='', rtncode=AppRtnCode.ERROR, *args, **kwargs):
        super(self.__class__, self).__init__(msg, *args, **kwargs)
        self.rtncode = rtncode

def loadModuleClass(modulename, classname, basecls=None):
    '''
    载入模块中的类
    @param modulename: 模块名
    @param classname: 类名
    @param basecls: 基类，如果未None，则不进行基类检查
    @return 类对象，如果不存在，返回None
    '''
    try:
        m = importlib.import_module(modulename)
        c = getattr(m, classname)
    except Exception as ex:
        import traceback

        logging.error(str(traceback.format_exc()))
        logging.error('failed to load module class [{}.{}]'.format(modulename, classname))
        return None

    if basecls is not None and not isinstance(c, basecls.__class__):
        # 基类不对
        logging.critical('class [{}] not inherited from [{}]'.format(classname, basecls.__class__.__name__))
        return None

    return c
