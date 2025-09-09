from fastapi.param_functions import Query
from app import app
from app.common import PerformanceTimer
from app.scheduler import requestScheduler
from app.views import AppException, AppRequest, AppResponse, parse_app_request
from app.views.ct import router
from fastapi import Depends, Request
from pydantic import Schema

class PredictResponse(AppResponse):
    res: int=Schema(..., description='预测结果：0 - 无效，1 - 有效')
    prob: float=Schema(..., description='预测结果的概率值')

@router.get('/predict/v1', response_model=PredictResponse)
async def predict(
    request: Request,
    *,
    common: AppRequest = Depends(parse_app_request),
    sentence: str = Query(..., description='需要进行预测的句子'),
):
    '''评论有效性预测接口，不支持回调请求'''
    response = predict_sync(sentence, common)

    return response

def predict_sync(
    sentence: str,
    common: AppRequest,
):
    '''predict同步接口'''
    timer = PerformanceTimer()
    with timer:
        response = requestScheduler(app.schedulers.ct, 'predict', sentence, common, app.config['ct']['predict']['timeout'])
        if response is None:
            raise AppException('failed to get response from ct')
        else:
            response, request = response

    app.logger.debug('request ct.predict takes {} ms'.format(timer.read_millisecond()))
    return PredictResponse(
        res=response.res,
        prob=response.prob,
    )
