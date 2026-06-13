from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def test():
    return {"status": "ok"}