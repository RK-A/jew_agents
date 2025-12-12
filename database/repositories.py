from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import JewelryProduct, CustomerPreference, ConsultationRecord
from utils.logging import get_logger


logger = get_logger(__name__)


class JewelryProductRepository:
    """Repository for jewelry product operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, product_data: Dict[str, Any]) -> JewelryProduct:
        """Create a new jewelry product"""
        product = JewelryProduct(**product_data)
        self.session.add(product)
        await self.session.flush()
        logger.info(f"Created product: {product.id}")
        return product
    
    async def get_by_id(self, product_id: str) -> Optional[JewelryProduct]:
        """Get product by ID"""
        result = await self.session.execute(
            select(JewelryProduct).where(JewelryProduct.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[JewelryProduct]:
        """Get all products with pagination"""
        result = await self.session.execute(
            select(JewelryProduct).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_category(self, category: str) -> List[JewelryProduct]:
        """Get products by category"""
        result = await self.session.execute(
            select(JewelryProduct).where(JewelryProduct.category == category)
        )
        return list(result.scalars().all())
    
    async def update(self, product_id: str, update_data: Dict[str, Any]) -> Optional[JewelryProduct]:
        """Update product"""
        await self.session.execute(
            update(JewelryProduct)
            .where(JewelryProduct.id == product_id)
            .values(**update_data)
        )
        await self.session.flush()
        return await self.get_by_id(product_id)
    
    async def delete(self, product_id: str) -> bool:
        """Delete product"""
        result = await self.session.execute(
            delete(JewelryProduct).where(JewelryProduct.id == product_id)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def search_by_text(self, query: str, limit: int = 10) -> List[JewelryProduct]:
        """
        Simple text search fallback (when Qdrant unavailable)
        Searches in name, description, category, and material fields
        """
        search_pattern = f"%{query.lower()}%"
        result = await self.session.execute(
            select(JewelryProduct).where(
                or_(
                    JewelryProduct.name.ilike(search_pattern),
                    JewelryProduct.description.ilike(search_pattern),
                    JewelryProduct.category.ilike(search_pattern),
                    JewelryProduct.material.ilike(search_pattern)
                )
            ).limit(limit)
        )
        return list(result.scalars().all())


class CustomerPreferenceRepository:
    """Repository for customer preference operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, preference_data: Union[Dict[str, Any], CustomerPreference]) -> CustomerPreference:
        """Create customer preference profile"""
        if isinstance(preference_data, CustomerPreference):
            preference = preference_data
        else:
            preference = CustomerPreference(**preference_data)
        self.session.add(preference)
        await self.session.flush()
        logger.info(f"Created customer profile: {preference.user_id}")
        return preference
    
    async def get(self, user_id: str) -> Optional[CustomerPreference]:
        """Get customer preference by user ID (alias for get_by_user_id)"""
        return await self.get_by_user_id(user_id)
    
    async def get_by_user_id(self, user_id: str) -> Optional[CustomerPreference]:
        """Get customer preference by user ID"""
        result = await self.session.execute(
            select(CustomerPreference).where(CustomerPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[CustomerPreference]:
        """Get all customer preferences"""
        result = await self.session.execute(select(CustomerPreference))
        return list(result.scalars().all())
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> Optional[CustomerPreference]:
        """Update customer preferences"""
        await self.session.execute(
            update(CustomerPreference)
            .where(CustomerPreference.user_id == user_id)
            .values(**update_data)
        )
        await self.session.flush()
        logger.info(f"Updated customer profile: {user_id}")
        return await self.get_by_user_id(user_id)
    
    async def delete(self, user_id: str) -> bool:
        """Delete customer preference"""
        result = await self.session.execute(
            delete(CustomerPreference).where(CustomerPreference.user_id == user_id)
        )
        await self.session.flush()
        return result.rowcount > 0


class ConsultationRecordRepository:
    """Repository for consultation record operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, record_data: Dict[str, Any]) -> ConsultationRecord:
        """Create consultation record"""
        record = ConsultationRecord(**record_data)
        self.session.add(record)
        await self.session.flush()
        logger.info(f"Created consultation record: {record.id} for user: {record.user_id}")
        return record
    
    async def get_by_id(self, record_id: str) -> Optional[ConsultationRecord]:
        """Get consultation record by ID"""
        result = await self.session.execute(
            select(ConsultationRecord).where(ConsultationRecord.id == record_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str, limit: int = 50) -> List[ConsultationRecord]:
        """Get consultation records for a user"""
        result = await self.session.execute(
            select(ConsultationRecord)
            .where(ConsultationRecord.user_id == user_id)
            .order_by(ConsultationRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ConsultationRecord]:
        """Get all consultation records with pagination"""
        result = await self.session.execute(
            select(ConsultationRecord)
            .order_by(ConsultationRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def delete(self, record_id: str) -> bool:
        """Delete consultation record"""
        result = await self.session.execute(
            delete(ConsultationRecord).where(ConsultationRecord.id == record_id)
        )
        await self.session.flush()
        return result.rowcount > 0

