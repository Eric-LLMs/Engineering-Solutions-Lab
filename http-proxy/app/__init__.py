# fastapi application

import sys

# initialize logging
from app.common import initLogger

try:
    initLogger()
except:
    sys.exit(1)

# 加载配置
from app.config import AppConfig, loadServiceConfig

config = loadServiceConfig()

# 初始化 fastapi
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from typing import Any

class SchdulerManager(dict):
    '''调度器封装，只是为了方便使用调度器'''
    def __getattr__(self, attr: str) -> Any:
        if attr in self:
            return self[attr]
        else:
            return None

class Application(FastAPI):
    def __init__(self, config: AppConfig):
        '''
        @param config: 服务配置数据
        '''
        # 关闭各种doc说明页
        super(self.__class__, self).__init__(
            title='Http-Proxy',
            version='2.0.0',
            docs_url=config.docs_url,
            openapi_url=config.openapi_url,
            redoc_url=config.redoc_url,
        )

        self.config = config.dynamics   # 动态配置
        self.tables = config.tables     # 表配置
        self.logger = logging.getLogger()
        self.schedulers = SchdulerManager() # 后端调度器
        self.thread_pool = ThreadPoolExecutor(config.thread_num * 2) # 使用两倍工作线程数作为线程池大小
        self.logger.info('thread pool gets ready, {} threading size'.format(config.thread_num * 2))

app = Application(config)

# 加载调度器
from app.scheduler import loadScheduler
# 初始化 scheduler
for k, v in config.schedulers.items():
    sched = loadScheduler(k, v)
    if sched is None:
        app.logger.critical('failed to initialize {} scheduler'.format(k))
        sys.exit(-1)
    app.schedulers[k] = sched

# 跨域处理
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ '*' ],
    allow_credentials=True,
    allow_methods=[ '*' ],
    allow_headers=[ '*' ],
)

# 加载视图
from app.views import *

@app.on_event('startup')
async def on_startup():
    app.logger.info('app is running, now')
