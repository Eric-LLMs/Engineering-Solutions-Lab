from fastapi.param_functions import Query
from pydantic.main import BaseModel
from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.urs import router
from fastapi import Depends, Request
from pydantic import Schema
from typing import Any, Dict, List

import json

class DistillerResponse(AppResponse):
    extracts: List[Any]=Schema(None, description='结构化文本数据结果', example=[{
        'name': '住址',
        'original_name': '住址',
        'value': '北京市朝阳区光华路soho',
        'confidence': 1.0,
    }])
    meta: Dict[str, Any]=Schema(None, description='识别出来的元信息', example={
        'content_type': '身份证'
        })
    debug: Dict[str, Any]=Schema(None, description='返回的调试信息', example={
        'key': 'value',
    })

class DistillerRequest(BaseModel):
    data: str = Schema(..., description='需要进行结构化提取的文本')
    content_type: str = Schema('身份证', description='文本内容类型：病例报告/大病例/身份证/社保卡/...')

@router.post('/distiller/v1', response_model=DistillerResponse)
async def distiller(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    body: DistillerRequest,
):
    '''字符串结构化提取接口，不支持回调请求'''
    response = distiller_sync(body.data, body.content_type, common)

    return response

def distiller_sync(
    data: str,
    content_type: str,
    common: AppRequest,
):
    '''distiller同步接口'''
    timer = PerformanceTimer()
    with timer:
        response = requestScheduler(app.schedulers.urs, 'distiller', data, content_type, common, app.config['urs']['distiller']['timeout'])
        if response is None:
            raise AppException('failed to get response from urs')
        else:
            response, request = response

    app.logger.debug('request urs.distiller takes {} ms'.format(timer.read_millisecond()))
    return DistillerResponse(
        extracts=json.loads(response.extracts) if response.extracts else None,
        meta=json.loads(response.meta) if response.meta else None,
        debug=json.loads(response.rtn.debug) if response.rtn.debug else None,
    )
