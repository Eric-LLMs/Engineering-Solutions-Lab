from app import app
from app.views import AppResponse
from app.views.basic import router

@router.get('/ping', response_model=AppResponse)
@router.head('/ping')
async def ping():
    '''
    ping
    '''
    app.logger.debug('pong')

    return AppResponse()
