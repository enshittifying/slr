#!/usr/bin/env python3
"""
Vector Store Setup for R1 Validation
Creates and configures OpenAI Assistants API vector store with Bluebook.json
"""
import json
import sys
import time
from pathlib import Path
from openai import OpenAI

# Add config to path
sys.path.insert(0, str(Path(__file__).parent))
from config.validation_settings import OPENAI_API_KEY, BLUEBOOK_JSON_PATH, VECTOR_STORE_CACHE


def setup_vector_store():
    """Set up vector store with Bluebook.json for Assistants API."""
    print("="*70)
    print("Setting up OpenAI Vector Store for R1 Validation")
    print("="*70)

    if not OPENAI_API_KEY:
        print("❌ Error: OpenAI API key not configured")
        print("   Please set OPENAI_API_KEY in config/api_keys.json")
        return False

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Step 1: Check if Bluebook.json exists
    print(f"\n[1/4] Checking for Bluebook.json at {BLUEBOOK_JSON_PATH}")
    if not BLUEBOOK_JSON_PATH.exists():
        print(f"❌ Error: Bluebook.json not found at {BLUEBOOK_JSON_PATH}")
        print("   Please ensure Bluebook.json is in config/rules/")
        return False

    # Validate JSON
    try:
        with open(BLUEBOOK_JSON_PATH, 'r') as f:
            bluebook_data = json.load(f)
        redbook_rules = bluebook_data.get('redbook', {}).get('rules', [])
        bluebook_rules = bluebook_data.get('bluebook', {}).get('rules', [])
        print(f"✓ Found Bluebook.json with {len(redbook_rules)} Redbook + {len(bluebook_rules)} Bluebook rules")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in Bluebook.json: {e}")
        return False

    # Step 2: Create vector store
    print("\n[2/4] Creating vector store...")
    try:
        vector_store = client.beta.vector_stores.create(
            name="SLR Bluebook & Redbook Rules"
        )
        print(f"✓ Created vector store: {vector_store.id}")
    except Exception as e:
        print(f"❌ Error creating vector store: {e}")
        return False

    # Step 3: Upload Bluebook.json
    print("\n[3/4] Uploading Bluebook.json to vector store...")
    try:
        with open(BLUEBOOK_JSON_PATH, 'rb') as f:
            file_response = client.files.create(
                file=f,
                purpose='assistants'
            )
        print(f"✓ Uploaded file: {file_response.id}")

        # Add file to vector store
        client.beta.vector_stores.files.create(
            vector_store_id=vector_store.id,
            file_id=file_response.id
        )
        print(f"✓ Added file to vector store")

        # Wait for processing
        print("   Waiting for file processing...")
        for i in range(30):  # Wait up to 30 seconds
            vs = client.beta.vector_stores.retrieve(vector_store.id)
            if vs.file_counts.completed > 0:
                print(f"✓ File processed ({vs.file_counts.completed} files)")
                break
            time.sleep(1)
            print(f"   Still processing... ({i+1}s)")

    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return False

    # Step 4: Create assistant
    print("\n[4/4] Creating Bluebook assistant...")
    try:
        assistant = client.beta.assistants.create(
            name="SLR Bluebook Validator",
            instructions="""You are an expert legal citation validator for Stanford Law Review.

You have access to the complete Bluebook (21st edition) and Stanford Law Review Redbook via File Search.

CRITICAL RULES:
1. ALWAYS search your knowledge base BEFORE answering
2. Redbook rules take PRECEDENCE over Bluebook rules when they conflict
3. ONLY flag errors you can support with a direct rule citation
4. Quote the exact rule text as evidence for every error
5. If a citation is correct, say so - don't invent errors

Use File Search to find applicable rules, then validate the citation against those rules.""",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store.id]
                }
            }
        )
        print(f"✓ Created assistant: {assistant.id}")
    except Exception as e:
        print(f"❌ Error creating assistant: {e}")
        return False

    # Step 5: Save to cache
    print("\n[5/5] Saving configuration...")
    cache_data = {
        "vector_store_id": vector_store.id,
        "assistant_id": assistant.id,
        "file_id": file_response.id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bluebook_path": str(BLUEBOOK_JSON_PATH)
    }

    VECTOR_STORE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(VECTOR_STORE_CACHE, 'w') as f:
        json.dump(cache_data, f, indent=2)
    print(f"✓ Saved configuration to {VECTOR_STORE_CACHE}")

    # Summary
    print("\n" + "="*70)
    print("✓ Vector Store Setup Complete!")
    print("="*70)
    print(f"\nVector Store ID: {vector_store.id}")
    print(f"Assistant ID:    {assistant.id}")
    print(f"File ID:         {file_response.id}")
    print(f"\nThe R1 validation system will now use Assistants API with File Search")
    print("for comprehensive Bluebook/Redbook rule retrieval.\n")

    return True


def main():
    """Main entry point."""
    try:
        success = setup_vector_store()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
