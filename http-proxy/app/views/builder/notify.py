import json

from fastapi.param_functions import Query
from pydantic.main import BaseModel
from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.builder import router
from app.views.builder.patient.impl import notify_patient
from fastapi import Depends, Request
from pydantic import Schema


class NotifyRequest(BaseModel):
    typeid: int = Schema(..., description='数据类型：8-患者(仅支持)')
    docid: str = Schema(..., description='全局唯一id')
    commands: int = Schema(3, description='命令行id：1-搜索建库 2-摘要建库 3-搜索摘要建库')


@router.post('/notify/v1', response_model=AppResponse)
async def notify(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    body: NotifyRequest,
):
    '''
    实时流数据修改建库通知
    '''
    app.logger.debug(body)
    timeout = app.config['build']['notify']['timeout']
    timer = PerformanceTimer()
    with timer:
        response = AppResponse()
        error_info = ""
        while True:
            typeid = body.typeid
            docid = body.docid
            commands = body.commands

            #校验typeid
            if (typeid != 8):
                error_info = 'wrong typeid:{}'.format(typeid)
                break

            # 计算建库数据、发送到http-proxy
            doc_json = notify_patient(typeid, docid, commands, timeout)
            if (len(doc_json) <= 0):
                error_info = 'doc is empty'
                break

            # 载入返回doc、校验时间戳
            doc = json.loads(doc_json)
            if ("timestamp" not in doc.keys()):
                error_info = 'no timestamp'
                break

            # doc存入redis
            timestamp = int(doc["timestamp"])
            ret = requestScheduler('redis', 'setNotifyIdxDoc', typeid, timestamp, doc_json)
            if (ret < 0):
                error_info = 'failed to save redis data: {}:{}'.format(timestamp, doc_json)
                break
            break

        if (len(error_info) > 0):
            raise Exception(error_info)

    app.logger.debug('request builder.notify takes {} ms'.format(
        timer.read_millisecond()))

    return response
