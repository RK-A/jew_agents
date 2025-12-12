#!/usr/bin/env python3
"""
CLI tool for managing jewelry database and Qdrant data

Usage:
    python scripts/manage_data.py init                    # Initialize database and Qdrant
    python scripts/manage_data.py fill                    # Fill with test data
    python scripts/manage_data.py fill --products 100     # Fill with custom counts
    python scripts/manage_data.py clear                   # Clear all data
    python scripts/manage_data.py status                  # Check data status
    python scripts/manage_data.py sync                    # Sync PostgreSQL to Qdrant
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.init_db import (
    init_database,
    check_connection,
    drop_tables,
    create_tables,
    get_table_counts
)
from database.fill_data import (
    fill_database,
    clear_all_data,
    get_data_summary
)
from rag.init_qdrant import init_qdrant_collection as init_qdrant, check_qdrant_status, clear_qdrant_collection
from rag.fill_qdrant import sync_products_to_qdrant as fill_qdrant_from_db
from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)


async def cmd_init():
    """Initialize database and Qdrant"""
    logger.info("=== Initializing Database and Qdrant ===")
    
    # Initialize database
    logger.info("Step 1/2: Initializing PostgreSQL...")
    await init_database()
    
    # Initialize Qdrant
    logger.info("Step 2/2: Initializing Qdrant...")
    await init_qdrant()
    
    logger.info("✓ Initialization complete!")


async def cmd_fill(args):
    """Fill database with test data"""
    logger.info("=== Filling Database with Test Data ===")
    
    products_count = args.products or settings.default_products_count
    users_count = args.users or settings.default_users_count
    consultations_count = args.consultations or settings.default_consultations_count
    
    logger.info(f"Configuration:")
    logger.info(f"  Products: {products_count}")
    logger.info(f"  Users: {users_count}")
    logger.info(f"  Consultations: {consultations_count}")
    
    if args.clear:
        logger.warning("Clearing existing data first...")
        await clear_all_data()
    
    await fill_database(
        products_count=products_count,
        users_count=users_count,
        consultations_count=consultations_count,
        clear_existing=False
    )
    
    summary = await get_data_summary()
    logger.info(f"✓ Database filled successfully: {summary}")


async def cmd_clear():
    """Clear all data from database and Qdrant"""
    logger.warning("=== Clearing All Data ===")
    logger.warning("This will delete all data from PostgreSQL and Qdrant!")
    
    # Clear PostgreSQL
    logger.info("Clearing PostgreSQL...")
    await clear_all_data()
    
    # Clear Qdrant
    logger.info("Clearing Qdrant...")
    await clear_qdrant_collection()
    
    logger.info("✓ All data cleared")


async def cmd_status():
    """Check status of database and Qdrant"""
    logger.info("=== System Status ===")
    
    # Check PostgreSQL
    logger.info("\n--- PostgreSQL ---")
    pg_connected = await check_connection()
    if pg_connected:
        counts = await get_table_counts()
        logger.info(f"Status: Connected ✓")
        logger.info(f"Products: {counts.get('jewelry_products', 0)}")
        logger.info(f"Users: {counts.get('customer_preferences', 0)}")
        logger.info(f"Consultations: {counts.get('consultation_records', 0)}")
        
        summary = await get_data_summary()
        if summary.get('product_categories'):
            logger.info(f"Product breakdown: {summary['product_categories']}")
    else:
        logger.error("Status: Disconnected ✗")
    
    # Check Qdrant
    logger.info("\n--- Qdrant ---")
    qdrant_status = await check_qdrant_status()
    if qdrant_status.get('exists'):
        logger.info(f"Status: Connected ✓")
        logger.info(f"Collection: {settings.qdrant_collection}")
        info = qdrant_status.get('info', {})
        logger.info(f"Collection info: {info}")
    else:
        logger.error("Status: Disconnected or collection not found ✗")
        if 'error' in qdrant_status:
            logger.error(f"Error: {qdrant_status['error']}")


async def cmd_sync(args):
    """Sync PostgreSQL products to Qdrant"""
    logger.info("=== Syncing PostgreSQL → Qdrant ===")
    
    if args.clear:
        logger.info("Clearing Qdrant collection first...")
        await clear_qdrant_collection()
        await init_qdrant()
    
    logger.info("Syncing products to Qdrant...")
    count = await fill_qdrant_from_db()
    
    logger.info(f"✓ Synced {count} products to Qdrant")


async def cmd_reset():
    """Reset everything: drop tables, clear Qdrant, reinitialize"""
    logger.warning("=== Resetting Everything ===")
    logger.warning("This will drop all tables and recreate them!")
    
    # Drop and recreate tables
    logger.info("Dropping PostgreSQL tables...")
    await drop_tables()
    
    logger.info("Creating PostgreSQL tables...")
    await create_tables()
    
    # Clear and reinitialize Qdrant
    logger.info("Clearing Qdrant...")
    await clear_qdrant_collection()
    
    logger.info("Initializing Qdrant...")
    await init_qdrant()
    
    logger.info("✓ Reset complete")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Manage jewelry database and Qdrant data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_data.py init
  python scripts/manage_data.py fill --products 100 --users 30
  python scripts/manage_data.py sync --clear
  python scripts/manage_data.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Init command
    subparsers.add_parser("init", help="Initialize database and Qdrant")
    
    # Fill command
    fill_parser = subparsers.add_parser("fill", help="Fill database with test data")
    fill_parser.add_argument("--products", type=int, help="Number of products to generate")
    fill_parser.add_argument("--users", type=int, help="Number of users to generate")
    fill_parser.add_argument("--consultations", type=int, help="Number of consultations to generate")
    fill_parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    fill_parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    # Clear command
    subparsers.add_parser("clear", help="Clear all data")
    
    # Status command
    subparsers.add_parser("status", help="Check system status")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync PostgreSQL to Qdrant")
    sync_parser.add_argument("--clear", action="store_true", help="Clear Qdrant before sync")
    
    # Reset command
    subparsers.add_parser("reset", help="Reset everything (drop tables, clear Qdrant)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Set random seed if provided
    if hasattr(args, 'seed') and args.seed:
        import random
        random.seed(args.seed)
        logger.info(f"Random seed set to: {args.seed}")
    
    # Execute command
    try:
        if args.command == "init":
            asyncio.run(cmd_init())
        elif args.command == "fill":
            asyncio.run(cmd_fill(args))
        elif args.command == "clear":
            asyncio.run(cmd_clear())
        elif args.command == "status":
            asyncio.run(cmd_status())
        elif args.command == "sync":
            asyncio.run(cmd_sync(args))
        elif args.command == "reset":
            asyncio.run(cmd_reset())
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

