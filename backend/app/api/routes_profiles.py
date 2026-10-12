from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.profile import ProductProfileResponse
from backend.app.services.profile_service import list_profiles, get_profile_by_id

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.get("", response_model=List[ProductProfileResponse])
def get_profiles():
    return list_profiles()

@router.get("/{profile_id}", response_model=ProductProfileResponse)
def get_profile(profile_id: str):
    profile = get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "not_found", "message": f"Profile '{profile_id}' not found."}
        })
    return profile
