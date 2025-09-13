import logging

class DynamicData():
    '''
    动态数据
    '''
    def __init__(self, name):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name

    def __expr__(self):
        if self.name:
            return '{}:{}'.format(self.__class__.__name__, self.name)
        else:
            return self.__class__.__name__

    def load(self, **kwargs) -> bool:
        '''
        载入数据
        @return true/false
        '''
        raise NotImplementedError()

    def release(self):
        '''
        释放数据
        '''
        raise NotImplementedError()
