from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.profile_historical_stats import ProfileHistoricalStats
from app.schemas.profile_historical_stats import ProfileHistoricalStatsCreate, ProfileHistoricalStatsUpdate

class ProfileHistoricalStatsService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_stats(self, stats_in: ProfileHistoricalStatsCreate) -> ProfileHistoricalStats:
        # Ensure profile_id is provided, as it's a primary key
        if not stats_in.profile_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile ID is required.")
        
        # Check if stats for this profile_id already exist
        existing_stats = await self.get_stats_by_profile_id(stats_in.profile_id)
        if existing_stats:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                detail=f"Historical stats for profile_id '{stats_in.profile_id}' already exist.")

        stats = ProfileHistoricalStats(**stats_in.model_dump())
        self.db_session.add(stats)
        await self.db_session.commit()
        await self.db_session.refresh(stats)
        return stats

    async def get_stats_by_profile_id(self, profile_id: str) -> Optional[ProfileHistoricalStats]:
        result = await self.db_session.execute(
            select(ProfileHistoricalStats).filter(ProfileHistoricalStats.profile_id == profile_id)
        )
        return result.scalars().first()

    async def get_all_stats(self, skip: int = 0, limit: int = 100) -> List[ProfileHistoricalStats]:
        result = await self.db_session.execute(
            select(ProfileHistoricalStats).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update_stats(self, profile_id: str, stats_in: ProfileHistoricalStatsUpdate) -> Optional[ProfileHistoricalStats]:
        stats = await self.get_stats_by_profile_id(profile_id)
        if not stats:
            return None # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stats not found")
        
        update_data = stats_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(stats, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(stats)
        return stats

    async def delete_stats(self, profile_id: str) -> bool:
        stats = await self.get_stats_by_profile_id(profile_id)
        if not stats:
            return False # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stats not found")
        
        await self.db_session.delete(stats)
        await self.db_session.commit()
        return True

# Dependency provider (example)
from app.database import get_db # Assuming get_db provides AsyncSession
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession # Ensure AsyncSession is imported

async def get_profile_historical_stats_service(db: AsyncSession = Depends(get_db)) -> ProfileHistoricalStatsService:
    return ProfileHistoricalStatsService(db)
