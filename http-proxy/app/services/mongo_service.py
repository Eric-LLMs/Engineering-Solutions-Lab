import uuid
import pymongo
import json

from app.scheduler import RemoteServer
from app.views import AppRequest


class MongoService(RemoteServer):
    ''' Mongodb服务'''

    def __init__(self, ip: str, port: int, user: str, pwd: str):
        '''
        @param[in] ip
        @param[in] port
        @param[in] user
        @param[in] pwd
        '''
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.user = user
        self.pwd = pwd

        self.logger.debug('initialized {}'.format(self))

    def __repr__(self) -> str:
        return 'mongo mongodb://{}:{}@{}:{}/'.format(self.user, self.pwd, self.ip, self.port)

    def ping(self) -> bool:
        return True

    def getLogId(self) -> str:
        '''
        获取请求唯一 logid
        @return logid
        '''
        return 'logid-{}'.format(uuid.uuid1())

    def search(self, dbname: str, table: str, key: str, value: str) -> list:
        '''
        @brief 依据kv查询mongo
        @param[in] dbname: 库名
        @param[in] table： 表名
        @param[in] key: 查询键名
        @param[in] value: 查询键值
        @return 返回结果集字典
        '''
        rets = []
        url = 'mongodb://' + str(self.ip) + ':' + str(self.port) + '/'
        client = pymongo.MongoClient(url)
        db = client[dbname]
        db.authenticate(str(self.user), str(self.pwd))
        col = db[table]
        results = col.find({key: value})
        for result in results:
            if 'deleted' in result and result['deleted'] == True:
                continue
            rets.append(result)
        return rets

    def do_search(self, dbname: str, table_name: str, search_condition: dict) -> list:
        '''
        @brief 依据kv查询mongo
        @param[in] dbname: 库名
        @param[in] table： 表名
        @param[in] search_condition: 查询条件
        @return 返回结果集字典
        '''
        rets = []
        url = 'mongodb://' + str(self.ip) + ':' + str(self.port) + '/'
        client = pymongo.MongoClient(url)
        db = client[dbname]
        db.authenticate(str(self.user), str(self.pwd))
        col = db[table_name]
        results = col.find(search_condition)
        for result in results:
            rets.append(result)
        return rets
