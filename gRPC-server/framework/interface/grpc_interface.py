import logging
import grpc
import multiprocessing
import os
import threading

from .base_interface import BaseInterface
from grpc._server import _RequestIterator
from framework import app, FrameworkException, ErrCode, loadClass
from framework.dictmgr import DictManager
from framework.performance import PerformanceTimer
from concurrent.futures import ThreadPoolExecutor
from types import GeneratorType

class GrpcInterface(BaseInterface):
    '''
    grpc 接口
    '''
    def __init__(self, name: str=None):
        super(self.__class__, self).__init__(name)

    def loadFromConfig(self, listen_port, num_workers=0, services={}):
        '''
        从配置数据中创建接口
        '''
        self.listen_port = listen_port
        if self.listen_port is None:
            self.logger.error('no listen_port specified')
            raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

        self.num_workers = num_workers
        if self.num_workers <= 0: # 使用 cpu 核心数替代
            self.num_workers = multiprocessing.cpu_count()
            self.logger.info('set num_workers to {}(cpu cores)'.format(self.num_workers))

        self.services = services
        if self.services is None:
            self.logger.error('no services specified')
            raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

    def run(self):
        '''
        启动接口运行
        '''
        self.grpc = grpc.server(ThreadPoolExecutor(max_workers=self.num_workers),
            options=(
                ('grpc.max_send_message_length', 50 * 1024 * 1024),
                ('grpc.max_receive_message_length', 50 * 1024 * 1024)
            )
        )

        # 加入所有grpc service实现类
        for name, value in self.services.items():
            clsname = value.get('class', None)
            c = loadClass(clsname)
            if c is None:
                self.logger.error('failed to load grpc service {}'.format(clsname))
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)
            elif GrpcService not in c.__bases__:
                self.logger.error('loaded invalid grpc service {}: not inherited from {}'.format(clsname, GrpcService.__name__))
                raise FrameworkException(errcode=ErrCode.INVALID_CONFIG_DATA)

            # 创建服务并加入到接口
            svr = c(**value.get('args', {}))
            svr.addToGrpcInterface(self)

        bind = self.grpc.add_insecure_port('[::]:{}'.format(self.listen_port))
        if bind != self.listen_port: # 绑定失败
            self.logger.error('failed to bind port {} for {}'.format(self.listen_port, self))
            raise FrameworkException(errcode=ErrCode.INTERFACE_BIND_ERROR)

        self.grpc.start()
        self.logger.info('{} start running, listen port {}, {} workers'.format(self, self.listen_port, self.num_workers))

    def stop(self):
        '''
        停止接口运行
        '''
        self.grpc.stop(0)
        self.logger.info('{} stopped'.format(self))

class GrpcService():
    '''
    grpc服务端基类
    '''
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dictmgr = DictManager()    # 词典管理器
        self.reload_mutex = threading.RLock()

    def __repr__(self):
        return self.__class__.__name__

    def addToGrpcInterface(self, interface: GrpcInterface):
        '''
        加入到grpc接口
        @param interface: grpc 接口
        '''
        raise NotImplementedError()

    def beforeRequest(self, request, context, logInfo: dict):
        '''
        处理api请求的前置函数
        '''
        pass

    def afterRequest(self, request, context, response, logInfo: dict):
        '''
        处理api请求的后置函数
        '''
        pass

    @staticmethod
    def grpc_interface(f):
        def wrapper(self, request, context):
            '''
            @param request: grpc request
            @param context: grpc context
            @param logInfo: 附加日志dict
            '''
            timer = PerformanceTimer()
            timer.start()

            logInfo = {}    # k-v 形式日志数据
            response = None

            try:
                # 前置处理
                self.beforeRequest(request, context, logInfo)

                response = f(self, request, context, logInfo)

                return response
            except:
                import traceback
                self.logger.error(traceback.format_exc())
                raise
            finally:
                # 后置处理
                self.afterRequest(request, context, response, logInfo)

                timer.stop()

                # 全局请求数增加
                with app.counter[1]:
                    app.counter[0].value += 1
                    request_counter = app.counter[0].value

                # 输出日志
                extraLog = ' '.join([ '{}={}'.format(k, v) for k, v in logInfo.items() if k != 'key' and (type(v) != str or len(v) > 0)]) if len(logInfo) > 0 else ''

                self.logger.info('{} * {} {:08d} api={} tm={} rz={} sz={} ip={} pid={} {} '.format(
                    self,
                    threading.currentThread().ident, # 线程id
                    request_counter,
                    f.__name__, # api函数名
                    timer.read_microsecond(), # 请求耗时，单位：微妙
                    request.ByteSize(), # 请求包大小
                    response.ByteSize() if response is not None else 0, # 响应包大小
                    ':'.join(context.peer().split(':')[1:-1]), # 请求方ip
                    os.getpid(), # 进程id
                    extraLog, # 其他字段
                ))

        return wrapper

    @staticmethod
    def grpc_stream_interface(f):
        '''针对输出为stream的接口修饰器'''
        def wrapper(self, request, context):
            '''
            @param request: grpc request
            @param context: grpc context
            @param logInfo: 附加日志dict
            '''
            timer = PerformanceTimer()
            timer.start()

            logInfo = {}    # k-v 形式日志数据
            request_sz = 0  # 请求包大小
            response_sz = 0 # 响应包大小

            try:
                # 前置处理
                if not isinstance(request, _RequestIterator): # 单请求
                    self.beforeRequest(request, context, logInfo)
                    request_sz = request.ByteSize()

                for each in f(self, request, context, logInfo):
                    try:
                        yield each
                    except:
                        break
                    else:
                        response_sz += each.ByteSize()
            except:
                import traceback
                self.logger.error(traceback.format_exc())
                raise
            finally:
                timer.stop()

                if isinstance(request, _RequestIterator):
                    request_sz = logInfo.get('_rz', 0)

                # 全局请求数增加
                with app.counter[1]:
                    app.counter[0].value += 1
                    request_counter = app.counter[0].value

                # 输出日志
                extraLog = ' '.join([ '{}={}'.format(k, v) for k, v in logInfo.items() if k != 'key' and (not k.startswith('_')) and (type(v) != str or len(v) > 0)]) if len(logInfo) > 0 else ''

                self.logger.info('{} * {} {:08d} api={} tm={} rz={} sz={} ip={} pid={} {} '.format(
                    self,
                    threading.currentThread().ident, # 线程id
                    request_counter,
                    f.__name__, # api函数名
                    timer.read_microsecond(), # 请求耗时，单位：微妙
                    request_sz, # 请求包大小
                    response_sz, # 响应包大小
                    ':'.join(context.peer().split(':')[1:-1]), # 请求方ip
                    os.getpid(), # 进程id
                    extraLog, # 其他字段
                ))

        return wrapper
