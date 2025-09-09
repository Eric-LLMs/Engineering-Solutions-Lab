# -*- coding: utf-8 -*-
"""
@File: lcasearch.py
@Author:
@Time: 12月 17, 2020
"""

from fastapi.param_functions import Query
from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.lca import router
from fastapi import Depends, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, List
import json

class QueryInfo(BaseModel):
    question: str=Field(None, description='取得的相似问题')
    answer: str=Field(None, description='相似问题答案')
    simquery: Dict[str, Any]=Field(None, description='相似问及输入query的相似分数')


class LCASearchResponse(AppResponse):
    # res: int=Schema(..., description='预测结果：0 - 无效，1 - 有效')
    queries: List[QueryInfo] = Field(..., description='结构化文本数据结果')

class LCASearchRequest(BaseModel):
    '''新增相似查询请求包'''
    knowledge_base: str = Query(None, description='文本知识库类型')
    query: str = Query(..., description='需要聚类的query列表')
    threshold: float = Query(..., description='过滤相似query的阈值')


@router.post('/lcasearch/v1', response_model=LCASearchResponse)
async def lcasearch(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    body: LCASearchRequest

):
    res = dict(body)
    query = res['query']
    knowledge_base = res['knowledge_base']
    threshold = res['threshold']
    '''评论有效性预测接口，不支持回调请求'''
    response = lcasearch_sync(common, knowledge_base, query, threshold)

    return response

def lcasearch_sync(
    common: AppRequest,
    knowledge_base: str,
    query: str,
    threshold: float
):
    '''lcasearch同步接口'''
    timer = PerformanceTimer()
    with timer:
        response = requestScheduler(app.schedulers.lca, 'lcasearch', common, knowledge_base, query, threshold, app.config['lca']['lcasearch']['timeout'])
        if response is None:
            raise AppException('failed to get response from lca.lcasearch')
        else:
            response, request = response
    app.logger.debug('request lca.lcasearch takes {} ms'.format(timer.read_millisecond()))
    res = []
    for item in response.comment_analyzer_response_content:
        item_info = item.replace('{', '').replace('}', '').split(',')
        item_dic = {}
        for info in item_info:
            k = str(info.split(':')[0]).strip()
            v = info.split(':')[1]
            item_dic[k] = v
        res.append(QueryInfo(question=item_dic['question'], answer=item_dic['answer'], score=float(item_dic['score'])))

    return LCASearchResponse(
        # res=response.rtn,
        queries=res
    )
