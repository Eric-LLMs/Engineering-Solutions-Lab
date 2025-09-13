# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: config.py
@Author:
@Time: 11月 13, 2020
"""

import os
import sys

import collections

__dir__ = os.path.dirname(os.path.dirname(__file__))
sys.path.append(__dir__)

config = collections.namedtuple(
  "Params",
  [
    "root",
    "albert_config_path",
    "albert_checkpoint_path",
    "albert_dict_path",
    "lgb_path",
    "threshold",
    "redis_expiration_time",
    "redis_ip",
    "redis_port",
    "redis_pwd"
  ])


video_keys = collections.namedtuple(
  "Params",
  [
    'key_redis_queries_vec',
    'key_redis_vector_similarity',
    'key_redis_lcsq',
    'key_redis_lcstr',
    'key_redis_filtering_words',
    'key_redis_queries_cnt',
    'key_redis_sentence_similarity',
    'key_redis_clustering_groups',
    'key_redis_res_temp_query_groups',
    'key_redis_queries_list',
    'key_redis_question_answer_list',
  ])


def gen_redis_keys(video_id): # acme:algorithm:服务名:功能:xxx
  return video_keys(
    key_redis_queries_vec="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_queries_vec"),  # 保存query embedding
    key_redis_vector_similarity="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_vector_similarity"),  # 保存cos相似度计算结果
    key_redis_lcsq="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_lcsq"),  # 保存最长公共子序列值
    key_redis_lcstr="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_lcstr"),  # 保存最长公共字串
    key_redis_filtering_words="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_filtering_words"),  # 保存句子有效信息
    key_redis_queries_cnt="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_queries_cnt"),  # 聊天中query总数
    key_redis_sentence_similarity="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_sentence_similarity"),  # 保存句子的比较结果
    key_redis_clustering_groups="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_clustering_groups"),  # 聚类结果
    key_redis_res_temp_query_groups="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_res_temp_query_groups"),  # 临时组对
    key_redis_queries_list="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_queries_list"),  # 所有query 列表
    key_redis_question_answer_list="acme:algorithm:CommentAnalyzerService:%s_%s" % (video_id, "key_redis_question_answer_list"),  # 所有问答对列表
  )
