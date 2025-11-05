from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from routers.auth import get_current_user, SessionDep
from schema.users import User
from schema.auth import UserProfilePublic, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/profile", response_model=UserProfilePublic)
def get_my_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return UserProfilePublic(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        province=current_user.province,
        city=current_user.city,
        role=current_user.role,
    )

@router.put("/me/profile", response_model=UserProfilePublic)
def update_my_profile(payload: UserProfileUpdate, current_user: Annotated[User, Depends(get_current_user)], session: SessionDep):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.province is not None:
        current_user.province = payload.province
    if payload.city is not None:
        current_user.city = payload.city

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return UserProfilePublic(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        province=current_user.province,
        city=current_user.city,
        role=current_user.role,
    )

@router.get("/me/history")
def get_my_history(current_user: Annotated[User, Depends(get_current_user)]):
    # TODO: Implementar con Reservas/Servicios reales; por ahora placeholder
    return {"last_services": []}
