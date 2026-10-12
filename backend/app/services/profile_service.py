from typing import List, Optional
from backend.app.models.database import get_connection
from backend.app.schemas.profile import ProductProfileResponse

def list_profiles() -> List[ProductProfileResponse]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM product_profiles ORDER BY name ASC").fetchall()
        return [ProductProfileResponse(**dict(row)) for row in rows]

def get_profile_by_id(profile_id: str) -> Optional[ProductProfileResponse]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM product_profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not row:
            return None
        return ProductProfileResponse(**dict(row))
