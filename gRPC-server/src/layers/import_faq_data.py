# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: import_faq_data.py
@Author:
@Time: 12月 14, 2020
"""

import os
import sys

from pathlib import Path

__dir__ = os.path.dirname(os.path.dirname(__file__))
sys.path.append(__dir__)

__dir__ = Path(__file__).resolve().parent
__base__ = __dir__.parent

sys.path.append(str(__base__.joinpath('interface')))
os.chdir(str(__dir__))

# add interface folder into PATH
sys.path.append(str(__base__))
sys.path.append(str(__base__.joinpath('src')))

from framework import loadYamlConfig
from src.layers.analyzer import *

# initialize logging
logging.getLogger().setLevel(logging.DEBUG)

# loading client.yml
try:
    config = loadYamlConfig('../conf/service.yml')
    logging.debug('loaded service config')
except Exception as ex:
    logging.critical('failed to load service config: {}'.format(ex))
    sys.exit(-1)

# 服务器端口号
port = config['interfaces']['grpc']['args']['listen_port']
# 开发环境
# client = CommentAnalyzerClient('127.0.0.1', port)

print(port)
