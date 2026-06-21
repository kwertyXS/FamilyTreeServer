from fastapi import APIRouter, HTTPException
from src.schemas.family import *
from src.schemas.family import TreeSchemaOut
from src.services.family_service import get_tree_service, get_person_service, get_events_service, get_persons_service

router = APIRouter()


@router.get("/tree", response_model=TreeSchemaOut)
async def get_tree():
    """Полное дерево: все люди + связи для отрисовки на фронте."""
    return await get_tree_service()


@router.get("/persons")
async def get_persons():
    """Список всех людей."""
    return await get_persons_service()


@router.get("/persons/{person_id}", response_model=PersonSchemaOut)
async def get_person(person_id: str):
    """Детальная информация о персоне."""
    res = await get_person_service(person_id)
    return res


@router.get("/events")
async def get_events():
    """Все события, отсортированные по году (хронология)."""
    res = await get_events_service()
    return res
