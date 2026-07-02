from fastapi import APIRouter

from src.api.dependencies import UserVerifiedDep, AdminVerifiedDep

router = APIRouter()


@router.get("/health")
async def test():
    return {"status": "ok"}

@router.get("/check_register")
async def check_register(user_id: UserVerifiedDep):
    return {"status": "ok"}

@router.get("/check_admin_privileges")
async def check_admin_privileges(user_id: AdminVerifiedDep):
    return {"status": "ok"}

@router.get("/can_register")
async def can_register():
    return {
        "status": "ok",
        "can_register": True
    }