import os
import sys
import json
import numpy
import logging
import datetime

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(__dir__, '../interfaces'))
sys.path.append(os.path.abspath(os.path.join(__dir__, '../')))

# from framework.layer import BaseLayer
# from src.config import *
# from src.layers.features_extractor import *
from layers.features_extractor import *
from layers.inverted_index import Inverted_Index

class CommentAnalyzer():
    def __init__(self, albert_config_path, albert_checkpoint_path, albert_dict_path, lgb_path,
                 threshold, redis_expiration_time, redis_ip, redis_port, redis_pwd, **kwargs):
        self.config = config(
            root=__dir__,
            albert_checkpoint_path=albert_checkpoint_path,
            albert_config_path=albert_config_path,
            albert_dict_path=albert_dict_path,
            lgb_path=lgb_path,
            threshold=threshold,
            redis_expiration_time=redis_expiration_time,
            redis_ip=redis_ip,
            redis_port=redis_port,
            redis_pwd=redis_pwd
        )
        self.key_redis_faq_id = 'top_similar_pairs' # 知识库在redis中key中标示
        self.feature_extractor = FeatureExtractor(self.config)
        self.similar_invert_index = self.load_similar_invert_index()


    def add_to_clustering_group(self, video_id, text):
        """
        聊天过程中时时进行分组
        :param video_id: video id
        :param text: 用书输入query
        :return: 当前query与历史query共同聚类
        """
        res = []
        video_keys = gen_redis_keys(video_id)
        # 获取历史query
        queris = self.feature_extractor.redis_conn.lrange(video_keys.key_redis_queries_list, 0, -1)
        for query in queris:
            lcs_ab, abs_ab, min_rate, max_rate = self.feature_extractor.LCSeq(self.key_redis_faq_id, text, query)
            # if max_rate < 0.4 or min_rate < 0.3:
            #     continue
            if max_rate < 0.4:
                continue

        # 将本次加入历史query 列表
        self.feature_extractor.redis_conn.lpush(video_keys.key_redis_queries_list, text)
        # 实时记录某个query 出现的总次数
        self.feature_extractor.redis_conn.hincrby(name=video_keys.key_redis_queries_cnt, key=text, amount=1)

        # 取得历史计算的结果
        dic_keys = self.feature_extractor.redis_conn.hkeys(video_keys.key_redis_clustering_groups)

        dic_clustering_groups = {}
        for k in dic_keys:
            dic_clustering_groups[k] = {}
            sim_query_score = json.loads(
                self.feature_extractor.redis_conn.hget(video_keys.key_redis_clustering_groups, k))
            # 格式 {k:{s1:v1,s2:v2,s3:v3}"}
            for k_s, k_v in sim_query_score.items():
                dic_clustering_groups[k][k_s] = k_v

        # text 已经作为种子不再计算（a后面每加入一个query 都会与dic中的所有query计算过）
        if text in dic_clustering_groups:
            # text 已经计算过，直接返回上次结果
            list_set = []
            for key_query in dic_clustering_groups:
                self.feature_extractor.redis_conn.delete(video_keys.key_redis_res_temp_query_groups)
                # 本身同意数据较少，组中结点，有一个结点满足相似阈值，就加入组中
                self.feature_extractor.get_groups(video_id, dic_clustering_groups, key_query)
                res_temp_query_pairs = self.feature_extractor.redis_conn.smembers(
                    video_keys.key_redis_res_temp_query_groups)
                list_set.append(res_temp_query_pairs)
            res_merge_list = self.feature_extractor.merge_list(list_set)
            for i, list_group in enumerate(res_merge_list):
                cnt = 0
                for q in list_group:
                    cnt += float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_queries_cnt, q))
                group_info = "{group_id:%s,hit_amount:%s,item_amount:%s,items:%s}" % (
                i, cnt, len(list_group), list_group)
                res.append(group_info)
            return res
        else:
            dic_clustering_groups[text] = {}
            # 记录自身到自身的计算结果, 不可为空
            dic_clustering_groups[text][text] = 0.510910442483746  # str((0.52, a, a))

        for b in queris:
            if len(text) == 0 or len(b) == 0:
                continue

            # 相同query 不做计算
            if text == b:
                continue

            # 计算过b,text 不再计算
            if b in dic_clustering_groups:
                if text in dic_clustering_groups[b]:
                    continue

            # 计算过text,b 不再计算
            if b in dic_clustering_groups[text]:
                continue

            ra = text + b
            rb = b + text
            score = 0.00

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, ra):
                score = float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_sentence_similarity, ra))

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, rb):
                score = float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_sentence_similarity, rb))

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, ra) == False \
                    and self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity,
                                                                  rb) == False:
                X, info = self.feature_extractor.get_features(video_id, text, b)
                x = [numpy.array(X)]
                score = float(self.feature_extractor.lightGBM_processor.lightGBM.predict(x,
                                                                                         num_iteration=self.feature_extractor.lightGBM_processor.lightGBM.best_iteration)[
                                  0])
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_sentence_similarity, ra, score)
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_sentence_similarity, rb, score)

            if score > float(self.config.threshold):
                dic_clustering_groups[text][b] = score

        # 将最新结果更新到redis
        for key in dic_clustering_groups:
            for key_sim in dic_clustering_groups[key]:
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_clustering_groups, key,
                                                       json.dumps({key_sim: dic_clustering_groups[key][key_sim]}))

        list_set = []
        for key_query in dic_clustering_groups:
            self.feature_extractor.redis_conn.delete(video_keys.key_redis_res_temp_query_groups)
            # 本身同意数据较少，组中结点，有一个结点满足相似阈值，就加入组中
            self.feature_extractor.get_groups(video_id, dic_clustering_groups, key_query)
            res_temp_query_pairs = self.feature_extractor.redis_conn.smembers(
                video_keys.key_redis_res_temp_query_groups)
            list_set.append(res_temp_query_pairs)

        res_merge_list = self.feature_extractor.merge_list(list_set)

        for i, list_group in enumerate(res_merge_list):
            cnt = 0
            for q in list_group:
                cnt += float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_queries_cnt, q))
            group_info = "{group_id:%s,hit_amount:%s,item_amount:%s,items:%s}" % (
            i, cnt, len(list_group), list_group)
            res.append(group_info)

        # 设置redis过期时间
        for redis_key in video_keys:
            # 小时 * 3600s
            self.feature_extractor.redis_conn.expire(redis_key, self.config.redis_expiration_time * 3600)

        return res

    def add_to_query_clustering(self, video_id, text):
        """
        聊天过程中时时进行分组
        :param video_id: video id
        :param text: 用书输入query
        :return: 当前query与历史query共同聚类
        """
        res = []
        video_keys = gen_redis_keys(video_id)
        # 获取历史query
        queris = self.feature_extractor.redis_conn.lrange(video_keys.key_redis_queries_list, 0, -1)
        for query in queris:
            lcs_ab, abs_ab, min_rate, max_rate = self.feature_extractor.LCSeq(self.key_redis_faq_id, text, query)
            # if max_rate < 0.4 or min_rate < 0.3:
            #     continue
            if max_rate < 0.6:
                continue

        # 将本次加入历史query 列表
        self.feature_extractor.redis_conn.lpush(video_keys.key_redis_queries_list, text)
        # 实时记录某个query 出现的总次数
        self.feature_extractor.redis_conn.hincrby(name=video_keys.key_redis_queries_cnt, key=text, amount=1)

        # 取得历史计算的结果
        dic_keys = self.feature_extractor.redis_conn.hkeys(video_keys.key_redis_clustering_groups)

        dic_clustering_groups = {}
        for k in dic_keys:
            dic_clustering_groups[k] = {}
            sim_query_score = json.loads(
                self.feature_extractor.redis_conn.hget(video_keys.key_redis_clustering_groups, k))
            # 格式 {k:{s1:v1,s2:v2,s3:v3}"}
            for k_s, k_v in sim_query_score.items():
                dic_clustering_groups[k][k_s] = k_v

        # text 已经作为种子不再计算（a后面每加入一个query 都会与dic中的所有query计算过）
        if text in dic_clustering_groups:
            # text 已经计算过，直接返回上次结果
            list_set = []
            for key_query in dic_clustering_groups:
                self.feature_extractor.redis_conn.delete(video_keys.key_redis_res_temp_query_groups)
                # 本身同意数据较少，组中结点，有一个结点满足相似阈值，就加入组中
                self.feature_extractor.get_groups(video_id, dic_clustering_groups, key_query)
                res_temp_query_pairs = self.feature_extractor.redis_conn.smembers(
                    video_keys.key_redis_res_temp_query_groups)
                list_set.append(res_temp_query_pairs)
            res_merge_list = self.feature_extractor.merge_list(list_set)
            for i, list_group in enumerate(res_merge_list):
                cnt = 0
                for q in list_group:
                    cnt += float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_queries_cnt, q))
                group_info = "{group_id:%s,hit_amount:%s,item_amount:%s,items:%s}" % (
                i, cnt, len(list_group), list_group)
                res.append(group_info)
            return res
        else:
            dic_clustering_groups[text] = {}
            # 记录自身到自身的计算结果, 不可为空
            dic_clustering_groups[text][text] = 0.510910442483746  # str((0.52, a, a))

        for b in queris:
            if len(text) == 0 or len(b) == 0:
                continue

            # 相同query 不做计算
            if text == b:
                continue

            # 计算过b,text 不再计算
            if b in dic_clustering_groups:
                if text in dic_clustering_groups[b]:
                    continue

            # 计算过text,b 不再计算
            if b in dic_clustering_groups[text]:
                continue

            ra = text + b
            rb = b + text
            score = 0.00

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, ra):
                score = float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_sentence_similarity, ra))

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, rb):
                score = float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_sentence_similarity, rb))

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, ra) == False \
                    and self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity,
                                                                  rb) == False:
                X, info = self.feature_extractor.get_features(video_id, text, b)
                x = [numpy.array(X)]
                score = float(self.feature_extractor.lightGBM_processor.lightGBM.predict(x,
                                                                                         num_iteration=self.feature_extractor.lightGBM_processor.lightGBM.best_iteration)[
                                  0])
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_sentence_similarity, ra, score)
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_sentence_similarity, rb, score)

            if score > float(self.config.threshold):
                dic_clustering_groups[text][b] = score

        # 将最新结果更新到redis
        for key in dic_clustering_groups:
            for key_sim in dic_clustering_groups[key]:
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_clustering_groups, key,
                                                       json.dumps({key_sim: dic_clustering_groups[key][key_sim]}))

        list_set = []
        for key_query in dic_clustering_groups:
            self.feature_extractor.redis_conn.delete(video_keys.key_redis_res_temp_query_groups)
            # 本身同意数据较少，组中结点，有一个结点满足相似阈值，就加入组中
            self.feature_extractor.get_groups(video_id, dic_clustering_groups, key_query)
            res_temp_query_pairs = self.feature_extractor.redis_conn.smembers(
                video_keys.key_redis_res_temp_query_groups)
            list_set.append(res_temp_query_pairs)

        res_merge_list = self.feature_extractor.merge_list(list_set)

        for i, list_group in enumerate(res_merge_list):
            cnt = 0
            for q in list_group:
                cnt += float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_queries_cnt, q))
            group_info = "{group_id:%s,hit_amount:%s,item_amount:%s,items:%s}" % (
            i, cnt, len(list_group), list_group)
            res.append(group_info)

        # 设置redis过期时间
        for redis_key in video_keys:
            # 小时 * 3600s
            self.feature_extractor.redis_conn.expire(redis_key, self.config.redis_expiration_time * 3600)

        return res

    def query_clustering(self, filename, queries:list):
        res = ''
        for test in queries:
           res = self.add_to_clustering_group(filename, test)
        return res

    def get_top_similar_queries(self, query, threshold=0.32):
        """
        取出大于阈值的相似query
        :param query: 用户输入的query
        :param threshold: 阈值内容
        :return: 返回与query相似, 并且大于阈值的query列表
        """
        # oldtime = datetime.datetime.now()
        dic_score_temp = {}
        res  = []
        video_keys = gen_redis_keys(self.key_redis_faq_id)
        # t = datetime.datetime.now()
        # print(u'gen_redis_keys 相差：%s豪秒\n' % ((t - oldtime).total_seconds() * 1000))
        # 获取历史query
        queris = set()
        query_filter = self.similar_invert_index.fiter(query)
        for char in query_filter:
            recall_list = self.similar_invert_index.get_char_ed_recall(char)
            queris = queris | set(recall_list)

        for sim_query in queris:
            lcs_ab, abs_ab, min_rate, max_rate = self.feature_extractor.LCSeq(self.key_redis_faq_id, sim_query, query)
            # if max_rate < 0.4 or min_rate < 0.3:
            #     continue
            if max_rate < 0.4:
                continue
            X, info = self.feature_extractor.get_features(self.key_redis_faq_id, sim_query, query)
            x = [numpy.array(X)]
            # t11 = datetime.datetime.now()
            # print(u'feature_extractor.get_features  相差：%s豪秒\n' % ((t11 - t1).total_seconds() * 1000))
            score = float(self.feature_extractor.lightGBM_processor.lightGBM.predict(x,
                                                                                     num_iteration=self.feature_extractor.lightGBM_processor.lightGBM.best_iteration)[
                              0])
            if score < threshold:
                continue
            dic_score_temp[sim_query] = score
            # t12 = datetime.datetime.now()
            # print(u'lightGBM_processor.lightGBM.predict  相差：%s豪秒\n' % ((t12 - t11).total_seconds() * 1000))
            # print(score, compair, query)
        # t2 = datetime.datetime.now()
        # print(u'get_features  lightGBM_processor 相差：%s豪秒\n' % ((t2 - t1).total_seconds() * 1000))
        dic_score = sorted(dic_score_temp.items(), key=lambda item: item[1], reverse=True)
        for sim_pair in dic_score:
            sim_query = sim_pair[0]
            score = sim_pair[1]
            query_answer = self.feature_extractor.redis_conn.hmget(video_keys.key_redis_question_answer_list, sim_query)
            res.append('{question:%s,answer:%s,score:%s}' % (sim_query, query_answer[0], str(float(score) /0.510910442483746)[0:4]))
        # t3 = datetime.datetime.now()
        # print(u'feature_extractor.redis_conn.hkeys  相差：%s豪秒\n' % ((t3 - t2).total_seconds() * 1000))
        return res


    def load_similar_invert_index(self):
        video_keys = gen_redis_keys(self.key_redis_faq_id)
        queris = self.feature_extractor.redis_conn.hkeys(video_keys.key_redis_question_answer_list)
        similar_inverted_index_path = os.path.join(__dir__, '../../data/similar_inverted_index.pkl')
        similar_invert_index = Inverted_Index(queris, similar_inverted_index_path)
        similar_invert_index.load_inverted_dic()
        # t1 = datetime.datetime.now()
        # print(u'feature_extractor.redis_conn.hkeys  相差：%s豪秒\n' % ((t1 - t).total_seconds() * 1000))
        # print(len(queris))
        # 数据库变更，更新倒排索引
        queris_temp_set = set()
        for value in similar_invert_index.terms_inverted_index_dic.values():
            queris_temp_set = queris_temp_set | value
        diff_data = set(queris) ^ queris_temp_set
        if len(diff_data) > 0:
            similar_invert_index.updata_inverted_index(queris)
        return similar_invert_index

    def init_faq_queries_fetures(self, qa_pairs = { }):
        """
        store the faq data and features into redis
        :param qa_pairs : the question and answer pairs
        :return: null
        """
        video_keys = gen_redis_keys(self.key_redis_faq_id)
        for q, a in qa_pairs.items():
            # 加入或者修改最新的query 对
            self.feature_extractor.redis_conn.hset(video_keys.key_redis_question_answer_list, q, a)
            # 初始化faq库，并生成faq数据特征，并且写入redis, 不再重复计算
            pairs = q + q
            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, pairs):
                score = float(self.feature_extractor.redis_conn.hget(video_keys.key_redis_sentence_similarity, pairs))

            if self.feature_extractor.redis_conn.hexists(video_keys.key_redis_sentence_similarity, pairs) == False:
                X, info = self.feature_extractor.get_features(video_keys.key_redis_sentence_similarity, q, q)
                x = [numpy.array(X)]
                score = float(self.feature_extractor.lightGBM_processor.lightGBM.predict(
                        x, num_iteration=self.feature_extractor.lightGBM_processor.lightGBM.best_iteration)[0]
                    )
                self.feature_extractor.redis_conn.hset(video_keys.key_redis_sentence_similarity, pairs, score)
            print(q,a,score)
