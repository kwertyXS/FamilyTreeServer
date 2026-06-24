from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.schemas.family import *
from src.schemas.family import TreeSchemaOut
from src.services.family_service import get_tree_service, get_person_service, get_events_service, get_persons_service

router = APIRouter()

sessionDep = Annotated[AsyncSession, Depends(get_session)]

@router.get("/tree", response_model=TreeSchemaOut)
async def get_tree(session: sessionDep):
    """Полное дерево: все люди + связи для отрисовки на фронте."""
    return await get_tree_service(session)


@router.get("/persons")
async def get_persons(session: sessionDep):
    """Список всех людей."""
    return await get_persons_service(session)


@router.get("/persons/{person_id}", response_model=PersonSchemaOut)
async def get_person(session: sessionDep, person_id: str):
    """Детальная информация о персоне."""
    res = await get_person_service(session, person_id)
    return res


@router.get("/events")
async def get_events(session: sessionDep):
    """Все события, отсортированные по году (хронология)."""
    res = await get_events_service(session)
    return res
