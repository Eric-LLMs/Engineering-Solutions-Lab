# -*- coding: utf-8 -*-
"""
@File: cluster_queries.py
@Author:
@Time: 1月 8, 2021
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

import uuid
import hashlib
import json
import requests
import xlrd

class QueryInfo(BaseModel):
    group_id: str = Field(None, description='组别id')
    item_amount: float = Field(None, description='文本数（去重后）')
    items: list = Field(None, description='相似问列表')


class LCAClusterResponse(AppResponse):
    res: List[QueryInfo] = Field(..., description='结构化文本数据结果')
    filename: str = Field(None, description='临时文件名称')


class LCAClusterCallbackRequest(LCAClusterResponse):
    '''cluster回调请求包'''
    request: AppRequest=Field(..., description='原始请求信息')

class ClusterCueriesRequest(BaseModel):
    '''新增聚类请求包'''
    queries: List[str] = Field(..., description='需要聚类的query列表', example=["坏死到什么程度不能做手术？？有标准","坏死到什么程度不能做手术？？有标准","现在服用激素可以手术好吗","服用激素可以手术吗"])
    knowledge_base: str = Field(None, description='文本知识库类型')

# cluster callback router
cluster_callback_router = APIRouter(default_response_class=JSONResponse)
@cluster_callback_router.post(
    "{$callback}",
)
def lcacluster_callback(body: LCAClusterCallbackRequest):
    '''cluster回调接口'''
    pass


@router.post('/cluster_queries/v1', response_model=LCAClusterResponse, callbacks=cluster_callback_router.routes)
async def cluster_queries(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    body: ClusterCueriesRequest
):
    res = dict(body)
    queries = res['queries']
    knowledge_base = res['knowledge_base']
    if common.callback: # 异步
        app.thread_pool.submit(cluster_queries_sync, common, queries, knowledge_base)
        return LCAClusterResponse()
    else:
        response = cluster_queries_sync(common, queries, knowledge_base)
        return response


def cluster_queries_sync(
    common: AppRequest,
    queries: List,
    knowledge_base: str
):
    '''cluster_queries同步接口'''
    timer = PerformanceTimer()
    filename = str(uuid.uuid1()).replace('-', '')[0:15]
    with timer:
        queries_temp = str(queries).replace('"', '').replace('\'', '').replace(' ', '').replace('[',
                                                                                                             '').replace(
            ']', '').replace('\r', '').replace('\n', '').split(',')
        queries = []
        for query in queries_temp:
            queries.append(query)

        response = requestScheduler(app.schedulers.lca, 'cluster', common, filename, queries,
                                    app.config['lca']['cluster']['timeout'])
        if response is None:
            raise AppException('failed to get response from cluster')
        else:
            response, request = response

    app.logger.debug('request lca.cluster_queries takes {} ms'.format(timer.read_millisecond()))
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

    return LCAClusterResponse(
        res=res if res else None,
        filename=filename,
    )
