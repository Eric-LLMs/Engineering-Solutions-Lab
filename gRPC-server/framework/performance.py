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

    def read(self, name='default') -> int:
        '''read timer, second'''
        if name not in self.timer:
            raise Exception('timer {} not found'.format(name))

        return self.timer[name]['pass']

    def read_millisecond(self, name='default') -> int:
        '''read timer, millisecond'''
        return int(self.read(name) * 1000)

    def read_microsecond(self, name='default') -> int:
        '''read timer, microsecond'''
        return int(self.read(name) * 1000 * 1000)

    def readString(self, name='default') -> str:
        '''read timer, likes: 3m27s'''
        ts = self.read(name)
        return PerformanceTimer.renderTimerOutput(ts)

    @staticmethod
    def renderTimerOutput(ts) -> str:
        '''
        render timer output to readable string
        @param ts: timestamp(seconds)
        @return readable string
        '''
        day, hour, minute, second = 0, 0, 0, 0
        output = ''

        day = ts // 60 // 60 // 24
        if day > 0:
            output = '{} day{} '.format(int(day), 's' if day > 1 else '')
            ts -= day * 60 * 60 * 24
        hour = ts // 60 // 60
        if hour > 0:
            output += '{} hour{} '.format(int(hour), 's' if hour > 1 else '')
            ts -= hour * 60 * 60
        minute = ts // 60
        if minute > 0:
            output += '{} minute{} '.format(int(minute), 's' if minute > 1 else '')
            ts -= minute * 60
        second = ts
        if second > 0:
            output += '{} second{} '.format('{:.1f}'.format(second).rstrip('0').rstrip('.'), 's' if second >= 2 else '')

        return output.rstrip()
