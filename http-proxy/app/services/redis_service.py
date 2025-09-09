import redis
import uuid
import os
import re
import time
from retrying import retry

from app.scheduler import RemoteServer
from app.views import AppRequest


class RedisService(RemoteServer):
    ''' redis服务 '''

    def __init__(self, ip: str, port: int, auth: str = '', db: int = 0, env: str = 'local'):
        '''
        @param ip:
        @param port
        @param auth: 权限密码
        @param db: db 号
        '''
        super(self.__class__, self).__init__()

        self.ip = ip
        self.port = port
        self.auth = auth
        self.db = db
        self.env = env

        self.pool = redis.ConnectionPool(
            host=ip, port=port, password=auth, db=db)
        self.r = redis.StrictRedis(connection_pool=self.pool)
        self.logger.debug('initialized {}'.format(self))

    def __repr__(self) -> str:
        return 'redis {}:{}, db {}'.format(self.ip, self.port, self.db)

    def ping(self) -> bool:
        return True

    def getPlaybackFirstDomainStr(self) -> str:
        '''
        获取redis存入key的一级域
        @return key
        '''
        # bs-build:playback:8:timestamp
        return 'bs-build-{}'.format(self.env)

    def getPlaybackSecondDomainStr(self) -> str:
        '''
        获取redis存入key的二级域
        @return key
        '''
        # bs-build:playback:8:timestamp
        return 'playback'

    def getNotifyIdxDocKey(self, idx: int = 0, timestamp: int = 0) -> str:
        '''
        获取建库索引计数器对应的redis key
        @param idx: 建库索引
        @return key
        '''
        # bs-build:playback:8:timestamp
        return '{}:{}:{}:{}'.format(self.getPlaybackFirstDomainStr(), self.getPlaybackSecondDomainStr(), idx, timestamp)

    def getNotifyIdxLockKey(self, idx: int = 0) -> str:
        '''
        获取建库索引锁定对应的redis key
        @param idx: 建库索引
        @return key
        '''
        return '{}:{}:{}:lock'.format(self.getPlaybackFirstDomainStr(), self.getPlaybackSecondDomainStr(), idx)

    def setNotifyIdxDoc(self, idx: int, timestamp: int, doc: str) -> int:
        '''
        @brief 存储建库doc至redis
        @param[in] timestamp: 时间戳
        @param[in] doc: 建库的json串
        @return 状态码 <0 失败
        '''
        main_key = self.getNotifyIdxDocKey(idx, timestamp)
        ret = self.r.rpush(main_key, doc)
        self.r.expire(main_key, 60*60*24*7)
        return ret

    def searchDocWithKey(self, key: str) -> list:
        '''
        @brief 通过key查找doc列表
        @param[in] idx: 建库索引
        @param[in] key: 查找key
        @return 文档列表
        '''
        ret = []
        for i in range(0, self.r.llen(key)):
            doc = self.r.lindex(key, i)
            doc = doc.decode('utf-8')
            ret.append(doc)

        return ret

    def parseRedisKey(self, key: str) -> tuple:
        recom = re.compile(r'{}:{}:(\d+):(\d+)'.format(
            self.getPlaybackFirstDomainStr(), self.getPlaybackSecondDomainStr()))
        m = recom.match(key)
        idx = int(m.group(1))
        timestamp = int(m.group(2))
        return (idx, timestamp)

    def searchDocWithTimescope(self, idx: int, btime: int, etime: int) -> list:
        '''
        @brief 依据时间范围从redis查找doc
        @param[in] idx: 建库索引
        @param[in] btime: 开始时间
        @param[in] etime: 结束时间
        @return doc列表
        '''
        bkey = self.getNotifyIdxDocKey(idx, btime)
        ekey = self.getNotifyIdxDocKey(idx, etime)

        # 公共前缀
        lkey = [bkey, ekey]
        common_pre = os.path.commonprefix(lkey)

        # 匹配表达式
        if (idx):
            re_match = '{}*'.format(common_pre)
        else:
            re_match = '{}:{}:*:*'.format(self.getPlaybackFirstDomainStr(),
                                          self.getPlaybackSecondDomainStr())

        # 先遍历得到所有相关键
        cursor = 1
        isFirst = True
        full_doc_keys = []
        while(cursor):
            if isFirst:
                isFirst = False
                cursor = 0
            ret = self.r.scan(cursor, re_match)
            cursor = int(ret[0])
            if (len(ret) > 1 and len(ret[1]) > 0):
                full_doc_keys.extend(ret[1])

        # 筛选出范围内键
        useful_keys = []
        for doc_key in full_doc_keys:
            doc_key = doc_key.decode('utf-8')
            ret = self.parseRedisKey(doc_key)
            idx = ret[0]
            timestamp = ret[1]
            if timestamp < btime or timestamp > etime:
                continue
            useful_keys.append(doc_key)
        useful_keys.sort()

        # 反向排序，时间从后往前
        useful_keys.reverse()

        # 查找key对应的doc列表,并进行回放
        ret = []
        for doc_key in useful_keys:
            if (len(self.searchDocWithKey(doc_key)) > 0):
                ret.extend(self.searchDocWithKey(doc_key))

        return ret

    def getBuildIdCounterKey(self, idx: int) -> str:
        '''
        @brief 生成建库id计数器的redis key
        @param[in] idx: 建库索引
        @return 建库id计数器的redis key
        '''
        return 'bs-build-{}:id-mapping:{}:counter'.format(self.env, idx)

    def getShieldDictFlagKey(self, idx: int) -> str:
        '''
        @brief 返回屏蔽词典可用标记的redis key
        @param[in] idx: 建库索引
        @return 可用标记的redis key
        '''
        return 'acme-algorithm-{}:bs-shielding-dict:{}:flag'.format(self.env, idx)

    def reset(self, idx: int) -> bool:
        '''
        @brief 重置索引
        @param[in] idx: 建库索引
        @return True:成功 False:失败
        '''
        # 删除counterKey
        counterKey = self.getBuildIdCounterKey(idx)
        ret = self.r.delete(counterKey)
        if ret < 0:
            raise Exception('redis delete key[{}] failed!'.format(counterKey))

        # 删除mapping
        re_match = 'bs-build-{}:id-mapping:{}:docid:*'.format(self.env, idx)
        full_doc_keys = []
        cursor = 0
        while (True):
            ret = self.r.scan(cursor, re_match, 50)
            cursor = int(ret[0])
            if (len(ret) > 1 and len(ret[1]) > 0):
                full_doc_keys.extend(ret[1])
            if not cursor:
                break
        for key in full_doc_keys:
            ret = self.r.delete(key)
            if ret < 0:
                raise Exception('redis delete key[{}] failed!'.format(key))
        # 屏蔽词典标记为不可用
        flagKey = self.getShieldDictFlagKey(idx)
        ret = self.r.set(flagKey, '0')
        self.r.expire(flagKey, 60*60*24*30)
        if ret < 0:
            raise Exception('redis set key[{}] failed!'.format(flagKey))

        # 删除屏蔽词典
        removeKey = self.getRemoveDocidKey(idx)
        ret = self.r.delete(removeKey)
        if ret < 0:
            raise Exception('redis delete key[{}] failed!'.format(removeKey))

        # 设置屏蔽词典开始时间戳
        timestamp = int(round(time.time() * 1000))
        timestampKey = self.getRemoveDictTimestampKey(idx)
        ret = self.r.set(timestampKey, timestamp)
        self.r.expire(timestampKey, 60*60*24*30)
        if ret < 0:
            raise Exception('redis set key[{}] failed!'.format(timestampKey))

        # 屏蔽词典标记为可用
        flagKey = self.getShieldDictFlagKey(idx)
        ret = self.r.set(flagKey, '1')
        self.r.expire(flagKey, 60*60*24*30)
        if ret < 0:
            raise Exception('redis set key[{}] failed!'.format(flagKey))

        # counter重新从0开始
        counterKey = self.getBuildIdCounterKey(idx)
        ret = self.r.set(counterKey, 0)
        self.r.expire(counterKey, 60*60*24*30)
        if ret < 0:
            raise Exception('redis set key[{}] failed!'.format(counterKey))

        return True

    def getBuildIdMappingKey(self, docid: str, typeid: int) -> str:
        '''
        @brief 生成建库id映射的redis key
        @param docid: 文档原始id
        @param typeid: 建库索引
        @return 建库id计数器的redis key
        '''
        return 'bs-build-{}:id-mapping:{}:docid:{}'.format(self.env, typeid, docid)

    def getgetMappingDocIdLua(self) -> str:
        '''
        @brief getMappingDocId lua 脚本
        '''
        ret = "if redis.call('EXISTS', ARGV[1]) == 0 then\n" \
            "    return {0, 0}\n" \
            "else\n" \
            "    local docid = redis.call('INCR', ARGV[1])\n" \
            "    if redis.call('EXISTS', ARGV[2]) == 0 then\n" \
            "        redis.call('HSET', ARGV[2], 'id', docid)\n" \
            "        redis.call('HSET', ARGV[2], 'timestamp', ARGV[3])\n" \
            "        return {0, docid}\n" \
            "    else\n" \
            "        local ts = redis.call('HGET', ARGV[2], 'timestamp')\n" \
            "        local olddocid = redis.call('HGET', ARGV[2], 'id')\n" \
            "        if ts and tonumber(ts) > tonumber(ARGV[3]) then \n" \
            "            return {tonumber(olddocid), 0}\n" \
            "        else\n" \
            "            redis.call('HSET', ARGV[2], 'id', docid)\n" \
            "            redis.call('HSET', ARGV[2], 'timestamp', ARGV[3])\n" \
            "            return {tonumber(olddocid), docid}\n" \
            "        end\n" \
            "    end\n" \
            "end"
        return ret

    def getMappingDocId(self, docid: str, timestamp: int, typeid: int) -> tuple:
        '''
        @brief 获取文档id的映射id
        @param id: 原始的docid
        @param timestamp: doc时间戳
        @param idx: 建库索引
        @param iddOld[OUT]: 返回之前的映射id
        @return 唯一id
        '''
        idCntKey = self.getBuildIdCounterKey(typeid)
        docId = self.getBuildIdMappingKey(docid, typeid)
        ids = []

        ids = self.r.eval(self.getgetMappingDocIdLua(), 0,
                          idCntKey, docId, str(timestamp))
        iddOld = ids[0]
        iddNew = ids[1]

        return (iddOld, iddNew)

    def getRemoveDocidKey(self, typeid: int) -> str:
        '''
        @brief 获取屏蔽docid的key
        @param[in] typeid: 库索引号
        @return key
        '''
        return 'acme-algorithm-{}:bs-remove-mapping:{}:docids'.format(self.env, typeid)

    def getRemoveDictTimestampKey(self, typeid: int) -> str:
        '''
        @brief 获取屏蔽词典时间戳的redis存储key
        @param[in] typeid: 库索引号
        @return key
        '''
        return 'acme-algorithm-{}:bs-remove-mapping:{}:timestamp'.format(self.env, typeid)

    def addRemoveDocid(self, docid: int, typeid: int) -> int:
        '''
        @brief 增加屏蔽docid
        @param docid: doc建库唯一数字id
        @param typeid: 库索引号
        @return 唯一id
        '''
        key = self.getRemoveDocidKey(typeid)
        ret = self.r.sadd(key, docid)
        self.r.expire(key, 60*60*24*7)
        return ret

    def cleanRemoveDocids(self, typeid: int) -> int:
        '''
        @brief 增加屏蔽docid
        @param typeid: 库索引号
        @return 唯一id
        '''
        key = self.getRemoveDocidKey(typeid)
        ret = self.r.delete(key)
        return ret
