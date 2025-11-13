#!/usr/bin/env python3
"""
Debug GPT-5 responses to understand empty response issue
"""

import json
from pathlib import Path
import openai
from src.processors.footnote_extractor import extract_footnotes_from_docx

def debug_gpt_responses():
    """Debug what GPT-5 is actually returning"""
    
    # Load API key
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    api_key = config['openai']['api_key']
    
    client = openai.OpenAI(api_key=api_key)
    
    # Extract a problematic footnote
    footnotes_dict = extract_footnotes_from_docx("output/data/SherkowGugliuzza_PostSP_PostEEFormatting[70].docx")
    footnotes = [(num, text) for num, text in footnotes_dict.items()]
    
    # Test footnote 3 (which was failing)
    footnote_text = footnotes[2][1]  # 0-indexed, so footnote 3 is index 2
    
    print("=" * 70)
    print("DEBUG: GPT-5 Response Analysis")
    print("=" * 70)
    print(f"\nFootnote 3 text ({len(footnote_text)} chars):")
    print(f"'{footnote_text[:200]}...'")
    
    # Test multiple approaches
    prompts_to_test = [
        ("Simple", "Extract citations as JSON: {\"citations\":[{\"type\":\"case\",\"text\":\"citation\"}]}"),
        ("Direct", "List all legal citations in this footnote as a JSON array."),
        ("Minimal", "Find citations. Return JSON with citations array."),
    ]
    
    for name, system_prompt in prompts_to_test:
        print(f"\n" + "-" * 50)
        print(f"Testing {name} approach...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "user", "content": f"{system_prompt}\n\nFootnote: {footnote_text[:300]}..."}
                ],
                max_completion_tokens=400
            )
            
            content = response.choices[0].message.content
            print(f"Response length: {len(content) if content else 0} chars")
            
            if content and content.strip():
                print(f"✅ Got response: '{content[:100]}...'")
                break
            else:
                print("❌ Empty response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test with minimal content to see if it's a content length issue
    print(f"\n" + "-" * 50)
    print("Testing with short content...")
    
    short_text = "See Smith v. Jones, 123 U.S. 456 (1995)."
    
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "user", "content": f"Extract citations: {short_text}"}
            ],
            max_completion_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"Short content response: '{content}'")
    
    except Exception as e:
        print(f"❌ Short content error: {e}")

if __name__ == "__main__":
    debug_gpt_responses()