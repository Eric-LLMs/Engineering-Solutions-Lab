import logging

class BaseInterface():
    '''
    接口基类
    '''
    def __init__(self, name: str=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name

    def __repr__(self):
        if self.name is None:
            return self.__class__.__name__
        else:
            return '{}:{}'.format(self.__class__.__name__, self.name)

    def loadFromConfig(self, **kwargs):
        '''
        从配置数据中创建接口
        @param config: 配置数据
        '''
        raise NotImplementedError()

    def run(self):
        '''
        启动接口的运行
        '''
        raise NotImplementedError()

    def stop(self):
        '''
        停止接口的运行
        '''
        raise NotImplementedError()
