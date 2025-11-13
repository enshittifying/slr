#!/usr/bin/env python3
"""
Check Assistant API and vector store health
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.llm_interface import LLMInterface
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("ASSISTANT API HEALTH CHECK")
    print("="*80)

    # Initialize LLM interface
    print("\n1. Initializing LLM interface...")
    llm = LLMInterface(use_vector_store=True)

    if not llm.assistant_id:
        print("   ✗ No assistant ID configured")
        return

    print(f"   ✓ Assistant ID: {llm.assistant_id}")
    print(f"   ✓ Vector store enabled: {llm.use_vector_store}")

    # Try to retrieve assistant
    print("\n2. Checking assistant status...")
    try:
        assistant = llm.client.beta.assistants.retrieve(llm.assistant_id)
        print(f"   ✓ Assistant retrieved successfully")
        print(f"     - Name: {assistant.name}")
        print(f"     - Model: {assistant.model}")
        print(f"     - Tools: {[t.type for t in assistant.tools]}")

        if assistant.tool_resources and assistant.tool_resources.file_search:
            vs_ids = assistant.tool_resources.file_search.vector_store_ids
            print(f"     - Vector Store IDs: {vs_ids}")

            # Check vector store health
            print("\n3. Checking vector store(s)...")
            for vs_id in vs_ids:
                try:
                    vs = llm.client.beta.vector_stores.retrieve(vs_id)
                    print(f"   ✓ Vector Store {vs_id}:")
                    print(f"     - Name: {vs.name}")
                    print(f"     - Status: {vs.status}")
                    print(f"     - File counts: {vs.file_counts}")
                except Exception as e:
                    print(f"   ✗ Vector Store {vs_id}: {e}")
        else:
            print("   ⚠ No vector stores attached to assistant")

    except Exception as e:
        print(f"   ✗ Failed to retrieve assistant: {e}")
        return

    # Try a simple test query
    print("\n4. Testing simple query...")
    test_query = "What is Bluebook rule 10.2.1 about?"

    try:
        result = llm.call_assistant_with_search(test_query, response_format="text", max_retries=3)

        if result["success"]:
            print(f"   ✓ Test query successful")
            print(f"     Response: {result['data'][:200]}...")
            print(f"     Tokens: {result['tokens']}")
            print(f"     Cost: ${result['cost']:.4f}")
        else:
            print(f"   ✗ Test query failed: {result['error']}")

    except Exception as e:
        print(f"   ✗ Test query exception: {e}")

    print("\n" + "="*80)
    print("HEALTH CHECK COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
