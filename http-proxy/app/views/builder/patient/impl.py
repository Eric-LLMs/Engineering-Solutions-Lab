# 患者管理数据建库

import json
from retrying import retry
from app import app

from .builder import DataBuilderMain
from app.views.builder.buildone import do_buildone
from app.views import AppRequest


def notify_patient(typeid: int, docid: str, commands, timeout: int):
    '''
    根据docid构建文档
    @param[in] docid: 建库文档id
    '''
    if typeid != 8:
        app.logger.warn("error typeid![%d]" % (typeid))
        return ""

    # 生成建库文档
    builder = DataBuilderMain(typeid, "patient", app.tables, app.config['env'])
    doc_json = str(builder.run(docid))
    # app.logger.debug(doc_json)

    # 发送建库HTTP服务请求
    doc_json = send_doc_to_build(doc_json, commands, timeout)

    return doc_json


def send_doc_to_build(doc_json: str, commands, timeout: int):
    # 发送建库HTTP服务请求
    '''
    for layer in app.proxy:
        ret = layer.build(doc_json, commands)
        if (ret < 0):
            return ""
    '''
    doc = json.loads(doc_json)
    do_buildone(common=AppRequest(),layer=-1,commands=commands,doc=doc, timeout=timeout)

    return doc_json
