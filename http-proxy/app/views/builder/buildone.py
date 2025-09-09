import json
import sys
import time

from fastapi.param_functions import Query
from fastapi import Body
from pydantic.main import BaseModel
from app import app
from app.common import PerformanceTimer, AppRtnCode
from app.scheduler import requestScheduler, requestScheduler2D
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.builder import router
from app.views.builder.patient.builder import DateEncoder
from fastapi import Depends, Request
from pydantic import Schema


def do_buildone(common: AppRequest, layer: int, commands: int, doc: dict, timeout: int) -> AppResponse:
    response = AppResponse()
    typeid = doc['typeid']
    docid = doc['docid']
    timestamp = doc['timestamp']

    iddOld, iddNew = requestScheduler(
        'redis', 'getMappingDocId', docid, timestamp, typeid)

    if iddNew == 0:
        app.logger.debug(
            'refused to build doc id {} to index {}'.format(docid, typeid))
    elif iddNew == sys.maxsize:
        app.logger.debug(
            'failed to get mapping doc id of doc id {} to index {}'.format(docid, typeid))
        raise AppException('failed to get mapping doc id of doc id {} to index {}'.format(docid, typeid), rtncode=AppRtnCode.ERROR)

    if iddOld == 0:
        app.logger.debug('doc id {} got global idd {}'.format(docid, iddNew))
    else:
        app.logger.debug(
            'doc id {} got global idd from {} to {}'.format(docid, iddOld, iddNew))

    # layer运算
    if iddNew > 0 and layer == -1:
        layer = iddNew % app.schedulers.get('bs', None).getRowsCount()

    while(True):
        # 屏蔽旧数据
        if iddOld > 0:
            # 屏蔽词典
            ret = requestScheduler('redis', 'addRemoveDocid', iddOld, typeid)
            if ret == None or ret <= 0:
                app.logger.warn('upload remove docid {} to redis failed!'.format(iddOld))

            for idx in range(app.schedulers.get('bs', None).getRowsCount()):
                bs_res, bs_req = requestScheduler2D(
                    'bs', 'remove', idx, common, idx, commands, typeid, iddOld, timeout)
                if bs_res.code != 0:
                    app.logger.warn('failed to remove doc id {} from index {}! request is \"{}\"'.format(
                        iddOld, idx, bs_req))
                else:
                    app.logger.debug(
                        'remove doc id {} from index {}'.format(iddOld, idx))
        # 没有需要建库的内容
        if doc["segnum"] <= 0:
            # remove不管返回结果，跑完就完了。
            break

        if iddNew <= 0:
            break

        # 修改doc
        doc['docid'] = iddNew

        final = 0
        for idx in range(app.schedulers.get('bs', None).getRowsCount()):
            if layer == idx:
                doc_json = json.dumps(doc, cls=DateEncoder, ensure_ascii=False)
                bs_res, bs_req = requestScheduler2D(
                    'bs', 'build', idx, common, idx, commands, typeid, iddNew, doc_json, timeout)
                if bs_res.code != 0:
                    app.logger.warn('failed to build doc id {} ({}) to index {}, layer {}'.format(
                        docid, iddNew, idx, layer))
                else:
                    final = 1
                    app.logger.debug('succeed to build doc id {} ({}) to index {}, layer {}'.format(
                        docid, iddNew, idx, layer))
        if final == 1:
            break

        layer = (layer + 1) % app.schedulers.get('bs', None).getRowsCount()
        time.sleep(1)
        #break

    return response


@router.post('/one/v1', response_model=AppResponse)
async def buildone(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    layer: int = Query(-1, description='集群layer'),
    commands: int = Query(3, description='命令行id：1-仅搜索 2-仅摘要 3-搜索摘要'),
    doc: dict = Body(...),
):
    '''
    单条数据建库结果
    '''
    #app.logger.debug(json.dumps(data, cls=DateEncoder, ensure_ascii=False))
    timer = PerformanceTimer()
    with timer:
        response = AppResponse()
        error_info = ""
        while True:
            # 校验commands
            if commands > 3 or commands < 0:
                error_info = 'wrong commands:{}'.format(commands)
                break

            # 校验layer
            scheduler = app.schedulers.get('bs', None)
            if layer >= scheduler.getRowsCount() or (layer < 0 and layer != -1):
                app.logger.warn(
                    'the layer {} [range:0-{}] does not exist, automatic redistribution!'.format(layer, scheduler.getRowsCount()))
                layer = -1

            # 校验typeid
            if 'typeid' not in doc:
                error_info = 'no typeid in build doc'
                break

            # 校验timestamp
            if 'timestamp' not in doc:
                error_info = 'no timestamp in build doc'
                break

            # 校验docid
            if 'docid' not in doc:
                error_info = 'no docid in build doc'
                break

            if len(doc) <= 0:
                error_info = 'empty build doc!'
            else:
                response = do_buildone(
                    common=common, layer=layer, commands=commands, doc=doc, timeout=app.config['build']['buildone']['timeout'])
            break

        if (len(error_info) > 0):
            raise Exception(error_info)

    app.logger.debug('request builder.buildone takes {} ms'.format(
        timer.read_millisecond()))

    return response
