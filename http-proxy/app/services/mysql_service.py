import uuid
import http.client
import json
import pymysql
import time
import datetime
import records

from app.scheduler import RemoteServer
from app.views import AppRequest


class MysqlService(RemoteServer):
    ''' MySQL服务 '''

    def __init__(self, ip: str, port: int, user: str, pwd: str):
        '''
        @param ip:
        @param port
        '''
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.username = user
        self.password = pwd

        self.logger.debug('initialized {}'.format(self))

    def __repr__(self) -> str:
        return 'mysql {}:{}'.format(self.ip, self.port)

    def ping(self) -> bool:
        return True

    def getLogId(self) -> str:
        '''
        获取请求唯一 logid
        @return logid
        '''
        return 'logid-{}'.format(uuid.uuid1())

    def testLink(self, dbname):
        try:
            conn_string = ''.join('mysql+pymysql://%s:%s@%s:%d/%s' %
                                  (self.username, self.password, self.dbhost, self.dbport, dbname))
            db = records.Database(conn_string)
            data = db.query('SELECT VERSION()').all()
            print("Database version : %s " % data)
            if db:
                db.close()
            return True
        except Exception as e:
            self.logger.warn("查询出错：%s" % e)
        return False

    def do_search(self, dbname: str, table_name: str, search_condition: dict) -> list:
        '''
        @brief 查询表
        @param[in] dbname: db名称
        @param[in] table_name: 表名称
        @param[in] search_condition: 查询条件 
                like 
            {'patient_id':'eb25483fff564d2eb927822a429991cd','disease_course_id':'668216f63e33474cb05636404588ece5'}
        @param[in/out] results: 表拉取填充结果
            like:
            {'表名':[内容列表], '表名':[内容列表]}
        @return 查询结果列表
        '''
        db = None
        try:
            conn_string = ''.join('mysql+pymysql://%s:%s@%s:%d/%s' %
                                  (self.username, self.password, self.ip, self.port, dbname))
            db = records.Database(conn_string)
        except Exception as e:
            self.logger.warn("连接出错：%s" % e)
            db.close()
            return []
        if db == None:
            db.close()
            return []

        try:
            sql = "SELECT * FROM " + table_name + " WHERE "
            for (k, v) in search_condition.items():
                if v == None:
                    return []
                sql = sql + k + '=:' + k + ' and '
            sql = sql[:-5]
            data = (db.query(sql, **search_condition)).all(as_dict=True)
            db.close()
        except Exception as e:
            self.logger.warn("查询出错：%s" % e)
            db.close()
            return []

        return data
