# -*- coding: utf-8 -*-
"""
@File: cluster.py
@Author:
@Time: 12月 25, 2020
"""

from fastapi.param_functions import Query
from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.lca import router, oss_bucket
from datetime import date
from fastapi.responses import JSONResponse
from google.protobuf.json_format import MessageToDict
from fastapi import APIRouter, Depends, Request, File, UploadFile
from pydantic import BaseModel, Field
from typing import Any, Dict, List
from retrying import retry

import os
import uuid
import hashlib
import json
import requests
import xlrd, xlwt


from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo
import oss2

oss_dict = {
    'endpoint': ' ',
    'bucket': ' ',
    'fakeAccessKey_ID': ' ',
    'SECRET': ' '
}


class QueryInfo(BaseModel):
    group_id: str = Field(None, description='组别id')
    item_amount: float = Field(None, description='文本数（去重后）')
    items: list = Field(None, description='相似问列表')


class LCAClusterResponse(AppResponse):
    # res: int=Schema(..., description='预测结果：0 - 无效，1 - 有效')
    res: List[QueryInfo] = Field(..., description='结构化文本数据结果')
    filename: str = Field(None, description='临时文件名称')


class LCAClusterCallbackRequest(LCAClusterResponse):
    '''cluster回调请求包'''
    request: AppRequest=Field(..., description='原始请求信息')

# cluster callback router
cluster_callback_router = APIRouter(default_response_class=JSONResponse)
@cluster_callback_router.post(
    "{$callback}",
)
def lcacluster_callback(body: LCAClusterCallbackRequest):
    '''cluster回调接口'''
    pass

@router.post('/cluster/v1', response_model=LCAClusterResponse, callbacks=cluster_callback_router.routes)
async def cluster(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    data: UploadFile = File(..., description='文件二进制流'),
):
    '''excel文件接口，支持回调请求'''
    content = await data.read()
    try:
        filename = str(uuid.uuid1()).replace('-', '')[0:15]
        res = []
        prefix = 'http://{}.{}/{}/{}'.format(oss_dict['bucket'], oss_dict['endpoint'], 'knowledge_v1/nlp_query_cluster',
                                             date.today().strftime('%Y/%m/%d'))
        url = '{}/{}.xls'.format(prefix, filename)
        app.thread_pool.submit(cluster_sync, content, common, filename)
        # cluster_sync(content, common, filename)
        return LCAClusterResponse(
            res=res,
            filename=url,
        )
    except Exception as e:
        app.logger.debug('the clustering file path: {}'.format(e))
        raise e

def cluster_sync(
    data: bytes,
    common: AppRequest,
    filename,
):
    '''cluster同步接口'''
    timer = PerformanceTimer()
    with timer:
        queries=[]
        workbook = xlrd.open_workbook(file_contents=data)
        sheet_names = workbook.sheet_names()  # 返回表格中所有工作表的名字
        worksheet = workbook.sheet_by_name(sheet_names[0])
        rows_cnt = worksheet.nrows  # 总行数
        for i in range(rows_cnt):
            rowdate = worksheet.row_values(i)
            query = str(rowdate[0]).replace('\r', '').replace('\n', '')
            queries.append(query)

        response = requestScheduler(app.schedulers.lca, 'cluster', common, filename, queries,  app.config['lca']['cluster']['timeout'])
        if response is None:
            raise AppException('failed to get response from cluster')
        else:
            response, request = response

    app.logger.debug('request lca.cluster takes {} ms'.format(timer.read_millisecond()))
    res = []
    for item in response.comment_clustering_response_content:
        item = item.replace('\', \'', '##').replace('\'', '').replace('{', '').replace('}', '')
        item_info = item.split(',')
        item_dic = {}
        sim_items = []
        for info in item_info:
            if 'group_id' in info or 'item_amount' in info or 'items' in info:
                k = str(info.split(':')[0]).strip()
                v = info.split(':')[1]
                item_dic[k] = v
                if k == 'items':
                    sim_items = item_dic[k].split('##')
            else:
                sim_items.append(info)

        res.append(QueryInfo(group_id=item_dic['group_id'], item_amount=item_dic['item_amount'], items=sim_items))

    # app.logger.debug('cluster data md5 checksum: {}'.format(filename))
    # 异步上传文件至oss
    # app.thread_pool.submit(uploadDataToOss, data, request, response, timer.read_millisecond())

    prefix = 'http://{}.{}/{}/{}'.format(oss_dict['bucket'], oss_dict['endpoint'], 'knowledge_v1/nlp_query_cluster',
                                  date.today().strftime('%Y/%m/%d'))
    url = '{}/{}.xls'.format(prefix, filename)

    dir = os.path.dirname(__file__)
    filename = '{}/{}.xls'.format(os.path.join(dir, 'temp'), filename)
    app.logger.debug('the clustering file path: {}'.format(filename))
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('groups', cell_overwrite_ok=True)
    worksheet.write(0, 0, 'group_id')
    worksheet.write(0, 1, 'item_amount')
    worksheet.write(0, 2, 'items')
    for i, res_item in enumerate(res):
        print(res_item.group_id, res_item.item_amount, res_item.items)
        worksheet.write(i + 1, 0, res_item.group_id)
        worksheet.write(i + 1, 1, res_item.item_amount)
        worksheet.write(i + 1, 2, res_item.items)
    workbook.save(filename)

    # app.thread_pool.submit(upload_oss, filename)
    upload_oss(filename)
    return LCAClusterResponse(
        res=res if res else None,
        filename=url,
    )

def cluster_async(
    request: Request,
    common: AppRequest,
    data: bytes,
):
    '''
    mit异步回调接口
    '''
    if not common.callback: return

    app.logger.debug('cluster async start')
    sync_response = cluster_sync(data, common)
    app.logger.debug('cluster async done')

    callback_request = LCAClusterCallbackRequest(
        request=request,
        **sync_response.dict(),
    )

    # post
    response = requests.post(common.callback, data=callback_request.dict())

    if response.ok:
        app.logger.debug('cluster async callback {} succeed'.format(common.callback))
    else:
        app.logger.error('cluster async callback {} failed, status code = {}'.format(common.callback, response.status_code))

@retry(stop_max_attempt_number=3)
def uploadDataToOss(data: bytes, request: Any, response: Any, tm: int):
    '''
    上传相关数据到oss
    @param data: excel文件
    @param request: cluster请求包
    @param response: cluster响应包
    @param tm: cluster请求耗时
    '''
    if not oss_bucket: return

    md5sum = hashlib.md5(data).hexdigest()
    app.logger.debug('cluster data md5 checksum: {}'.format(md5sum))
    prefix = '{}/{}/{}/{}'.format(app.config['oss']['prefix'], 'knowledge_v1/nlp_query_cluster', date.today().strftime('%Y/%m/%d'), md5sum)
    upload_fname = '{}'.format(prefix)
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

@retry(stop_max_attempt_number=3)
def upload_oss(filename):
    print('upload_oss %s' % filename)
    bucket = None
    try:
        bucket = app.oss.stub
    except:
        auth = oss2.Auth(oss_dict['AccessKey_ID'], oss_dict['SECRET'])
        bucket = oss2.Bucket(auth, oss_dict['endpoint'], oss_dict['bucket'])

    key = '{}/{}/{}'.format('knowledge_v1/nlp_query_cluster', date.today().strftime('%Y/%m/%d'), filename.split('/')[-1])

    total_size = os.path.getsize(filename)
    part_size = determine_part_size(total_size, preferred_size=100 * 1024)

    upload_id = bucket.init_multipart_upload(key).upload_id

    parts = []

    with open(filename, 'rb') as fileobj:
        part_number = 1
        offset = 0
        while offset < total_size:
            num_to_upload = min(part_size, total_size - offset)
            result = bucket.upload_part(key, upload_id, part_number,
                                        SizedFileAdapter(fileobj, num_to_upload))
            parts.append(PartInfo(part_number, result.etag))

            offset += num_to_upload
            part_number += 1

    bucket.complete_multipart_upload(key, upload_id, parts)

    with open(filename, 'rb') as fileobj:
        assert bucket.get_object(key).read() == fileobj.read()

    url = bucket.sign_url('GET', key, 60 * 60)

    if os.path.isfile(filename):
        os.remove(filename)

    return url