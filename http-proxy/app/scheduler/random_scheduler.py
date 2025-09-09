#!/usr/bin/env python3
#coding=utf-8

import logging
import random
import threading
import time

from .scheduler import Scheduler, RemoteServer, loadRemoteServer

class RandomSchedulerDetectThread(threading.Thread):
    def __init__(self, name, scheduler):
        '''
        @param scheduler: 调度器
        '''
        super(RandomSchedulerDetectThread, self).__init__(daemon=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.scheduler = scheduler

    def run(self):
        self.logger.info('detect thread of {} started'.format(self.name))
        while True:
            try:
                server = self.scheduler.servers[self.scheduler.unavailable[0]]

                self.logger.debug('detect server {}'.format(server))
                if server.ping():
                    self.scheduler.setAvailable(server)
                    self.logger.debug('server {} detect alived'.format(server))
            except KeyboardInterrupt:
                break
            except:
                pass

            time.sleep(2)
        self.logger.info('detect thread of {} exited'.format(self.name))

class RandomScheduler(Scheduler):
    '''随机调度'''
    def __init__(self, name: str, **kwargs):
        super(RandomScheduler, self).__init__(name, **kwargs)

        self.servers = []   # 记录所有服务器

        self.available = [] # 记录可用服务器在servers中的idx
        self.unavailable = [] # 记录不可用服务器在servers中的idx

        clsname = kwargs.get('impl', None)
        if clsname is None:
            self.logger.critical('no remote server class specified')
            raise Exception()

        c = loadRemoteServer(clsname)
        if c is None:
            self.logger.critical('failed to load remote server class: {}'.format(clsname))
            raise Exception()

        for one in kwargs.get('servers', []):
            server = c(**one)
            self.logger.info('register {}'.format(server))
            self.registerServer(server)

        # 启动探活线程
        self.detectThread = RandomSchedulerDetectThread(self.__class__.__name__, self)
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
        if len(self.available) > 0:
            return self.servers[random.choice(self.available)]
        else:
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
