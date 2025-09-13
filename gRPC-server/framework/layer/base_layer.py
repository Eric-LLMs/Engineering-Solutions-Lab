import logging
import multiprocessing
import threading
import traceback

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError
from enum import Enum
from framework.dictmgr import DictManager
from multiprocessing.queues import Empty

class LayerMode(Enum):
    '''
    并发层模式
    '''
    MULTI_THREAD = 0    # 多线程，适合IO密集型并发
    MULTI_PROCESS = 1   # 多进程，适合CPU密集型并发

class ParallelLayer():
    '''
    并发层
    '''
    name = None # 并发层名
    mode = LayerMode.MULTI_PROCESS   # 并发层模式
    num_workers = 1 # 并发数
    max_queue_size = 1024   # 最大任务队列

    def __init__(self, c, **kwargs):
        '''
        初始化
        @param c: 并发层实现类
        @param kwargs: 并发层参数
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.impl = c # 实现类
        self.impl_kwargs = kwargs
        self.dictmgr = DictManager()    # 词典管理器

    def run(self):
        '''
        启动并发层
        '''
        readyEvents = []
        if self.mode == LayerMode.MULTI_THREAD:
            # 多线程模式
            self.pool = ThreadPoolExecutor(self.num_workers)
            self.logger.info('{} create thread pool * {}'.format(self, self.num_workers))
            for i in range(self.num_workers):
                readyEvents.append(threading.Event())
        elif self.mode == LayerMode.MULTI_PROCESS:
            # 多进程模式
            self.pool = ProcessPoolExecutor(self.num_workers)
            self.logger.info('{} create process pool * {}'.format(self, self.num_workers))
            manager = multiprocessing.Manager()
            for i in range(self.num_workers):
                readyEvents.append(manager.Event())

        # 启动 pool
        self.tasks = [ self.pool.submit(parallel_core, self.name, self.impl, self.impl_kwargs, readyEvents[i], i) for i in range(self.num_workers) ]
        for event in readyEvents:
            event.wait()

        self.logger.info('{} start running, {} mode, {} workers'.format(self, self.mode, self.num_workers))

    def stop(self):
        '''
        停止并发层
        '''
        self.logger.info('{} prepare to stop'.format(self))
        for task in self.tasks:
            task.cancel()

        self.logger.info('{} cancelled all tasks'.format(self))

        self.pool.shutdown(True)
        self.logger.info('{} stopped'.format(self))

    def isHealthy(self) -> bool:
        '''
        并发层是否健康
        @return true/false
        '''
        for task in self.tasks:
            try:
                e = task.exception(0)
                raise e
            except TimeoutError:
                pass
            except:
                self.logger.error(traceback.format_exc())
                return False

        return True

    def __repr__(self):
        if self.name is None:
            return self.__class__.__name__
        else:
            return '{}:{}'.format(self.__class__.__name__, self.name)

from framework import app
from framework.dictmgr import DictManager

class BaseLayer():
    '''
    并发层实现基类
    '''
    def __init__(self, **kwargs):
        '''
        初始化
        @param kwargs: 并发层参数
        '''
        self.logger = logging.getLogger(self.__class__.__name__)

    def __repr__(self):
        return self.__class__.__name__

    def registerDict(self, dictmgr: DictManager):
        '''
        注册词典
        '''
        pass

    def process(self, data, **kwargs):
        '''
        执行并发层
        @param data: 输入数据
        @param kwargs: 其他参数
        '''
        raise NotImplementedError()

def parallel_core(name, cls, cls_kwargs, ready, idx):
    '''
    并发层核心函数
    @param cls: 并发层实现类
    @param cls_kwargs: 并发层实现类配置
    @param ready: 并发层就绪
    @param idx: 并发idx
    '''
    layer = app.layers[name]
    try:
        impl = cls(**cls_kwargs)
        ready.set()
        # 设置dictmanager
        dictmgr = DictManager()

        # 注册词典
        impl.registerDict(dictmgr)

        layer.logger.info('{} instance no.{} initialized'.format(impl, idx))

        while not app.isexit.is_set():
            try:
                idd, input, emits, kwargs = layer.queue.get(timeout=1)

                iddroot = idd.split(':', 1)[0]

                for i, one in enumerate(impl.process(input, **(kwargs.get(layer.name, {})))):
                    # 检查idd请求是否失败
                    if app.output[iddroot]['err'].value != 0:
                        break

                    # 向后流水
                    next_idd = '{}:{:08d}'.format(idd, i)

                    if len(emits) == 0:
                        # 保存到 app.output
                        app.output[next_idd] = one
                    else:
                        nextLayer = emits[0]

                        info = app.output[iddroot]
                        with info['lock']:
                            info['cnt'].value += 1

                        request = (
                            next_idd,
                            one,
                            emits[1:],
                            kwargs,
                        )
                        app.layers[nextLayer].queue.put(request)

                info = app.output[iddroot]
                with info['lock']:
                    info['cnt'].value -= 1
                    if info['cnt'].value == 0:
                        info['done'].set()
            except Empty:
                continue
            except:
                import traceback
                layer.logger.error(traceback.format_exc())
                # 发生异常，请求失败
                info = app.output[iddroot]
                with info['lock']:
                    info['cnt'].value -= 1
                if info['cnt'].value == 0:
                    info['done'].set()
    except:
        layer.logger.error('parallel layer occurred exception')
        ready.set()
        raise
