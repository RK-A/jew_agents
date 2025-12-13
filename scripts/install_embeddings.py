"""Script to install and verify embedding dependencies"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and print result"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def test_imports():
    """Test if embeddings can be imported"""
    print(f"\n{'='*60}")
    print("Testing Imports")
    print(f"{'='*60}")
    
    tests = [
        ("langchain_openai", "from langchain_openai import OpenAIEmbeddings"),
        ("langchain_huggingface", "from langchain_huggingface import HuggingFaceEmbeddings"),
        ("langchain_community", "from langchain_community.embeddings import HuggingFaceEmbeddings"),
        ("langchain_core", "from langchain_core.embeddings import Embeddings"),
        ("embedding_factory", "from rag.embedding_factory import create_langchain_embeddings"),
    ]
    
    results = []
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name}")
            results.append(True)
        except ImportError as e:
            print(f"✗ {name}: {e}")
            results.append(False)
    
    return all(results)


def main():
    """Main installation script"""
    print("="*60)
    print("Embedding Dependencies Installation Script")
    print("="*60)
    
    # Step 1: Upgrade pip
    run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        "Step 1: Upgrading pip"
    )
    
    # Step 2: Install LangChain OpenAI
    run_command(
        [sys.executable, "-m", "pip", "install", "langchain-openai>=0.0.5"],
        "Step 2: Installing langchain-openai"
    )
    
    # Step 3: Install LangChain HuggingFace
    run_command(
        [sys.executable, "-m", "pip", "install", "langchain-huggingface>=0.0.1"],
        "Step 3: Installing langchain-huggingface"
    )
    
    # Step 4: Install sentence transformers
    run_command(
        [sys.executable, "-m", "pip", "install", "sentence-transformers>=2.2.0"],
        "Step 4: Installing sentence-transformers"
    )
    
    # Step 5: Install LangChain community
    run_command(
        [sys.executable, "-m", "pip", "install", "langchain-community>=0.0.10"],
        "Step 5: Installing langchain-community"
    )
    
    # Step 6: Test imports
    success = test_imports()
    
    print(f"\n{'='*60}")
    if success:
        print("✓ All embedding dependencies installed successfully!")
        print("="*60)
        print("\nYou can now use:")
        print("- OpenAI embeddings: EMBEDDING_PROVIDER=openai")
        print("- HuggingFace embeddings: EMBEDDING_PROVIDER=huggingface")
        print("- GigaChat embeddings: EMBEDDING_PROVIDER=gigachat")
        print("\nNext steps:")
        print("1. Configure .env file")
        print("2. Run: python main.py")
    else:
        print("✗ Some dependencies failed to install")
        print("="*60)
        print("\nPlease check errors above and:")
        print("1. Ensure Python 3.10+ is installed")
        print("2. Try: pip install -r requirements.txt")
        print("3. Check internet connection")
        sys.exit(1)


if __name__ == "__main__":
    main()

