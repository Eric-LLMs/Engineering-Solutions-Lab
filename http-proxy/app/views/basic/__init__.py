from app.views import RouteWithLog
from fastapi import APIRouter

router = APIRouter(route_class=RouteWithLog)

# ping
from app.views.basic import ping
# reload
from app.views.basic import reload
