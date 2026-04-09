#!/usr/bin/env python3
"""Test Ollama setup"""

import requests
import sys


def test_ollama () :
    print( "=" * 60 )
    print( "Testing Ollama Connection" )
    print( "=" * 60 )

    # Test connection
    try :
        resp = requests.get( "http://localhost:11434/api/tags", timeout=5 )
        if resp.status_code == 200 :
            models = resp.json().get( 'models', [] )
            print( f"✅ Ollama is running!" )
            print( f"   Models available:" )
            for m in models :
                print( f"   - {m.get( 'name', 'unknown' )}" )
        else :
            print( f"❌ Ollama returned status {resp.status_code}" )
            return False
    except Exception as e :
        print( f"❌ Cannot connect to Ollama: {e}" )
        print( "   Make sure 'ollama serve' is running in another terminal" )
        return False

    # Test embedding
    print( "\n📊 Testing embeddings..." )
    try :
        resp = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model" : "all-minilm", "prompt" : "Software Engineer with Python skills"},
            timeout=30
        )
        if resp.status_code == 200 :
            emb = resp.json().get( 'embedding', [] )
            print( f"   ✅ Embedding generated: {len( emb )} dimensions" )
            print( f"   First 5 values: {emb[:5]}" )
        else :
            print( f"   ❌ Embedding failed: {resp.status_code}" )
            print( f"   Response: {resp.text}" )
    except Exception as e :
        print( f"   ❌ Embedding error: {e}" )

    # Test chat
    print( "\n💬 Testing chat..." )
    try :
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model" : "llama3.2:3b",
                "messages" : [{"role" : "user", "content" : "Say 'hello world' in one word"}],
                "stream" : False,
                "options" : {"temperature" : 0.1}
            },
            timeout=60
        )
        if resp.status_code == 200 :
            reply = resp.json().get( 'message', {} ).get( 'content', '' )
            print( f"   ✅ Chat response: {reply[:100]}" )
        else :
            print( f"   ❌ Chat failed: {resp.status_code}" )
            print( f"   Response: {resp.text}" )
    except Exception as e :
        print( f"   ❌ Chat error: {e}" )

    return True


def test_backend_ollama () :
    print( "\n" + "=" * 60 )
    print( "Testing Backend Ollama Integration" )
    print( "=" * 60 )

    try :
        from backend.services.ollama_service import get_ollama_service
        svc = get_ollama_service()
        health = svc.health_check()

        if health.get( 'available' ) :
            print( f"✅ Ollama service detected!" )
            print( f"   Host: {health.get( 'host' )}" )
            print( f"   Embedding model: {health.get( 'embedding_model_loaded' )}" )
            print( f"   LLM model: {health.get( 'llm_model_loaded' )}" )
        else :
            print( f"❌ Ollama service not available: {health.get( 'error' )}" )
            return False
    except Exception as e :
        print( f"❌ Backend import error: {e}" )
        return False

    return True


if __name__ == "__main__" :
    print( "\n🔧 Ollama Setup Test\n" )

    ollama_ok = test_ollama()
    print()

    if ollama_ok :
        print( "✅ Ollama is working!" )
        print( "\nNow you can start the backend:" )
        print( "   uvicorn backend.main:app --reload" )
    else :
        print( "\n❌ Ollama setup incomplete. Please:" )
        print( "   1. In a terminal, run: ollama serve" )
        print( "   2. In another terminal, run: ollama pull all-minilm" )
        print( "   3. Then: ollama pull llama3.2:3b" )