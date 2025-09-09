#!/usr/bin/env python3
# coding=utf-8

import logging
import random
import threading
import time

from .scheduler import Scheduler, RemoteServer, loadRemoteServer


class RandomScheduler2DDetectThread(threading.Thread):
    def __init__(self, name, scheduler):
        '''
        @param scheduler: 调度器
        '''
        super(RandomScheduler2DDetectThread, self).__init__(daemon=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.scheduler = scheduler

    def run(self):
        self.logger.info('detect thread of {} started'.format(self.name))
        while True:
            try:
                server = self.scheduler.servers[self.scheduler.unavailable[0]
                                                ][self.scheduler.unavailable[0][0]]

                self.logger.debug('detect server {}'.format(server))
                if server.ping():
                    self.scheduler.setAvailable(
                        self.scheduler.unavailable[0], server)
                    self.logger.debug('server {} detect alived'.format(server))
            except KeyboardInterrupt:
                break
            except:
                pass

            time.sleep(2)
        self.logger.info('detect thread of {} exited'.format(self.name))


class RandomScheduler2D(Scheduler):
    '''随机调度'''

    def __init__(self, name: str, **kwargs):
        super(RandomScheduler2D, self).__init__(name, **kwargs)

        self.servers = []   # 记录所有服务器

        self.available = []  # 记录可用服务器在servers中的idx
        self.unavailable = []  # 记录不可用服务器在servers中的idx

        clsname = kwargs.get('impl', None)
        if clsname is None:
            self.logger.critical('no remote server class specified')
            raise Exception()

        c = loadRemoteServer(clsname)
        if c is None:
            self.logger.critical(
                'failed to load remote server class: {}'.format(clsname))
            raise Exception()

        for one in kwargs.get('servers', []):
            server = c(**one)
            self.logger.info(
                'register servers {} (layer {})'.format(server, one['layer']))
            self.registerServer(one['layer'], server)

        # 启动探活线程
        self.detectThread = RandomScheduler2DDetectThread(
            self.__class__.__name__, self)
        self.detectThread.start()

    def registerServer(self, row, server):
        '''
        注册服务器
        @param row: 集群行号
        @param server: 服务器
        @return 服务器列idx
        '''
        idx = 0
        if len(self.servers) != row:
            idx = len(self.servers[row])
            self.servers[row].append(server)
            self.available[row].append(idx)
        else:
            col_servers = []
            col_servers.append(server)
            col_availables = []
            col_availables.append(idx)
            self.servers.append(col_servers)
            self.available.append(col_availables)

        return idx

    def getOne(self, row):
        '''
        获取一个实例
        @param row: 集群行号
        @return server/None
        '''
        if len(self.servers[row]) == 0:
            return None
        if len(self.available[row]) > 0:
            return self.servers[row][random.choice(self.available[row])]
        else:
            return random.choice(self.servers[row])

    def getServers(self, row) -> list:
        '''
        获取指定行集群所有服务器实例
        @param[in] row: 集群行号
        '''
        return self.servers[row]

    def getRowsCount(self) -> int:
        '''
        获取指定集群行数
        @return 集群行数
        '''
        return len(self.servers)

    def setAvailable(self, row, server):
        '''
        设置服务器可用
        @param row: 集群行号
        @param server: 服务器
        '''
        try:
            i = self.servers[row].index(server)
            if i not in self.available[row]:
                self.available[row].append(i)
            if i in self.unavailable[row]:
                self.unavailable[row].remove(i)
        except:
            pass

    def setUnavailable(self, row, server):
        '''
        设置服务器不可用
        @param row: 集群行号
        @param server: 服务器
        '''
        try:
            i = self.servers[row].index(server)
            if i in self.available[row]:
                self.available[row].remove(i)
            if i not in self.unavailable[row]:
                self.unavailable[row].append(i)
        except:
            pass
