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

import re
import xlrd
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

albert_config_path = os.path.join('..', config['layers']['analyzer']['args']['albert_config_path'])
albert_checkpoint_path = os.path.join('..', config['layers']['analyzer']['args']['albert_checkpoint_path'])
albert_dict_path = os.path.join('..', config['layers']['analyzer']['args']['albert_dict_path'])
lgb_path = os.path.join('..', config['layers']['analyzer']['args']['lgb_path'])
threshold = config['layers']['analyzer']['args']['threshold']
redis_expiration_time = config['layers']['analyzer']['args']['redis_expiration_time']
# redis_ip: 192.168.1.56
# redis_port: 7001
# redis_pwd: fq9YesajeqxcLxs
redis_ip = config['layers']['analyzer']['args']['redis_ip']
redis_port = config['layers']['analyzer']['args']['redis_port']
redis_pwd = config['layers']['analyzer']['args']['redis_pwd']

analyzer = CommentAnalyzer(albert_config_path, albert_checkpoint_path, albert_dict_path, lgb_path,
                 threshold, redis_expiration_time, redis_ip, redis_port, redis_pwd)


qa_pairs = { }


def read_excel():
    faq_data = os.path.join(__dir__, 'cases/acme.xlsx')
    workbook = xlrd.open_workbook(faq_data)
    worksheet = workbook.sheet_by_name('知识库')
    # # sheet的名称，行数，列数
    # print (worksheet.name,worksheet.nrows,worksheet.ncols)
    rows_cnt = worksheet.nrows  # 总行数
    for i in range(rows_cnt):
        if i == 0:
            continue
        rowdate = worksheet.row_values(i)  # i行的list
        question = str(rowdate[0]).replace('\r', '').replace('\n', '')
        answer = str(rowdate[1]).replace('\r', '').replace('\n', '')
        qa_pairs[question] = answer

import datetime
if __name__=="__main__":
    read_excel()
    analyzer.init_faq_queries_fetures(qa_pairs)
    oldtime = datetime.datetime.now()
    res = analyzer.get_top_similar_queries(query='儿童缺血性股骨头坏死，保守治疗修复', threshold=0.32)

    for item in res:
       print(item)
    newtime = datetime.datetime.now()
    print(u'相差：%s豪秒\n' % ((newtime - oldtime).total_seconds() * 1000))