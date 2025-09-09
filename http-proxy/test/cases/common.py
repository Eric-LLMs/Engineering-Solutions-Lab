import json
import requests
import uuid

class Client():
    '''
    search-proxy 客户端
    '''
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def _get(self, url: str, **kwargs):
        '''
        get url
        '''
        response = requests.get(url, params=kwargs)
        return response

    def getLogId(self):
        '''
        获取 logid
        @return logid
        '''
        return 'logid-{}'.format(uuid.uuid1())

    def ping(self):
        '''
        ping
        '''
        url = 'http://{}:{}/ping'.format(self.ip, self.port)

        self._get(url, source='pytest', logid=self.getLogId())
