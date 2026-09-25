"""
Matching Service placeholder.

Yash-Thakur will implement the full AI/heuristic multi-criteria matching service here.
For now, stubs to picking the nearest available verified worker via Lokesh's PostGIS geo helper.
"""

from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.worker import Worker
from backend.app.models.enums import VerificationStatus, WorkerAvailability
from app.db.geo_queries import nearby_workers_async


async def find_best_worker_match(
    db: AsyncSession,
    lat: float,
    lng: float,
    skill: Optional[str] = None,
    radius_km: float = 15.0,
) -> Tuple[Optional[Worker], Optional[str]]:
    """
    Placeholder matching service:
    Picks the nearest available verified worker within the radius using Lokesh's geo-query helper.

    Returns:
        (matched_worker, match_reason) or (None, None)
    """
    # TODO (Yash-Thakur): Implement multi-criteria AI matching algorithm
    # (distance + rating + workload balancing + cooperative fairness)
    nearby = await nearby_workers_async(
        db=db,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        skill=skill,
        verification_status=VerificationStatus.VERIFIED,
        availability=WorkerAvailability.AVAILABLE,
        limit=1,
    )

    if nearby:
        worker, dist_km = nearby[0]
        return worker, f"Nearest available verified worker ({dist_km:.1f} km away)"

    return None, None
