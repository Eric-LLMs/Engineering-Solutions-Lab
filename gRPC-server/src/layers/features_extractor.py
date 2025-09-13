# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: features_processor.py
@Author:
@Time: 11月 13, 2020
"""

import os
import sys

import redis
import numpy as np
import logging
from rediscluster import StrictRedisCluster

import jieba
import jieba.posseg
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics.pairwise import cosine_similarity

__dir__ = os.path.dirname(os.path.dirname(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.dirname(__dir__))

from src.config import *
from src.layers.albert_processor import *
from src.layers.lgb_processor import *

class FeatureExtractor:
     def __init__(self, config):
         self.config = config
         self.albert_processor = AlbertProcessor(self.config)
         self.lightGBM_processor = LGBProcessor(self.config)

         # self.redis_conn = redis.StrictRedis(host=self.config.redis_ip, port=self.config.redis_port, password=self.config.redis_pwd, decode_responses=True)
         # 集群
         redis_basis_conn = [{'host': '192.168.1.122', 'port': 6385},
                             {'host': '192.168.1.123', 'port': 6385},
                             {'host': '192.168.1.71', 'port': 6385}]
         self.redis_conn = StrictRedisCluster(startup_nodes=redis_basis_conn, password='admin', decode_responses=True)
         # local
         # self.redis_conn = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)

         # a 形容词 an 名形容词 n 名词 nz 专有名词 v 动词 vn 动名词
         self.filter_pos = ['a', 'an', 'n', 'nz', 'v', 'vn', '观察对象', '解剖结构', '动作', '骨科疾病', '治疗措施', '基本所见', '治疗措施',
                      '药品名', '评价结果', '手术名称', '一般检查', '病因事件', '治疗措施', 'omaha', '影像检查', '非骨科疾病', '国家医保', '国家临床']

     def similarity(self, video_id, querya, queryb):
         video_keys = gen_redis_keys(video_id)
         sentence_vec1 = None
         sentence_vec2 = None
         if self.redis_conn.hexists(video_keys.key_redis_queries_vec, querya):
             str_v1_list = self.redis_conn.hget(video_keys.key_redis_queries_vec, querya).replace('\n', '').\
                 replace('[', '').replace(']', '').split(' ')
             dlist = []
             for v in str_v1_list:
                 if v != '':
                     dlist.append(float(v))
             darr = np.array(dlist).astype(np.float)
             sentence_vec1 = darr
         else:
             token_ids1, segment_ids1 = self.albert_processor.tokenizer.encode(querya)
             sentence_vec1 = self.albert_processor.albert.predict([np.array([token_ids1]), np.array([segment_ids1])])[0]
             self.redis_conn.hset(video_keys.key_redis_queries_vec, querya, sentence_vec1)

         if self.redis_conn.hexists(video_keys.key_redis_queries_vec, queryb):
             str_v2_list = self.redis_conn.hget(video_keys.key_redis_queries_vec, queryb).replace('\n', '')\
                 .replace('[', '').replace(']','').split(' ')
             dlist = []
             for v in str_v2_list:
                 if v != '':
                     dlist.append(float(v))
             darr = np.array(dlist).astype(np.float)
             sentence_vec2 = darr
         else:
             token_ids2, segment_ids2 = self.albert_processor.tokenizer.encode(queryb)
             sentence_vec2 = self.albert_processor.albert.predict([np.array([token_ids2]), np.array([segment_ids2])])[0]
             self.redis_conn.hset(video_keys.key_redis_queries_vec, queryb, sentence_vec2)

         score = float(self.get_similarity(sentence_vec1, sentence_vec2))
         return score

     def get_similarity(self, vec1, vec2, mode='cos'):
         if mode == 'eu':
             return euclidean_distances([vec1, vec2])[0][1]
         if mode == 'cos':
             return cosine_similarity([vec1, vec2])[0][1]

     def LCSeq(self,video_id, str_a, str_b):
         video_keys = gen_redis_keys(video_id)
         # 最长公共子序列
         len1 = len(str_a)
         len2 = len(str_b)

         if len1 == 0 or len2 == 0:
             return 0, 0, 0, 0

         a_b = str_a + str_b
         b_a = str_b + str_a

         lcs_score = 0

         if self.redis_conn.hexists(video_keys.key_redis_lcsq, a_b):
             lcs_score = self.redis_conn.hget(video_keys.key_redis_lcsq, a_b)

         if self.redis_conn.hexists(video_keys.key_redis_lcsq, b_a):
             lcs_score = self.redis_conn.hget(video_keys.key_redis_lcsq, b_a)

         if self.redis_conn.hexists(video_keys.key_redis_lcsq, a_b) == False and self.redis_conn.hexists(video_keys.key_redis_lcsq, b_a) == False:
             res = [[0 for i in range(len1 + 1)] for j in range(len2 + 1)]
             for i in range(1, len2 + 1):
                 for j in range(1, len1 + 1):
                     if str_b[i - 1] == str_a[j - 1]:
                         res[i][j] = res[i - 1][j - 1] + 1
                     else:
                         res[i][j] = max(res[i - 1][j], res[i][j - 1])

             self.redis_conn.hset(video_keys.key_redis_lcsq, a_b, res[-1][-1])
             self.redis_conn.hset(video_keys.key_redis_lcsq, b_a, res[-1][-1])
             lcs_score = res[-1][-1]

         # 最长子序列 ｜句子a长度-句子b长度｜  最长子序列最小占比 最长子序列最大占比
         return lcs_score, abs(len1 - len2), min(float(lcs_score) / len1, float(lcs_score) / len2), max(
             float(lcs_score) / len1, float(lcs_score) / len2)

     def LCStr(self,video_id, a, b):
         video_keys = gen_redis_keys(video_id)
         # 最长公共字串
         len1 = len(a)
         len2 = len(b)

         res = [[0 for i in range(len1 + 1)] for j in range(len2 + 1)]
         a_b = a + b
         b_a = b + a
         lcstr_score = 0

         if self.redis_conn.hexists(video_keys.key_redis_lcstr, a_b):
             lcstr_score = self.redis_conn.hget(video_keys.key_redis_lcstr, a_b)

         if self.redis_conn.hexists(video_keys.key_redis_lcstr, b_a):
             lcstr_score = self.redis_conn.hget(video_keys.key_redis_lcstr, b_a)

         if self.redis_conn.hexists(video_keys.key_redis_lcstr, a_b) == False and self.redis_conn.hexists(video_keys.key_redis_lcstr, b_a) == False:
             for i in range(1, len2 + 1):
                 for j in range(1, len1 + 1):
                     if b[i - 1] == a[j - 1]:
                         res[i][j] = res[i - 1][j - 1] + 1
                         lcstr_score = max(lcstr_score, res[i][j])

             self.redis_conn.hset(video_keys.key_redis_lcstr, a_b, lcstr_score)
             self.redis_conn.hset(video_keys.key_redis_lcstr, b_a, lcstr_score)

         if len1 == 0 or len2 == 0:
             return lcstr_score, 0, 0
         else:
             # 最长子串 最长子串最小占比 最长子串最大占比
             return lcstr_score, min(float(lcstr_score) / len1, float(lcstr_score) / len2), max(
                 float(lcstr_score) / len1, float(lcstr_score) / len2)

     def get_groups(self, video_id, dic, key_query):
         video_keys = gen_redis_keys(video_id)
         if key_query in dic:
             self.redis_conn.sadd(video_keys.key_redis_res_temp_query_groups, key_query)
             for sim_key in dic[key_query]:
                 # 跳过自身，到自身的map
                 if sim_key == key_query:
                     continue
                 self.get_groups(video_id, dic, sim_key)

     def merge_list(self, queries):
         lenth = len(queries)
         for i in range(1, lenth):
             for j in range(i):
                 if queries[i] == {0} or queries[j] == {0}:
                     continue
                 x = queries[i].union(queries[j])
                 y = len(queries[i]) + len(queries[j])
                 if len(x) < y:
                     queries[i] = x
                     queries[j] = {0}
         return [i for i in queries if i != {0}]

     def get_features(self,video_id, a, b):
         q_a = self.filter_words_pos(video_id, a)
         q_b = self.filter_words_pos(video_id, b)
         # 最长子序列 ｜句子a长度-句子b长度｜  最长子序列最小占比 最长子序列最大占比
         lcs_ab, abs_ab, min_rate, max_rate = self.LCSeq(video_id, q_a, q_b)
         # 最长子串  最长子串最小占比 最长子串最大占比
         lcsring_ab, min_lcstring_rate, max_lcstring_rate = self.LCStr(video_id, a, b)
         # 文本相似度
         sim = (self.similarity(video_id, a, b) * 100 - 98) / 10
         info = q_a, q_b, a, b
         feautres = sim, lcs_ab, abs_ab, min_rate, max_rate, lcsring_ab, min_lcstring_rate, max_lcstring_rate
         return feautres, info

     def filter_words_pos(self, video_id, text):
         video_keys = gen_redis_keys(video_id)
         if self.redis_conn.hexists(video_keys.key_redis_filtering_words, text):
             return self.redis_conn.hget(video_keys.key_redis_filtering_words, text)
         segs = []
         pos = jieba.posseg.cut(text)
         for x in pos:
             if x.flag in self.filter_pos:
                 segs.append(x.word)
         res = ''.join(segs)
         self.redis_conn.hset(video_keys.key_redis_filtering_words, text, res)
         return res