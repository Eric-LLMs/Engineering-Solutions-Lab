import json

from fastapi.param_functions import Query
from pydantic.main import BaseModel
from app import app
from app.common import PerformanceTimer, AppException, AppRtnCode
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.builder import router
from app.views.builder.patient.impl import notify_patient
from fastapi import Depends, Request
from pydantic import Schema


def do_reset(common: AppRequest, idx: int, timeout: int) -> AppResponse:
    response = AppResponse()
    ret = requestScheduler('redis', 'reset', idx)
    if not ret:
        raise AppException(msg='call requestScheduler(\'redis\', \'reset\', {}) failed!'.format(idx), rtncode=AppRtnCode.ERROR)

    return response


@router.get('/reset/v1', response_model=AppResponse)
async def reset(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    idx: int = Query(..., description='索引类型'),
):
    '''
    重置索引
    '''
    app.logger.debug(request.query_params)
    timer = PerformanceTimer()
    with timer:
        response = do_reset(common=common, idx=idx, timeout=app.config['build']['reset']['timeout'])

    app.logger.debug('request builder.reset takes {} ms'.format(
        timer.read_millisecond()))

    return response
