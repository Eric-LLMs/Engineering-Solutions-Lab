from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.urs import router, oss_bucket
from datetime import date
from fastapi import APIRouter, Depends, Form, Request, File, UploadFile
from fastapi.responses import JSONResponse
from google.protobuf.json_format import MessageToDict
from pydantic import Schema
from retrying import retry
from typing import Any, Dict, List

import hashlib
import json
import requests

class OcrResponse(AppResponse):
    extracts: List[Any]=Schema(None, description='结构化文本数据结果', example=[{
        'name': '住址',
        'original_name': '住址',
        'value': '北京市朝阳区光华路soho',
        'confidence': 1.0,
    }])
    meta: Dict[str, Any]=Schema(None, description='识别出来的元信息', example={
        'content_type': '影像'
        })
    debug: Dict[str, Any]=Schema(None, description='返回的调试信息', example={
        'key': 'value',
    })

class OcrCallbackRequest(OcrResponse):
    '''ocr回调请求包'''
    request: AppRequest=Schema(..., description='原始请求信息')

# ocr callback router
ocr_callback_router = APIRouter(default_response_class=JSONResponse)

@ocr_callback_router.post(
    "{$callback}",
)
def ocr_callback(body: OcrCallbackRequest):
    '''ocr回调接口'''
    pass

@router.post('/ocr/v1', response_model=OcrResponse, callbacks=ocr_callback_router.routes)
async def ocr(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    data: UploadFile = File(..., description='图片二进制流'),
    params: str = Form(..., description='请求参数字符串，json格式', example=json.dumps({
        'content_type': '影像'
        }, ensure_ascii=False))
):
    '''OCR图像文本识别接口，支持回调请求'''
    content = await data.read()

    if common.callback: # 异步
        app.thread_pool.submit(ocr_async, request, common, content, params)

        return OcrResponse()
    else:
        response = ocr_sync(content, params, common)

        return response

def ocr_sync(
    data: bytes,
    params: str,
    common: AppRequest,
):
    '''ocr同步接口'''
    timer = PerformanceTimer()
    with timer:
        response = requestScheduler(app.schedulers.urs, 'ocr', data, params, common, app.config['urs']['ocr']['timeout'])
        if response is None:
            raise AppException('failed to get response from urs')
        else:
            response, request = response

    app.logger.debug('request urs.ocr takes {} ms'.format(timer.read_millisecond()))

    # 异步上传图片至oss
    app.thread_pool.submit(uploadDataToOss, data, request, response, timer.read_millisecond())

    return OcrResponse(
        extracts=json.loads(response.extracts) if response.extracts else None,
        meta=json.loads(response.meta) if response.meta else None,
        debug=json.loads(response.rtn.debug) if response.rtn.debug else None,
    )

def ocr_async(
    request: Request,
    common: AppRequest,
    data: bytes,
    params: str
):
    '''
    ocr异步回调接口
    '''
    if not common.callback: return

    app.logger.debug('ocr async start')
    sync_response = ocr_sync(data, params, common)
    app.logger.debug('ocr async done')

    callback_request = OcrCallbackRequest(
        request=request,
        **sync_response.dict(),
    )

    # post
    response = requests.post(common.callback, data=callback_request.dict())

    if response.ok:
        app.logger.debug('ocr async callback {} succeed'.format(common.callback))
    else:
        app.logger.error('ocr async callback {} failed, status code = {}'.format(common.callback, response.status_code))

@retry(stop_max_attempt_number=3)
def uploadDataToOss(data: bytes, request: Any, response: Any, tm: int):
    '''
    上传相关数据到oss
    @param data: 图片文件
    @param request: urs请求包
    @param response: urs响应包
    @param tm: urs请求耗时
    '''
    if not oss_bucket: return

    md5sum = hashlib.md5(data).hexdigest()
    app.logger.debug('ocr data md5 checksum: {}'.format(md5sum))
    prefix = '{}/{}/{}/{}'.format(app.config['oss']['prefix'], 'ocr', date.today().strftime('%Y/%m/%d'), md5sum)
    upload_fname = '{}.png'.format(prefix)
    upload_json_fname = '{}.json'.format(prefix)

    try:
        # 检查文件是否存在
        if not oss_bucket.object_exists(upload_fname):
            # 上传文件到oss
            oss_bucket.put_object(upload_fname, data)
            app.logger.debug('succeed to put oss, name={}, data size={} bytes'.format(upload_fname, len(data)))
        else:
            app.logger.debug('succeed to put oss (already), name={}, data size={} bytes'.format(upload_fname, len(data)))

        # 上传请求信息
        request.data = upload_fname.encode('utf-8') # 修改data字段，用oss中的地址替代原来的图片二进制流

        content = json.dumps({
            'request': MessageToDict(request, including_default_value_fields=True, preserving_proto_field_name=True, use_integers_for_enums=True),
            'response': MessageToDict(response, including_default_value_fields=True, preserving_proto_field_name=True, use_integers_for_enums=True),
            'tm': tm,
        }, ensure_ascii=False, indent=4)

        rtn=oss_bucket.put_object(upload_json_fname, content)
        app.logger.debug('succeed to put oss, name={}, data size={} bytes'.format(upload_json_fname, len(content)))
    except:
        app.logger.error('exception during put oss: {}'.format(traceback.format_exc()))
        raise
