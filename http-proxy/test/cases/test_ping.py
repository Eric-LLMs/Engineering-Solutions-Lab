import allure
import pytest

from .common import Client

@pytest.mark.dev
@pytest.mark.qa
@pytest.mark.staging
@pytest.mark.pre
@pytest.mark.production
@pytest.mark.pressure
@allure.feature('ping')
class TestPing:
    @pytest.fixture(autouse=True)
    def setup(self, ip, port):
        self.client = Client(ip, port)

    @allure.story('测试 ping 接口')
    @allure.severity(allure.severity_level.MINOR)
    def test_ping(self):
        self.client.ping()
