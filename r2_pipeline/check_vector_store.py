#!/usr/bin/env python3
"""
Direct vector store health check
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
    print("VECTOR STORE HEALTH CHECK")
    print("="*80)

    # Initialize LLM interface
    print("\n1. Initializing LLM interface...")
    llm = LLMInterface(use_vector_store=True)

    if not llm.assistant_id:
        print("   ✗ No assistant ID configured")
        return

    print(f"   ✓ Assistant ID: {llm.assistant_id}")

    # Get assistant details
    print("\n2. Retrieving assistant...")
    try:
        assistant = llm.client.beta.assistants.retrieve(llm.assistant_id)
        print(f"   ✓ Assistant: {assistant.name}")
        print(f"   ✓ Model: {assistant.model}")
        print(f"   ✓ Tools: {[t.type for t in assistant.tools]}")

        # Get vector store IDs
        if assistant.tool_resources and hasattr(assistant.tool_resources, 'file_search'):
            vs_ids = assistant.tool_resources.file_search.vector_store_ids
            print(f"   ✓ Vector stores attached: {len(vs_ids)}")

            # Check each vector store
            print("\n3. Checking vector stores...")
            for vs_id in vs_ids:
                print(f"\n   Vector Store: {vs_id}")
                try:
                    # The correct way to access vector stores in newer API
                    vs = llm.client.beta.vector_stores.retrieve(vs_id)
                    print(f"     ✓ Name: {vs.name if hasattr(vs, 'name') else 'N/A'}")
                    print(f"     ✓ Status: {vs.status if hasattr(vs, 'status') else 'N/A'}")
                    print(f"     ✓ File counts: {vs.file_counts if hasattr(vs, 'file_counts') else 'N/A'}")
                    print(f"     ✓ Created at: {vs.created_at if hasattr(vs, 'created_at') else 'N/A'}")
                    print(f"     ✓ Usage bytes: {vs.usage_bytes if hasattr(vs, 'usage_bytes') else 'N/A'}")

                    # List files in vector store
                    print(f"\n     Files in vector store:")
                    try:
                        files = llm.client.beta.vector_stores.files.list(vector_store_id=vs_id)
                        print(f"     ✓ Total files: {len(files.data)}")
                        for i, file in enumerate(files.data[:5]):  # Show first 5
                            print(f"       - File {i+1}: {file.id} (status: {file.status})")
                        if len(files.data) > 5:
                            print(f"       ... and {len(files.data) - 5} more files")
                    except Exception as e:
                        print(f"       ✗ Could not list files: {e}")

                except Exception as e:
                    print(f"     ✗ Error: {e}")
                    print(f"     ✗ Type: {type(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("   ⚠ No vector stores found on assistant")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

    # Try to search vector store directly
    print("\n4. Testing vector store search...")
    try:
        # Create a simple test thread and message
        thread = llm.client.beta.threads.create()
        print(f"   ✓ Created test thread: {thread.id}")

        message = llm.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="What is Bluebook rule 10.2.1?"
        )
        print(f"   ✓ Created test message")

        # Create a run to test file search
        run = llm.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=llm.assistant_id
        )
        print(f"   ✓ Created test run: {run.id}")
        print(f"   ✓ Run status: {run.status}")

        # Wait a bit and check status
        import time
        time.sleep(2)

        run = llm.client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        print(f"   ✓ Run status after 2s: {run.status}")

        if run.status == 'failed':
            print(f"   ✗ Run failed: {run.last_error}")
        elif run.status == 'completed':
            print(f"   ✓ Run completed successfully!")
            messages = llm.client.beta.threads.messages.list(thread_id=thread.id)
            if messages.data:
                print(f"   ✓ Response: {messages.data[0].content[0].text.value[:200]}...")
        else:
            print(f"   ⏳ Run still in progress: {run.status}")

    except Exception as e:
        print(f"   ✗ Search test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("VECTOR STORE CHECK COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
