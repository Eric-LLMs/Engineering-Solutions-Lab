#!/usr/bin/env python3
#coding=utf-8

import os
import sys

from pathlib import Path

__dir__ = Path(__file__).resolve().parent
__base__ = __dir__.parent.parent

sys.path.append(str(__base__))
sys.path.append(str(__base__.joinpath('interfaces')))
sys.path.append(str(__base__.joinpath('src')))

def loadClientConfig():
    '''载入客户端配置'''
    from framework import loadYamlConfig

    config = loadYamlConfig(os.path.join(__dir__, '../../conf/service.yml'))

    return config

def initializeClient(ip, port):
    from comment_analyzer_client import CommentAnalyzerClient

    client = CommentAnalyzerClient(ip, port)

    return client
