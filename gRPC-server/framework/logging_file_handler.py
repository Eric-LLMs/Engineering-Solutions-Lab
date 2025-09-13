#!/usr/bin/env python3
#coding=utf-8

from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler

class DebugTimedRotatingFileHandler(TimedRotatingFileHandler):
    '''file handler only show debug log'''
    def emit(self, record):
        if not record.levelno == self.level:
            return

        TimedRotatingFileHandler.emit(self, record)

class DebugRotatingFileHandler(RotatingFileHandler):
    '''file handler only show debug log'''
    def emit(self, record):
        if not record.levelno == self.level:
            return

        RotatingFileHandler.emit(self, record)
