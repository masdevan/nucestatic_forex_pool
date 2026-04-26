from fastapi import APIRouter

from app.api.routes.execution.market_structure import router as market_structure_router
from app.api.routes.execution.swing import router as swing_router

from app.api.routes.execution.risk_reward import router as risk_reward_router
from app.api.routes.execution.position import router as position_router
from app.api.routes.execution.time import router as time_router
from app.api.routes.execution.news import router as news_router
from app.api.routes.execution.calendar import router as calendar_router
from app.api.routes.execution.spread import router as spread_router
from app.api.routes.execution.accuracy import router as accuracy_router
from app.api.routes.execution.candle_speed import router as candle_speed_router
from app.api.routes.execution.total_loss_today import router as total_loss_today_router

router = APIRouter()

router.include_router(market_structure_router, prefix="", tags=["execution"])
router.include_router(swing_router, prefix="", tags=["execution"])
router.include_router(risk_reward_router, prefix="", tags=["execution"])
router.include_router(position_router, prefix="", tags=["execution"])
router.include_router(time_router, prefix="", tags=["execution"])
router.include_router(news_router, prefix="", tags=["execution"])
router.include_router(calendar_router, prefix="", tags=["execution"])
router.include_router(spread_router, prefix="", tags=["execution"])
router.include_router(accuracy_router, prefix="", tags=["execution"])
router.include_router(candle_speed_router, prefix="", tags=["execution"])
router.include_router(total_loss_today_router, prefix="", tags=["execution"])
