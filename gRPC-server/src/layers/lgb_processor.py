# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c)2020 acme.cn, All Rights Reserved.
#
########################################################################
"""
@File: lgb_processor.py
@Author:
@Time: 11月 13, 2020
"""

import lightgbm as lgb


class LGBProcessor:
    def __init__(self, config):
        self.config = config
        self.lightGBM = self.load_lgb_model()
        pass

    def load_lgb_model(self,):
        model = lgb.Booster(model_file=self.config.lgb_path)
        return model
