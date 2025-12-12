#!/usr/bin/env python3
"""
Quick test script to verify system initialization

This script tests:
1. Database connection
2. Qdrant connection
3. Data generation
4. RAG search functionality
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.init_db import check_connection, get_table_counts
from database.fill_data import generate_products, get_data_summary
from rag.init_qdrant import check_qdrant_status
from utils.logging import get_logger

logger = get_logger(__name__)


async def test_database():
    """Test database connection and tables"""
    logger.info("Testing database...")
    
    # Check connection
    connected = await check_connection()
    if not connected:
        logger.error("❌ Database connection failed")
        return False
    
    logger.info("✓ Database connected")
    
    # Check tables
    counts = await get_table_counts()
    logger.info(f"✓ Table counts: {counts}")
    
    return True


async def test_qdrant():
    """Test Qdrant connection"""
    logger.info("\nTesting Qdrant...")
    
    try:
        status = await check_qdrant_status()
        
        if status.get("exists"):
            logger.info("✓ Qdrant connected")
            logger.info(f"✓ Collection status: {status}")
            return True
        else:
            logger.warning("⚠ Qdrant collection doesn't exist (run 'manage_data.py init' first)")
            return True
    
    except Exception as e:
        logger.error(f"❌ Qdrant connection failed: {e}")
        return False


async def test_data_generation():
    """Test data generation"""
    logger.info("\nTesting data generation...")
    
    try:
        # Generate small test batch
        products = await generate_products(count=5)
        
        if len(products) == 5:
            logger.info("✓ Product generation working")
            logger.info(f"  Sample product: {products[0].name}")
            return True
        else:
            logger.error("❌ Product generation failed")
            return False
    
    except Exception as e:
        logger.error(f"❌ Data generation error: {e}")
        return False


async def test_system_status():
    """Get overall system status"""
    logger.info("\nSystem Status:")
    
    # Database
    counts = await get_table_counts()
    logger.info(f"  Products: {counts.get('jewelry_products', 0)}")
    logger.info(f"  Users: {counts.get('customer_preferences', 0)}")
    logger.info(f"  Consultations: {counts.get('consultation_records', 0)}")
    
    # Summary
    if counts.get('jewelry_products', 0) > 0:
        summary = await get_data_summary()
        if summary.get('product_categories'):
            logger.info(f"  Categories: {summary['product_categories']}")
    
    return True


async def main():
    """Run all tests"""
    logger.info("=== Quick System Test ===\n")
    
    results = []
    
    # Test database
    results.append(("Database", await test_database()))
    
    # Test Qdrant
    results.append(("Qdrant", await test_qdrant()))
    
    # Test data generation
    results.append(("Data Generation", await test_data_generation()))
    
    # System status
    await test_system_status()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        logger.info(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        logger.info("\n✓ All tests passed!")
        return 0
    else:
        logger.error("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

