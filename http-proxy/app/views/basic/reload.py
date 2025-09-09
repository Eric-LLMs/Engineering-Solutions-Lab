from app import app
from app.config import loadServiceConfig
from app.views import AppResponse, AppRtnCode
from app.views.basic import router

import traceback

@router.get('/reload', response_model=AppResponse)
async def reload():
    '''
    reload 配置
    '''
    try:
        config = loadServiceConfig()
        app.config = config
    except Exception as ex:
        app.logger.error('failed to reload config: {}'.format(ex))
        return AppResponse(
            rtncode=AppRtnCode.ERROR,
            message=traceback.format_exc(),
            )
    else:
        app.logger.debug('succeed to reload config')
        return AppResponse()
