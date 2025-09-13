import logging
import threading
import time
import traceback

from . import DictBuffer
from framework import app, loadClass

class DictReloadThread(threading.Thread):
    '''
    词典重载线程
    '''
    def __init__(self, dictmgr):
        '''
        @param dictmgr: 词典管理器
        '''
        super(self.__class__, self).__init__(daemon=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.dictmgr = dictmgr

    def run(self):
        self.logger.info('dict reload thread started')
        while not app.isexit.is_set():
            try:
                _changed = False

                for name, value in [ (name, value) for name, value in self.dictmgr.dicts.items() ]:
                    ver = app.datavers[name]
                    if value.version < ver: # 需要重载
                        if not value.reload():
                            self.logger.error('reload dict {} failed'.format(name))
                        else:
                            self.logger.info('reload dict {}, version -> {}'.format(name, ver))

                        value.version = ver
                        _changed = True

                # sleep 5s，避免频繁 reload
                if _changed:
                    time.sleep(5)
            except:
                app.logger.error('dict reload thread has an exception: {}'.format(traceback.format_exc()))
                app.isexit.set()
            finally:
                time.sleep(0.5)

class DictManager():
    '''
    词典管理器
    '''
    def __init__(self):
        '''
        初始化
        @param config: 词典配置数据
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dicts = {} # 记录所有的词典

        # 启动dict reload线程
        self.dictReloadThread = DictReloadThread(self)
        self.dictReloadThread.start()

    def registerDict(self, name: str, **kwargs) -> DictBuffer:
        '''
        注册词典
        @param name: 词典名
        @return 注册的词典，如果异常，返回 None
        '''
        if name not in self.dicts:
            # 创建
            buffer = DictBuffer(name, **kwargs)
            # 记录数据版本号
            app.datavers[name] = buffer.version
            self.dicts[name] = buffer
            self.logger.info('register dynamic dict {}'.format(name))

        return self.dicts[name]
