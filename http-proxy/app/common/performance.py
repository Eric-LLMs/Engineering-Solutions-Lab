#!/usr/bin/env python3
# coding=utf-8

import time

class PerformanceTimer():
    '''timer for performance record'''

    def __init__(self):
        self.timer = {}

    def start(self, name='default'):
        '''
        start timer
        @param name: name of timer
        '''
        if name not in self.timer:
            self.timer[name] = {
                'timer': time.time(),
                'pass': 0
            }
        else:
            self.timer[name]['timer'] = time.time()

    def stop(self, name='default'):
        '''stop timer'''
        if name not in self.timer:
            raise Exception('timer {} not found'.format(name))

        now = time.time()

        self.timer[name]['pass'] += now - self.timer[name]['timer']

    def reset(self, name='default'):
        '''reset timer'''
        if name not in self.timer:
            raise Exception('timer {} not found'.format(name))

        self.timer[name]['pass'] = 0

    def restart(self, name='default'):
        '''restart timer'''
        self.reset(name)
        self.start(name)

    def read(self, name='default'):
        '''read timer, second'''
        if name not in self.timer:
            raise Exception('timer {} not found'.format(name))

        return self.timer[name]['pass']

    def read_millisecond(self, name='default'):
        '''read timer, millisecond'''
        return int(self.read(name) * 1000)

    def read_microsecond(self, name='default'):
        '''read timer, microsecond'''
        return int(self.read(name) * 1000 * 1000)

    def readString(self, name='default'):
        '''read timer, likes: 3m27s'''
        ts = self.read(name)
        return PerformanceTimer.renderTimerOutput(ts)

    def __enter__(self):
        '''支持with特性'''
        self.start()

    def __exit__(self, exc_ty, exc_val, tb):
        '''支持with特性'''
        self.stop()

    @staticmethod
    def renderTimerOutput(ts):
        '''
        render timer output to readable string
        @param ts: timestamp(seconds)
        @return readable string
        '''
        day, hour, minute, second = 0, 0, 0, 0
        output = ''

        day = ts // 60 // 60 // 24
        if day > 0:
            output = '{} 天 '.format(int(day))
            ts -= day * 60 * 60 * 24
        hour = ts // 60 // 60
        if hour > 0:
            output += '{} 小时 '.format(int(hour))
            ts -= hour * 60 * 60
        minute = ts // 60
        if minute > 0:
            output += '{} 分 '.format(int(minute))
            ts -= minute * 60
        second = ts
        if second > 0:
            output += '{} 秒'.format('{:.1f}'.format(second).rstrip('0').rstrip('.'))

        return output.rstrip()
