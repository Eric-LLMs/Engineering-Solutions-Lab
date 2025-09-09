import json
import sys

from fastapi.param_functions import Query
from pydantic.main import BaseModel
from app import app
from app.common import PerformanceTimer, AppRtnCode
from app.scheduler import requestScheduler, requestScheduler2D
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.builder import router
from app.views.builder.patient.impl import notify_patient
from fastapi import Depends, Request
from pydantic import Schema


def do_clean(common: AppRequest, typeid: int, layer: int, commands: int, timeout: int) -> AppResponse:
    # 校验typeid
    if typeid <= 0:
        app.logger.warn('failed to get typeid [{}] from request params'.format(typeid))
        raise AppException(msg='failed to get typeid [{}] from request params'.format(typeid), rtncode=AppRtnCode.ERROR)
    # 校验layer
    scheduler = app.schedulers.get('bs', None)
    if layer >= scheduler.getRowsCount() or (layer < 0 and layer != -1):
        app.logger.warn(
            'invalid layer value [{}][range:0-{}] from request params'.format(layer, scheduler.getRowsCount()))
        raise AppException(msg='invalid layer value [{}][range:0-{}] from request params'.format(layer, scheduler.getRowsCount()), rtncode=AppRtnCode.ERROR)
    # 清空redis屏蔽docids
    #requestScheduler('redis', 'cleanRemoveDocids', typeid)

    if (layer == -1):
        # 全部层
        for idx in range(app.schedulers.get('bs', None).getRowsCount()):
            bs_res, bs_req = requestScheduler2D(
                'bs', 'clean', idx, common, idx, commands, typeid, timeout)
            if bs_res.code != 0:
                app.logger.warn('failed to clean typeid {} from index {}! request is \"{}\"'.format(
                    typeid, idx, bs_req))
                raise AppException(msg='failed to clean typeid {} from index {}! request is \"{}\"'.format(
                    typeid, idx, bs_req), rtncode=AppRtnCode.ERROR)
            else:
                app.logger.debug(
                    'clean typeid {} from index {}'.format(typeid, idx))
    else:
        # 指定层
        for idx in range(app.schedulers.get('bs', None).getRowsCount()):
            if idx == layer:
                bs_res, bs_req = requestScheduler2D(
                    'bs', 'clean', idx, common, idx, commands, typeid, timeout)
                if bs_res.code != 0:
                    app.logger.warn('failed to clean typeid {} from index {}! request is \"{}\"'.format(
                        typeid, idx, bs_req))
                    raise AppException(msg='failed to clean typeid {} from index {}! request is \"{}\"'.format(
                        typeid, idx, bs_req), rtncode=AppRtnCode.ERROR)
                else:
                    app.logger.debug(
                        'clean typeid {} from index {}'.format(typeid, idx))
                    break

    return AppResponse()


@router.get('/clean/v1', response_model=AppResponse)
async def clean(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    idx: int = Query(..., description='索引类型'),
    layer: int = Query(-1, description='集群layer'),
    commands: int = Query(3, description='命令行id：1-仅搜索 2-仅摘要 3-搜索摘要'),
):
    '''
    清索引
    '''
    app.logger.debug(request.query_params)
    timer = PerformanceTimer()
    with timer:
        response = do_clean(common=common, typeid=idx,
                            layer=layer, commands=commands, timeout=app.config['build']['clean']['timeout'])

    app.logger.debug('request builder.clean takes {} ms'.format(
        timer.read_millisecond()))

    return response
