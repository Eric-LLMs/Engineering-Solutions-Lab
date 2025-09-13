# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################

"""
@File: client_test.py
@Author:
@Time: 11月 12, 2020
"""

if __name__ == '__main__':
    import os
    import sys

    import logging

    import datetime

    from pathlib import Path

    __dir__ = Path(__file__).resolve().parent
    __base__ = __dir__.parent

    sys.path.append(str(__base__.joinpath('interface')))
    os.chdir(str(__dir__))

    # add interface folder into PATH
    sys.path.append(str(__base__))
    sys.path.append(str(__base__.joinpath('src')))

    from src.comment_analyzer_client import CommentAnalyzerClient
    from framework import loadYamlConfig

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
    port = 39375
    client = CommentAnalyzerClient('192.168.0.221', port)
    # ping
    try:
        client.ping('test')
        logging.debug('ping is ok')
    except Exception as ex:
        logging.error('failed to ping: {}'.format(ex))
        sys.exit(-1)

    # shutdown
    try:
        # client.shutdown('test')
        logging.debug('shutdown is ok')
    except Exception as ex:
        logging.error('failed to shutdown: {}'.format(ex))
        sys.exit(-1)

    # user input queries one by one
    sample_file = 'sample.txt'
    cnt = 0
    for line in open(sample_file):
        # line = line.strip('\r\n')
        line = '睡觉枕头和颈椎 配合'
        print(line)
        cnt += 1
        oldtime = datetime.datetime.now()
        try:
            response = client.get_top_similar_queries(line, 0.22)
            logging.debug(response.comment_analyzer_response_content)
            logging.debug('get_top_similar_queries is ok')
        except Exception as ex:
            logging.error('failed to get top similar query : {}'.format(ex))
            sys.exit(-1)
        newtime = datetime.datetime.now()
        print(u'总条数：%s, 相差：%s豪秒\n' % (cnt, (newtime - oldtime).total_seconds() * 1000))
