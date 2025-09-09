from app.views import RouteWithLog
from fastapi import APIRouter

router = APIRouter(route_class=RouteWithLog)

# 实时流notify接口
from app.views.builder import notify
# 实时流回放接口
from app.views.builder import playback
# 单条数据建库接口
from app.views.builder import buildone
# 清库接口
from app.views.builder import clean
# id重置接口
from app.views.builder import reset