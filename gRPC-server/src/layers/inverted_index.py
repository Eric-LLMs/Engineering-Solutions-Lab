# -*- coding: utf-8 -*-
import os
import sys

import re
import hashlib
import pickle

parent_path = os.path.abspath(os.path.join(os.getcwd(), "."))
sys.path.append(parent_path)


class Inverted_Index:
    def __init__(self, queries:list, inverted_index_path = 'similar_inverted_index.pkl'):
        self.terms_inverted_index_path = inverted_index_path
        self.terms_inverted_index_dic = {}
        self.queries = queries

    def dump_bk_tree(self):
        with open(self.terms_inverted_index_path, 'wb') as f:
            pickle.dump(self.terms_inverted_index_dic, f)

    def load_inverted_dic(self):
        if os.path.exists(self.terms_inverted_index_path):
            with open(self.terms_inverted_index_path, 'rb') as f:
                self.terms_inverted_index_dic = pickle.load(f)
        else:
            for text in self.queries:
                terms = self.fiter(text)
                for char in terms:
                    if char == '':
                        continue
                    if char in self.terms_inverted_index_dic:
                        self.terms_inverted_index_dic[char].add(text)
                    else:
                        self.terms_inverted_index_dic[char] = set()
                        self.terms_inverted_index_dic[char].add(text)
            self.dump_bk_tree()

    def updata_inverted_index(self, new_queries):
        self.queries = new_queries
        self.terms_inverted_index_dic = {}
        for text in self.queries:
            terms = self.fiter(text)
            for char in terms:
                if char == '':
                    continue
                if char in self.terms_inverted_index_dic:
                    self.terms_inverted_index_dic[char].add(text)
                else:
                    self.terms_inverted_index_dic[char] = set()
                    self.terms_inverted_index_dic[char].add(text)
        self.dump_bk_tree()

    def get_char_ed_recall(self, char, min = 1, max = 3):
        terms_list = []
        if char in self.terms_inverted_index_dic:
            terms = self.terms_inverted_index_dic[char]
            for term in terms:
                terms_list.append(term)
        return terms_list


    def is_Chinese(self, word):
        for ch in word:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False


    def fiter(self, text):
        reg = "[^\u4e00-\u9fa5]"
        return  re.sub(reg, '', text)


    def cut_sentences(self, content):
        sentences = re.split(r'(\.|\!|\?|。|，|,| |！|？|：|\.{6})', content)
        sents_amout = len(sentences)
        sen_pos_dic = {}
        sen_pos = 0
        for i in range(0, sents_amout):
            sent_start = sen_pos
            sent_length = len(sentences[i])
            sen_pos_dic[i] = [sent_start, sent_length]
            sen_pos = sent_start + sent_length
        return sen_pos_dic, sentences


    def get_str_md5(self, text):
        """
        获取str md5 编码
        :param str: 参数必须是utf8
        :return:
        """
        if isinstance(str, text):
            text = text.encode("utf-8")
        m = hashlib.md5()
        m.update(text)
        return m.hexdigest()
