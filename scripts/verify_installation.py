#!/usr/bin/env python3
"""
Installation verification script
Checks that all components are properly installed and configured
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from database.init_db import check_connection, get_table_counts
from rag.init_qdrant import check_qdrant_status
from utils.logging import get_logger


logger = get_logger(__name__)


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"  {text}")


async def check_configuration():
    """Check configuration settings"""
    print_header("CONFIGURATION CHECK")
    
    issues = []
    
    # Check LLM configuration
    if settings.llm_api_key and settings.llm_api_key != "your_openai_api_key_here":
        print_success(f"LLM Provider: {settings.llm_provider}")
        print_info(f"Model: {settings.llm_model}")
    else:
        print_error("LLM API key not configured")
        issues.append("Set LLM_API_KEY in .env file")
    
    # Check embedding configuration
    if settings.embedding_api_key and settings.embedding_api_key != "your_embedding_api_key_here":
        print_success(f"Embeddings: {settings.embedding_model}")
    else:
        print_warning("Embedding API key not configured (may use fallback)")
        print_info("Set EMBEDDING_API_KEY in .env for full functionality")
    
    # Check database configuration
    print_success(f"Database URL: {settings.postgres_url.split('@')[1] if '@' in settings.postgres_url else 'configured'}")
    
    # Check Qdrant configuration
    print_success(f"Qdrant URL: {settings.qdrant_url}")
    print_info(f"Collection: {settings.qdrant_collection}")
    
    return issues


async def check_database():
    """Check database connection and data"""
    print_header("DATABASE CHECK")
    
    issues = []
    
    # Check connection
    try:
        connected = await check_connection()
        if connected:
            print_success("PostgreSQL connection: OK")
        else:
            print_error("PostgreSQL connection: FAILED")
            issues.append("Cannot connect to PostgreSQL")
            return issues
    except Exception as e:
        print_error(f"PostgreSQL connection: FAILED - {e}")
        issues.append(f"Database error: {e}")
        return issues
    
    # Check tables and data
    try:
        counts = await get_table_counts()
        
        print_info(f"Products: {counts.get('jewelry_products', 0)}")
        print_info(f"Customers: {counts.get('customer_preferences', 0)}")
        print_info(f"Consultations: {counts.get('consultation_records', 0)}")
        
        if counts.get('jewelry_products', 0) == 0:
            print_warning("No products in database")
            print_info("Run: python scripts/manage_data.py fill")
        else:
            print_success("Database has data")
    
    except Exception as e:
        print_error(f"Failed to check table counts: {e}")
        issues.append(f"Table check error: {e}")
    
    return issues


async def check_qdrant():
    """Check Qdrant connection and collection"""
    print_header("QDRANT CHECK")
    
    issues = []
    
    try:
        status = await check_qdrant_status()
        
        if status.get("exists"):
            print_success("Qdrant connection: OK")
            print_success(f"Collection '{settings.qdrant_collection}': EXISTS")
            
            info = status.get("info", {})
            if info:
                print_info(f"Vectors count: {info.get('vectors_count', 'unknown')}")
                print_info(f"Points count: {info.get('points_count', 'unknown')}")
            
            if info.get('points_count', 0) == 0:
                print_warning("Qdrant collection is empty")
                print_info("Run: python scripts/manage_data.py sync")
        else:
            print_warning("Qdrant collection does not exist")
            print_info("Run: python scripts/manage_data.py init")
            issues.append("Qdrant collection not initialized")
    
    except Exception as e:
        print_error(f"Qdrant check failed: {e}")
        issues.append(f"Qdrant error: {e}")
    
    return issues


async def check_api_health():
    """Check if API is accessible"""
    print_header("API CHECK")
    
    issues = []
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"http://{settings.api_host}:{settings.api_port}/api/health",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    print_success("API is running and accessible")
                    data = response.json()
                    print_info(f"Status: {data.get('status')}")
                    print_info(f"Database: {'✓' if data.get('database_connected') else '✗'}")
                    print_info(f"Qdrant: {'✓' if data.get('qdrant_connected') else '✗'}")
                else:
                    print_warning(f"API returned status {response.status_code}")
            
            except httpx.ConnectError:
                print_warning("API is not running")
                print_info("Start with: docker-compose up -d")
                print_info("Or run: python main.py")
            
            except Exception as e:
                print_warning(f"Could not check API: {e}")
    
    except ImportError:
        print_warning("httpx not available, skipping API check")
        print_info("Install with: pip install httpx")
    
    return issues


async def check_dependencies():
    """Check if all required packages are installed"""
    print_header("DEPENDENCIES CHECK")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "asyncpg",
        "qdrant_client",
        "langchain",
        "openai",
        "pydantic",
        "pydantic_settings",
        "httpx",
        "pytest",
        "faker"
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print_warning(f"\nMissing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return [f"Missing packages: {', '.join(missing)}"]
    
    return []


async def main():
    """Run all verification checks"""
    print(f"\n{Colors.BOLD}AI JEWELRY CONSULTATION SYSTEM{Colors.END}")
    print(f"{Colors.BOLD}Installation Verification{Colors.END}")
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(await check_dependencies())
    all_issues.extend(await check_configuration())
    all_issues.extend(await check_database())
    all_issues.extend(await check_qdrant())
    all_issues.extend(await check_api_health())
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    if not all_issues:
        print_success("All checks passed! System is ready to use.")
        print_info("\nNext steps:")
        print_info("1. Visit API docs: http://localhost:8000/docs")
        print_info("2. Run tests: pytest tests/ -v")
        print_info("3. Test API: ./scripts/quick_api_test.sh")
        return 0
    else:
        print_error(f"Found {len(all_issues)} issue(s):\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print_info("\nFor help, see QUICKSTART.txt")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Verification failed: {e}{Colors.END}")
        sys.exit(1)

