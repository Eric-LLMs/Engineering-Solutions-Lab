from app.views import RouteWithLog
from fastapi import APIRouter

router = APIRouter(route_class=RouteWithLog)

# 评论预测接口
from app.views.ct import predict
