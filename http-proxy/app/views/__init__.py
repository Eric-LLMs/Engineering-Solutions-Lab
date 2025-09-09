from app import app
from app.common import PerformanceTimer, AppException, AppRtnCode
from fastapi import Request, Response, Query
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, Schema, AnyHttpUrl
from starlette.responses import JSONResponse
from typing import Callable, List

import traceback

class AppRequest(BaseModel):
    '''基本请求包'''
    source: str = Schema(None, description='用于标记请求来源，以便日志/监控分析。建议填写请求模块名，或模块名-版本号')  # 请求来源
    logid: str = Schema(None, description='请求唯一 ID')    # logid
    debug: bool = Schema(False, description='调试模式，正常情况下，请勿使用该参数') # 调试模式
    appid: int = Schema(0, description='应用场景ID')    # 场景id
    callback: AnyHttpUrl = Schema(None, description='回调接口，如果指定该参数，则接口将通过异步方式 POST 该回调地址')   # 回调url

async def parse_app_request(
    source: str = Query(None, description='用于标记请求来源，以便日志/监控分析。建议填写请求模块名，或模块名-版本号'),
    logid: str = Query(None, description='请求唯一 ID'),
    debug: bool = Query(False, description='调试模式，正常情况下，请勿使用该参数'),
    appid: int = Query(0, description='应用场景ID'),
    callback: AnyHttpUrl = Query(None, description='如果接口支持回调，且指定该参数，则接口将通过异步方式 POST 该回调地址'),
) -> AppRequest:
    '''解析 app request 参数'''
    return AppRequest(
        source=source,
        logid=logid,
        debug=debug,
        appid=appid,
        callback=callback,
    )

class AppResponse(BaseModel):
    '''基本响应包'''
    code: AppRtnCode = Schema(AppRtnCode.OK, description='返回码，0 标识成功')    # 返回码
    message: str = Schema('', description='消息描述，一般用于描述错误信息') # 消息
    sample_ids: List[int] = Schema([], description='算法实验采样 ID 列表', example=[1001, 2059, 2580])

# application fastapi responses 定义
APP_FASTAPI_RESPONSES = {
    422: {
        "model": AppResponse,
        "content": {
            'application/json': {
                'example':  AppResponse(
                    code=AppRtnCode.VALIDATION_ERROR,
                    message='错误信息/调试堆栈信息',
                ).dict(),
            }
        }
    }
}

class RouteWithLog(APIRoute):
    '''自定义路由，提供日志输出'''
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            timer = PerformanceTimer()
            rtn = 0

            app.logger.debug('got request: {} {}'.format(request.method, request.scope['path']))

            try:
                with timer:
                    response = None
                    try:
                        response: Response = await original_route_handler(request)
                    except Exception as exc:
                        app.logger.error(traceback.format_exc())
                        rtn = AppRtnCode.ERROR
                        if isinstance(exc, RequestValidationError): rtn = AppRtnCode.VALIDATION_ERROR
                        elif isinstance(exc, AppException): rtn = exc.rtncode

                        response = JSONResponse(AppResponse(
                            code = rtn,
                            message = str(exc),
                        ).dict())

                    return response
            except Exception as exc:
                rtn = AppRtnCode.ERROR
                app.logger.error(traceback.format_exc())
                response = JSONResponse(AppResponse(
                    code = rtn,
                    message = str(exc),
                ).dict())

                return response
            finally:
                if request.method in ['GET', 'POST']:
                    # 根据参数构建日志信息
                    extraLog = ' '.join([ '{}={}'.format(k, v.replace('\n', ' ')) for k, v in request.query_params.items() if k not in ['source', 'logid'] ])

                    app.logger.info('HTTP-PROXY api={} method={} source={} logid={} tm={} rt={} status={} ip={} ua={} sz={} {}'.format(
                        request.scope['path'],
                        request.method,
                        request.query_params.get('source', '-'),
                        request.query_params.get('logid', '-'),
                        timer.read_microsecond(),
                        rtn,
                        response.status_code,
                        request.client.host,
                        request.headers.get('user-agent', '-'),
                        response.headers['content-length'],
                        extraLog,
                    ))

        return custom_route_handler

# 基础接口
from app.views import basic
# urs 接口
from app.views import urs
# 评论模型接口
from app.views import ct
# 搜索建库接口
from app.views import builder
# 用户端文本分析
from app.views import lca

# 基础接口
app.include_router(basic.router)
# urs 接口
app.include_router(urs.router, prefix='/urs', tags=['URS'], responses=APP_FASTAPI_RESPONSES)
app.include_router(urs.ocr.ocr_callback_router, tags=['CALLBACK-PLACEHOLDER'])
# ct 接口
app.include_router(ct.router, prefix='/ct', tags=['COMMENT'], responses=APP_FASTAPI_RESPONSES)
# build 接口
app.include_router(builder.router, prefix='/build', tags=['BUILD'],)
# lca 接口
app.include_router(lca.router, prefix='/lca', tags=['LCA'], responses=APP_FASTAPI_RESPONSES)