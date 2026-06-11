"""Open Topic Network — Relations API (C 阶段).

通用图边：subject -(relation_type)-> object
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import RelationCreate, RelationPublic
from core.open_topic import TenantMissingError
from services import relation_service
from services.relation_service import RelationServiceError


router = APIRouter()


@router.get("", response_model=list[RelationPublic])
async def list_relations(
    subject_type: str | None = Query(default=None),
    subject_id: uuid.UUID | None = Query(default=None),
    object_type: str | None = Query(default=None),
    object_id: uuid.UUID | None = Query(default=None),
    relation_type: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    # 出边查询
    if subject_type and subject_id:
        try:
            rels = await relation_service.list_relations_out(
                db, subject_type, subject_id, viewer=user,
                relation_type=relation_type, limit=limit, offset=offset,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except TenantMissingError as e:
            raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
        return [RelationPublic.model_validate(r) for r in rels]
    # 入边查询
    if object_type and object_id:
        try:
            rels = await relation_service.list_relations_in(
                db, object_type, object_id, viewer=user,
                relation_type=relation_type, limit=limit, offset=offset,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except TenantMissingError as e:
            raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
        return [RelationPublic.model_validate(r) for r in rels]
    raise HTTPException(
        status_code=400,
        detail="Provide (subject_type, subject_id) for outgoing or (object_type, object_id) for incoming.",
    )


@router.post("", response_model=RelationPublic, status_code=201)
async def create_relation(
    req: RelationCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        rel = await relation_service.create_relation(
            db,
            creator=user,
            subject_type=req.subject_type, subject_id=req.subject_id,
            relation_type=req.relation_type,
            object_type=req.object_type, object_id=req.object_id,
            weight=req.weight,
        )
    except RelationServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return RelationPublic.model_validate(rel)
