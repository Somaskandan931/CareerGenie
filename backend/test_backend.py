#!/usr/bin/env python3
"""
Quick test script to verify backend setup
Run this from project root: python test_backend.py
"""

import sys
import os
from pathlib import Path


def test_imports () :
    """Test if all required packages can be imported"""
    print( "🔍 Testing Python package imports..." )

    required_packages = [
        ("fastapi", "FastAPI"),
        ("anthropic", "Anthropic"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "SentenceTransformer"),
        ("pdfplumber", "PDFPlumber"),
        ("docx", "python-docx"),
        ("dotenv", "python-dotenv"),
        ("google_search_results", "SerpAPI"),
    ]

    all_good = True
    for package, name in required_packages :
        try :
            __import__( package )
            print( f"  ✅ {name}" )
        except ImportError :
            print( f"  ❌ {name} - Run: pip install {package}" )
            all_good = False

    return all_good


def test_env_file () :
    """Check if .env file exists and has required keys"""
    print( "\n🔍 Checking environment configuration..." )

    env_path = Path( "backend/.env" )

    if not env_path.exists() :
        print( "  ❌ .env file not found at backend/.env" )
        print( "  📝 Create it with:" )
        print( "     SERPAPI_KEY=your_key_here" )
        print( "     ANTHROPIC_API_KEY=your_key_here" )
        return False

    print( "  ✅ .env file exists" )

    # Try to load it
    from dotenv import load_dotenv
    load_dotenv( env_path )

    serpapi_key = os.getenv( "SERPAPI_KEY" ) or os.getenv( "SEARCHAPI_KEY" )
    anthropic_key = os.getenv( "ANTHROPIC_API_KEY" )

    all_good = True

    if serpapi_key :
        print( f"  ✅ SERPAPI_KEY found (length: {len( serpapi_key )})" )
    else :
        print( "  ❌ SERPAPI_KEY not set in .env" )
        all_good = False

    if anthropic_key :
        print( f"  ✅ ANTHROPIC_API_KEY found (length: {len( anthropic_key )})" )
    else :
        print( "  ❌ ANTHROPIC_API_KEY not set in .env" )
        all_good = False

    return all_good


def test_directory_structure () :
    """Check if required directories exist"""
    print( "\n🔍 Checking directory structure..." )

    required_dirs = [
        "backend",
        "backend/services",
    ]

    required_files = [
        "backend/__init__.py",
        "backend/services/__init__.py",
        "backend/config.py",
        "backend/main.py",
        "backend/models.py",
        "backend/services/career_advisor.py",
        "backend/services/job_scraper.py",
        "backend/services/matcher.py",
        "backend/services/resume_parser.py",
        "backend/services/vector_store.py",
    ]

    all_good = True

    for dir_path in required_dirs :
        if Path( dir_path ).exists() :
            print( f"  ✅ {dir_path}/" )
        else :
            print( f"  ❌ {dir_path}/ missing - Create it with: mkdir -p {dir_path}" )
            all_good = False

    for file_path in required_files :
        if Path( file_path ).exists() :
            print( f"  ✅ {file_path}" )
        else :
            print( f"  ❌ {file_path} missing" )
            all_good = False

    return all_good


def test_backend_import () :
    """Try to import backend modules"""
    print( "\n🔍 Testing backend module imports..." )

    try :
        sys.path.insert( 0, str( Path.cwd() ) )

        from backend.config import settings
        print( "  ✅ backend.config" )

        from backend.services.vector_store import vector_store
        print( "  ✅ backend.services.vector_store" )

        from backend.services.career_advisor import career_advisor
        print( "  ✅ backend.services.career_advisor" )

        from backend.services.job_scraper import job_scraper
        print( "  ✅ backend.services.job_scraper" )

        from backend.services.matcher import job_matcher
        print( "  ✅ backend.services.matcher" )

        from backend.services.resume_parser import resume_parser
        print( "  ✅ backend.services.resume_parser" )

        print( "\n📊 Configuration Status:" )
        errors = settings.validate()
        if errors :
            print( "  ⚠️  Configuration issues:" )
            for error in errors :
                print( f"     - {error}" )
            return False
        else :
            print( "  ✅ All configuration valid" )
            return True

    except Exception as e :
        print( f"  ❌ Import failed: {str( e )}" )
        import traceback
        traceback.print_exc()
        return False


def main () :
    """Run all tests"""
    print( "=" * 60 )
    print( "Career Genie Backend Test Suite" )
    print( "=" * 60 )

    results = []

    results.append( ("Package Imports", test_imports()) )
    results.append( ("Directory Structure", test_directory_structure()) )
    results.append( ("Environment Config", test_env_file()) )
    results.append( ("Backend Modules", test_backend_import()) )

    print( "\n" + "=" * 60 )
    print( "Test Summary" )
    print( "=" * 60 )

    all_passed = True
    for test_name, passed in results :
        status = "✅ PASS" if passed else "❌ FAIL"
        print( f"{status} - {test_name}" )
        if not passed :
            all_passed = False

    print( "=" * 60 )

    if all_passed :
        print( "\n🎉 All tests passed! You're ready to run the backend:" )
        print( "   uvicorn backend.main:app --reload" )
    else :
        print( "\n⚠️  Some tests failed. Please fix the issues above." )
        print( "   Refer to SETUP_GUIDE.md for detailed instructions." )

    print()
    return 0 if all_passed else 1


if __name__ == "__main__" :
    exit( main() )