import json

from fastapi.param_functions import Query
from pydantic.main import BaseModel
from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.builder import router
from app.views.builder.patient.impl import send_doc_to_build
from fastapi import Depends, Request
from pydantic import Schema


@router.get('/playback/v1', response_model=AppResponse)
async def playback(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    typeid: int = Query(..., description='数据类型：8-患者(仅支持)'),
    btime: int = Query(..., description='开始时间'),
    etime: int = Query(..., description='结束时间'),
    commands: int = Query(3, description='命令行id：1-仅搜索 2-仅摘要 3-搜索摘要'),
):
    '''
    实时流数据回放
    '''
    app.logger.debug(request.query_params)
    timeout = app.config['build']['playback']['timeout']
    timer = PerformanceTimer()
    with timer:
        response = AppResponse()
        error_info = ""
        while True:
            # 校验commands
            if commands < 0 or commands > 3:
                error_info = 'wrong commands:{}'.format(commands)
                break

            # 校验时间戳
            if (etime - btime <= 0):
                error_info = 'start time is greater than end time!'
                break

            doc_list = requestScheduler(
                'redis', 'searchDocWithTimescope', typeid, btime, etime)
            app.logger.debug(
                'playback doc list count:{}'.format(len(doc_list)))
            for doc in doc_list:
                if (len(send_doc_to_build(doc, commands, timeout)) <= 0):
                    error_info = 'failed to playback:[{}]'.format(doc)
            break
        if (len(error_info) > 0):
            raise Exception(error_info)

    app.logger.debug('request builder.playback takes {} ms'.format(
        timer.read_millisecond()))

    return response
