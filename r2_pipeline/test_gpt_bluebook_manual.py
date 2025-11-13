#!/usr/bin/env python3
"""
Simple manual test of GPT + Full Bluebook.json on FN78-1
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.llm_interface import LLMInterface
from src.citation_parser import CitationParser
from src.rule_retrieval import BluebookRuleRetriever
from config.settings import BLUEBOOK_JSON_PATH
import json

def main():
    print("="*80)
    print("MANUAL TEST: GPT + Full Bluebook.json on FN78-1")
    print("="*80)

    # Load resources
    print("\n1. Loading resources...")
    llm = LLMInterface(use_vector_store=True)
    retriever = BluebookRuleRetriever(str(BLUEBOOK_JSON_PATH))

    with open(BLUEBOOK_JSON_PATH, 'r') as f:
        bluebook_json = json.load(f)
        bluebook_json_text = json.dumps(bluebook_json, indent=2)
    print(f"   ✓ Loaded Bluebook.json ({len(bluebook_json_text)} chars)")

    # Load prompt template
    prompt_path = Path(__file__).parent / "prompts" / "citation_format.txt"
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    print(f"   ✓ Loaded prompt template")

    # Extract FN78-1
    print("\n2. Extracting FN78-1...")
    fn78_text = """*SellPoolSuppliesOnline.com LLC v. Ugly Pools Arizona, Inc.*, 344 F. Supp. 3d 1075, 1081 (D. Ariz. 2018) ("The text of the DMCA does not limit the protection of CMI to registered works."); *Shihab v. Complex Media, Inc.*, No. 21-CV-6425 (PKC), 2022 WL 3544149, at *8 (S.D.N.Y. Aug. 17, 2022) ("The statutory language [of section 1202(b)(1)] plainly covers a wide range of conduct, and does not require that a defendant alter the CMI in any specific way."); Crusey, *supra* note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim does not require the plaintiff to prove 'direct causal relationship between the removal or alteration of CMI and any injury suffered by [the] plaintiff,' as '[t]he gravamen of the injury caused by a violation of section 1202 is … infringement of the public interest.'")."""

    parser = CitationParser(fn78_text, footnote_num=78)
    citations = parser.parse()
    citation = citations[0]  # FN78-1

    print(f"   Citation text: {citation.full_text[:100]}...")
    print(f"   Type: {citation.type}")

    # Get retrieved rules
    print("\n3. Retrieving relevant rules...")
    retrieved_rules, _ = retriever.retrieve_rules(citation.full_text)
    rules_context = retriever.format_rules_for_prompt(retrieved_rules)
    print(f"   ✓ Retrieved {len(retrieved_rules)} rules")

    # Format prompt
    print("\n4. Formatting prompt...")
    user_prompt = prompt_template.format(
        citation_text=citation.full_text,
        citation_type=citation.type,
        footnote_num=citation.footnote_num,
        citation_num=citation.citation_num,
        position="middle"
    )

    # Add retrieved rules
    if rules_context:
        user_prompt = f"{rules_context}\n\n---\n\n{user_prompt}"

    # Add full Bluebook.json
    user_prompt = f"{user_prompt}\n\n---\n\n## FULL BLUEBOOK.JSON FOR REFERENCE:\n```json\n{bluebook_json_text}\n```"

    print(f"   ✓ Prompt length: {len(user_prompt)} chars")
    print(f"   ✓ Estimated tokens: ~{len(user_prompt.split()) * 1.3:.0f}")

    # System prompt
    system_prompt = """You are an expert legal citation checker specialized in the Bluebook (21st edition).

Your task is to validate legal citations and identify formatting errors.

You have been provided with:
1. Retrieved relevant rules (at the top)
2. The citation to check
3. The FULL Bluebook.json file (at the bottom)

Use ALL of these sources to validate the citation. Cross-reference the retrieved rules with the full JSON to ensure accuracy."""

    # Call GPT
    print("\n5. Calling GPT-4o-mini with full Bluebook.json...")
    print("   (This may take 30-60 seconds due to large prompt size...)")

    result = llm.call_gpt(system_prompt, user_prompt, response_format="json", max_retries=3)

    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if result["success"]:
        validation = result["data"]

        print(f"\n✓ SUCCESS")
        print(f"\nIs Correct: {validation.get('is_correct')}")
        print(f"Overall Confidence: {validation.get('overall_confidence', 'N/A')}")
        print(f"Tokens Used: {result.get('tokens', 0)}")
        print(f"Cost: ${result.get('cost', 0):.4f}")

        errors = validation.get('errors', [])
        print(f"\nErrors Found: {len(errors)}")

        if errors:
            print("\nError Details:")
            for i, err in enumerate(errors, 1):
                print(f"\n  {i}. {err.get('error_type')}")
                print(f"     Description: {err.get('description')}")
                print(f"     Confidence: {err.get('confidence', 'N/A')}")
                print(f"     Rule: RB {err.get('rb_rule', 'N/A')} / BB {err.get('bluebook_rule', 'N/A')}")
                print(f"     Current: {err.get('current', '')[:80]}...")
                print(f"     Correct: {err.get('correct', '')[:80]}...")

        print(f"\nCorrected Version:")
        print(f"  {validation.get('corrected_version', 'N/A')[:200]}...")

        if validation.get('notes'):
            print(f"\nNotes: {validation['notes']}")

        if validation.get('file_search_confirmation'):
            print(f"\nFile Search: {validation['file_search_confirmation']}")

    else:
        print(f"\n✗ FAILED")
        print(f"Error: {result.get('error')}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
