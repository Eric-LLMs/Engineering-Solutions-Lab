#!/usr/bin/env python3
#coding=utf-8

import allure
import pytest

from .common import initializeClient

@pytest.mark.staging
@pytest.mark.pre
@pytest.mark.production
@pytest.mark.pressure
@allure.feature('ping')
class TestPing:
    @pytest.fixture(autouse=True)
    def setup(self, ip, port):
        self.client = initializeClient(ip, port)

    @allure.story('测试服务 ping 接口')
    @allure.severity(allure.severity_level.MINOR)
    def test_ping_local(self):
        '''
        测试ping本地是否成功
        '''
        with allure.step('请求服务 ping 接口'):
            self.client.ping('test')
