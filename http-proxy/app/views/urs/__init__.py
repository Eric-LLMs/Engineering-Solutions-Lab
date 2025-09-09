from app import app
from app.views import RouteWithLog
from fastapi import APIRouter

import oss2

router = APIRouter(route_class=RouteWithLog)

# oss bucket
oss_bucket = None

if 'oss' in app.config and app.config['oss']:
    auth = oss2.Auth(app.config['oss']['ak'], app.config['oss']['sk'])
    oss_bucket = oss2.Bucket(auth, app.config['oss']['url'], app.config['oss']['bucket'])

    app.logger.info('oss client initialized')

# 推荐接口
from app.views.urs import ocr
from app.views.urs import mit
from app.views.urs import distiller
