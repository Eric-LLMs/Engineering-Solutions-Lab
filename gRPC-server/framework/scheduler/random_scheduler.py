import logging
import random
import threading
import time
import traceback
from typing import Any, Tuple

from .scheduler import Scheduler
from framework import FrameworkException, ErrCode, loadClass

class RandomSchedulerDetectThread(threading.Thread):
    def __init__(self, scheduler):
        '''
        @param scheduler: 调度器
        '''
        super(RandomSchedulerDetectThread, self).__init__(daemon=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.scheduler = scheduler

    def run(self):
        self.logger.info('detect thread of {} started'.format(self.scheduler))
        while True:
            try:
                server = self.scheduler.servers[self.scheduler.unavailable[0]]

                self.logger.debug('detect server {}'.format(server))
                if server.ping():
                    self.scheduler.setAvailable(server)
                    self.logger.debug('server {} detect alived'.format(server))
                else:
                    self.logger.warn('server {} detect failed'.format(server))
            except KeyboardInterrupt:
                break
            except:
                pass

            time.sleep(2)

        self.logger.info('detect thread of {} exited'.format(self.scheduler))

class RandomScheduler(Scheduler):
    '''
    随机调度器
    '''
    def __init__(self, name: str=None, **kwargs):
        super(self.__class__, self).__init__(name)

        self.servers = []   # 记录所有服务器

        self.available = [] # 记录可用服务器在servers中的idx
        self.unavailable = [] # 记录不可用服务器在servers中的idx

        clsname = kwargs.get('class', None)
        if clsname is None:
            self.logger.error('no remote server class specified')
            raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

        c = loadClass(clsname)
        if c is None:
            self.logger.error('failed to load remote server class "{}"'.format(clsname))
            raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)
        try:
            for one in kwargs.get('servers', []):
                server = c(**one)
                self.registerServer(server)
                if not server.ping():
                    self.setUnavailable(server)
                self.logger.info('registered {} -> {}'.format(server, self))
        except Exception as ex:
            self.logger.error('failed to load {} from config:servers'.format(self))
            raise

        # 启动探活线程
        self.detectThread = RandomSchedulerDetectThread(self)
        self.detectThread.start()

    def registerServer(self, server):
        '''
        注册服务器
        @param server: 服务器
        @return 服务器idx
        '''
        idx = len(self.servers)

        self.servers.append(server)
        self.available.append(idx)

        return idx

    def getOne(self):
        '''
        获取一个实例
        @return server/None
        '''
        if len(self.servers) == 0: return None

        # 优先从有效服务器中选择
        try:
            chosen = random.choice(self.available)
            return self.servers[chosen]
        except:
            # 失败，从所有服务器中选择
            return random.choice(self.servers)

    def setAvailable(self, server):
        '''
        设置服务器可用
        @param server: 服务器
        '''
        try:
            i = self.servers.index(server)
            if i not in self.available:
                self.available.append(i)
            if i in self.unavailable:
                self.unavailable.remove(i)
        except:
            pass

    def setUnavailable(self, server):
        '''
        设置服务器不可用
        @param server: 服务器
        '''
        try:
            i = self.servers.index(server)
            if i in self.available:
                self.available.remove(i)
            if i not in self.unavailable:
                self.unavailable.append(i)
        except:
            pass

    def invoke(self, funcname, *args, **kwargs):
        '''
        调用服务方法
        @param funcname: 函数名
        @return response
        '''
        stub = self.getOne()
        if stub is None:
            self.logger.warn('failed to get one in {}'.format(self))
            return None

        func = getattr(stub, funcname)
        if func is None:
            self.logger.warn('failed to invoke {} in server of {}'.format(funcname, self))
            return None

        # 调用服务函数
        response = func(*args, **kwargs)
        return response

    def invokeRpc(self, funcname, *args, **kwargs):
        '''
        调用服务rpc接口方法
        @param funcname: 函数名
        @return response
        '''
        stub = self.getOne()
        if stub is None:
            self.logger.warn('failed to get one in {}'.format(self))
            return None

        func = getattr(stub, funcname)
        if func is None:
            self.logger.warn('failed to invoke {} in server of {}'.format(funcname, self))
            return None

        try:
            # 调用服务函数
            response = func(*args, **kwargs)
            self.setAvailable(stub)
        except:
            self.setUnavailable(stub)
            self.logger.warn('failed to invoke {} from server {}: {}'.format(funcname, stub, traceback.format_exc()))

            return None
        else:
            return response