# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: albert_processor.py
@Author:
@Time: 11月 13, 2020
"""

import os
import sys

__dir__ = os.path.dirname(os.path.dirname(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.dirname(__dir__))

from src.bert4keras.utils import Tokenizer, load_vocab
from src.bert4keras.bert import build_bert_model
from keras.models import Model


class AlbertProcessor:
    def __init__(self, config):
        self.config = config
        self.tokenizer = Tokenizer(self.config.albert_dict_path)
        self.albert = self.load_albert_model()

    def load_albert_model(self,):
        # 加载预训练模型
        bert = build_bert_model(
            config_path=self.config.albert_config_path,
            checkpoint_path=self.config.albert_checkpoint_path,
            with_pool=True,
            albert=True,
            return_keras_model=False,
        )
        model = Model(bert.model.input, bert.model.output)
        return model
