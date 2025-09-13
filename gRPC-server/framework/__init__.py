import importlib
import logging
import logging.config
import multiprocessing
import os
import time
import traceback
import uuid
import yaml

from .logging_file_handler import DebugRotatingFileHandler
from enum import Enum
from framework.performance import PerformanceTimer
from pathlib import Path

class ErrCode(Enum):
    '''错误码'''
    FAILED = 1
    FAILED_TO_LOAD_FILE = 2 # 载入文件失败
    INVALID_CONFIG_DATA = 3 # 非法的配置数据
    INVALID_DATA = 4    # 非法数据

    INTERFACE_BIND_ERROR = 100  # 接口绑定错误
    PARALLEL_LAYER_ERROR = 101  # 并发层错误

    BACKEND_UNAVAILABLE = 11001 # 后端不可用
    BACKEND_TIMEOUT = 11002 # 后端超时
    BACKEND_METHOD_NOT_IMPLEMENTED = 11003  # 后端方法未实现

class FrameworkException(Exception):
    '''框架异常'''
    def __init__(self, errcode: ErrCode=ErrCode.FAILED, *args):
        super(self.__class__, self).__init__(self, *args)
        self.errcode = errcode

    def __str__(self):
        return str(self.errcode)

def loadClass(clsname: str):
    '''
    动态载入类
    @param clsname: 类名
    @return 类对象，如果不存在，则返回 None
    '''
    if clsname is None: return None

    try:
        splitNames = clsname.split('.')
        modulename = '.'.join(splitNames[:-1])
        classname = splitNames[-1]

        m = importlib.import_module(modulename)
        c = getattr(m, classname)
    except Exception as ex:
        logging.error('failed to load class name "{}"'.format(clsname))
        if not isinstance(ex, FrameworkException):
            logging.error(traceback.format_exc())
        return None

    return c

def loadYamlConfig(fname):
    '''
    载入yaml格式配置数据
    @param fname: 配置文件名
    @return 载入的配置数据，如果载入失败，返回 None
    '''
    try:
        with open(fname, 'rt') as f:
            config = yaml.safe_load(f)

        return config
    except:
        return None

class DynamicInfo():
    '''
    动态数据信息
    '''
    def __init__(self, manager):
        version = manager.Value('i', 1) # 数据版本

class App():
    '''
    服务应用程序类
    '''
    CONF_DIR = 'conf'

    def __init__(self):
        '''
        初始化
        '''
        self.manager = multiprocessing.Manager()

        self.datavers = self.manager.dict() # 记录不同动态数据的版本号

        self.datainfo = self.manager.dict() # 记录不同动态数据信息

    def run(self):
        '''
        开始运行
        '''
        # 初始化 logger
        self.logger = logging.getLogger(self.__class__.__name__)
        # 载入logging.yml
        fname = '{}/logging.yml'.format(self.CONF_DIR)
        data = loadYamlConfig(fname)
        if data is None:
            self.logger.critical('failed to load {}'.format(fname))
            raise FrameworkException(errcode=ErrCode.FAILED_TO_LOAD_FILE)
        else:
            logging.config.dictConfig(data)
        self.logger.info('logging initialized')

        # 载入service.yml
        fname = '{}/service.yml'.format(self.CONF_DIR)
        self.config = loadYamlConfig(fname)
        if self.config is None:
            self.logger.critical('failed to load {}'.format(fname))
            raise FrameworkException(errcode=ErrCode.FAILED_TO_LOAD_FILE)
        self.logger.info('{} loaded'.format(fname))

        self.counter = self.manager.Value('i', 0), self.manager.RLock() # 请求计数器
        self.isexit = self.manager.Event() # 退出事件
        self.exited = self.manager.Event() # 已退出事件
        self.interfaces = [] # 所有接口
        self.layers = {} # 所有并发层
        self.output = self.manager.dict() # 保存并发结果的词典

        # 启动并发层
        self.run_layers()

        # 启动服务接口
        self.run_interfaces()

        # 等待结束
        self.waitForTerminate()

    def run_interfaces(self):
        '''
        启动服务接口
        '''
        from framework.interface import loadInterface, BaseInterface

        interface_config = self.config.get('interfaces', None)
        if interface_config is None:
            self.logger.critical('no interface specified!')
            raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

        for name, value in interface_config.items():
            clsname = value.get('class', None)
            if clsname is None:
                self.logger.critical('no interface class specified')
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

            c = loadClass(clsname)
            if c is None:
                self.logger.critical('failed to load interface class {}'.format(clsname))
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)
            elif BaseInterface not in c.__bases__:
                self.logger.critical('loaded invalid interface {}: not inherited from {}'.format(clsname, BaseInterface.__name__))
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

            interface = loadInterface(c, name, **value.get('args', {}))

            try:
                interface.run()
            except Exception as ex:
                self.logger.critical('failed to run {}'.format(interface))

                if not isinstance(ex, FrameworkException):
                    self.logger.error(traceback.format_exc())

                self.isexit.set()
                self.waitForTerminate()
                raise FrameworkException(errcode=ErrCode.FAILED)

            self.interfaces.append(interface)

        self.logger.info('all interfaces running')

    def run_layers(self):
        '''
        启动并发层
        '''
        from framework.layer import loadLayer, BaseLayer, LayerMode, ParallelLayer

        layer_config = self.config.get('layers', None)
        if layer_config is None:
            self.logger.info('no parallel layers specified')
            layer_config = {}

        for name, value in layer_config.items():
            clsname = value.get('class', None)
            if clsname is None:
                self.logger.critical('no parallel layer class specified')
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

            c = loadClass(clsname)
            if c is None:
                self.logger.critical('failed to load interface class {}'.format(clsname))
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

            layer = loadLayer(c, **value.get('args', {}))
            layer.name = name
            mode = value.get('mode', ParallelLayer.mode)
            if mode == 'thread':
                layer.mode = LayerMode.MULTI_THREAD
            elif mode == 'process':
                layer.mode = LayerMode.MULTI_PROCESS
            elif isinstance(mode, LayerMode):
                pass
            else:
                self.logger.critical('invalid parallel layer mode: {}'.format(mode))
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)
            layer.num_workers = value.get('num_workers', ParallelLayer.num_workers)
            layer.max_queue_size = value.get('max_queue_size', ParallelLayer.max_queue_size)
            layer.queue = self.manager.Queue(layer.max_queue_size)

            self.layers[name] = layer

        # 创建完所有并发层后，启动并发层
        for _, layer in self.layers.items():
            try:
                layer.run()
            except Exception as ex:
                self.logger.critical('failed to run {}'.format(layer))

                if not isinstance(ex, FrameworkException):
                    self.logger.error(traceback.format_exc())

                self.isexit.set()
                self.waitForTerminate()
                raise FrameworkException(errcode=ErrCode.FAILED)

    def waitForTerminate(self):
        '''
        等待app结束
        '''
        try:
            while not self.isexit.is_set():
                # 检查并发层是否正常
                for _, layer in self.layers.items():
                    if not layer.isHealthy():
                        self.logger.critical('parallel layer {} health check failed'.format(layer))
                        self.isexit.set()
                        raise FrameworkException(errcode=ErrCode.PARALLEL_LAYER_ERROR)

                self.isexit.wait(1)
        except:
            if not self.isexit.is_set():
                self.isexit.set()
            raise
        else:
            self.exited.set()
            time.sleep(1)   # 等待一会儿，用于可能的shutdown接口返回结果给客户端
        finally:
            # 关闭所有并发层
            for _, one in self.layers.items():
                one.stop()
            self.logger.info('all parallel layers stopped')

            # 关闭所有接口
            for one in self.interfaces:
                one.stop()
            self.logger.info('all interfaces stopped')

            self.logger.info('app gracefully exited')

    def parallel(self, data: list, emits: list, **kwargs) -> list:
        '''
        调用并发任务
        @param data: 请求数据
        @param emits: 并发层调用列表
        @return 返回结果，如果发生错误，返回 None
        '''
        if len(emits) == 0:
            return []
        else:
            for one in emits:
                if one not in self.layers:
                    self.logger.error('invalid parallel layer {} in emit list'.format(one))
                    return None

        timer = PerformanceTimer()
        timer.start()

        # 请求id
        idd = str(uuid.uuid1())
        app.output[idd] = self.manager.dict({
            'cnt': self.manager.Value('i', len(data)), # 记录计算任务数
            'lock': self.manager.RLock(),   # cnt lock
            'err': self.manager.Value('i', 0), # 是否错误
            'done': self.manager.Event(), # 处理完成事件
        })

        # 请求并发层
        firstLayer = emits[0]
        for i, one in enumerate(data):
            request = (
                '{}:{:08d}'.format(idd, i),
                one,
                emits[1:], # 表示子请求结束后，需要调用的后续并发层列表
                kwargs, # 并发层参数
            )
            self.layers[firstLayer].queue.put(request)

        # 等待并发层结束
        info = app.output[idd]

        while not self.isexit.is_set():
            info['done'].wait(1)

            if info['done'].is_set(): break

        # 获取结果数据
        resultCnt = 0
        if info['err'].value == 0:
            out = [ None ] * len(data)
            out_keys = [ None ] * len(data)
            key_prefix = '{}:'.format(idd)

            for key in sorted(self.output.keys()):
                if key.startswith(key_prefix):
                    idx = int(key.split(':', 2)[1])
                    if out_keys[idx] is None:
                        out_keys[idx] = []
                    out_keys[idx].append(key)

            for i, keys in enumerate(out_keys):
                if keys is None: continue
                elif len(keys) == 1: # 第i个输入只有一个结果，直接取值
                    out[i] = self.output[keys[0]]
                    resultCnt += 1
                else: # 第i个输入有超过一个结果，组成列表
                    out[i] = [ self.output[x] for x in sorted(keys) ]
                    resultCnt += len(keys)
        else:
            out = None

        # 删除本次任务的数据
        for key in self.output.keys():
            if key.startswith(idd):
                self.output.pop(key)

        timer.stop()
        self.logger.debug('got {:d} result(s) from layers [{}], costs {} ms'.format(resultCnt, ', '.join(emits), timer.read_millisecond()))

        return out

# 全局应用
app = App()
