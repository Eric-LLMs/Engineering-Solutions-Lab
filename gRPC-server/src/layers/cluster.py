# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: cluster.py
@Author:
@Time: 12月 25, 2020
"""

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(__dir__, '../interfaces'))
sys.path.append(os.path.abspath(os.path.join(__dir__, '../')))

from framework.layer import BaseLayer
from src.layers.features_extractor import *
from src.layers.comment_analyzer import CommentAnalyzer


class ClusterLayer(BaseLayer):
    '''检测并发层实现类'''
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = CommentAnalyzer(**kwargs)

    def process(self, data, **kwargs):
        '''
        query分组
        @param video_id: video id
        @param texts: texts that users input
        @return groups of all texts
        '''
        filename, queries = data
        groups = self.model.query_clustering(filename, queries)
        yield groups
