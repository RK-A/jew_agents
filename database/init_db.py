import asyncio
from sqlalchemy import text
from database.session import engine, async_session
from database.models import Base
from utils.logging import get_logger

logger = get_logger(__name__)


async def create_tables():
    """Create all database tables if they don't exist"""
    try:
        async with engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        raise


async def check_connection():
    """Check database connection"""
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False


async def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        async with engine.begin() as conn:
            logger.warning("Dropping all database tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}", exc_info=True)
        raise


async def get_table_counts():
    """Get row counts for all tables"""
    try:
        async with async_session() as session:
            counts = {}
            
            # Count jewelry products
            result = await session.execute(text("SELECT COUNT(*) FROM jewelry_products"))
            counts["jewelry_products"] = result.scalar()
            
            # Count customer preferences
            result = await session.execute(text("SELECT COUNT(*) FROM customer_preferences"))
            counts["customer_preferences"] = result.scalar()
            
            # Count consultation records
            result = await session.execute(text("SELECT COUNT(*) FROM consultation_records"))
            counts["consultation_records"] = result.scalar()
            
            return counts
    except Exception as e:
        logger.error(f"Error getting table counts: {e}", exc_info=True)
        return {}


async def init_database():
    """Initialize database: check connection and create tables"""
    logger.info("Initializing database...")
    
    if not await check_connection():
        raise Exception("Failed to connect to database")
    
    # Create database tables - if schema mismatch is detected (e.g. id column type changed),
    # drop and recreate tables to avoid conflicts during inserts (useful during development).
    logger.info("Ensuring database schema is up-to-date")
    # Check if jewelry_products.id is an identity/serial column
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT is_identity FROM information_schema.columns WHERE table_name='jewelry_products' AND column_name='id'"))
            row = result.fetchone()
            needs_recreate = False
            if row is None:
                logger.info("Table jewelry_products or column id not found; will create tables")
                needs_recreate = True
            else:
                is_identity = row[0]  # 'YES' or 'NO'
                if is_identity != 'YES':
                    logger.info("Detected jewelry_products.id is not identity; will recreate tables to apply schema changes")
                    needs_recreate = True
            if needs_recreate:
                logger.warning("Dropping and recreating tables (development operation)")
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            else:
                await conn.run_sync(Base.metadata.create_all)
    except Exception:
        # If anything goes wrong with checking schema, fall back to create_tables
        logger.exception("Error checking existing schema; proceeding to create tables")
        await create_tables()
    
    counts = await get_table_counts()
    logger.info(f"Database status: {counts}")
    
    logger.info("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_database())

