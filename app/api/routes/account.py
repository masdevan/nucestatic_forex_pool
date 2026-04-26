from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("")
async def get_account_info() -> Dict[str, Any]:
    from app.api.controllers.account_controller import get_account
    return get_account()