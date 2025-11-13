#!/usr/bin/env python3
"""
Test script to compare Assistant API vs Regular GPT with full Bluebook.json
on citations FN78-1, FN78-2, FN78-3
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.llm_interface import LLMInterface
from src.citation_parser import CitationParser
from src.rule_retrieval import BluebookRuleRetriever
from config.settings import BLUEBOOK_JSON_PATH
import json

def load_bluebook_json():
    """Load the full Bluebook.json file."""
    with open(BLUEBOOK_JSON_PATH, 'r') as f:
        return json.load(f)

def load_prompt_template():
    """Load the citation format prompt."""
    prompt_path = Path(__file__).parent / "prompts" / "citation_format.txt"
    with open(prompt_path, 'r') as f:
        return f.read()

def extract_citations():
    """Extract the 3 citations from FN78."""
    # Manual extraction for FN78
    fn78_text = """*SellPoolSuppliesOnline.com LLC v. Ugly Pools Arizona, Inc.*, 344 F. Supp. 3d 1075, 1081 (D. Ariz. 2018) ("The text of the DMCA does not limit the protection of CMI to registered works."); *Shihab v. Complex Media, Inc.*, No. 21-CV-6425 (PKC), 2022 WL 3544149, at *8 (S.D.N.Y. Aug. 17, 2022) ("The statutory language [of section 1202(b)(1)] plainly covers a wide range of conduct, and does not require that a defendant alter the CMI in any specific way."); Crusey, *supra* note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim does not require the plaintiff to prove 'direct causal relationship between the removal or alteration of CMI and any injury suffered by [the] plaintiff,' as '[t]he gravamen of the injury caused by a violation of section 1202 is … infringement of the public interest.'")."""

    parser = CitationParser(fn78_text, footnote_num=78)
    citations = parser.parse()
    return citations[:3]  # Return first 3

def test_with_assistant(llm, citation, prompt_template, retriever):
    """Test using Assistant API with file search."""
    print(f"\n{'='*80}")
    print(f"TESTING WITH ASSISTANT API: FN{citation.footnote_num}-{citation.citation_num}")
    print(f"{'='*80}")

    # Get retrieved rules
    retrieved_rules, _ = retriever.retrieve_rules(citation.full_text)
    rules_context = retriever.format_rules_for_prompt(retrieved_rules)

    # Format prompt
    user_prompt = prompt_template.format(
        citation_text=citation.full_text,
        citation_type=citation.type,
        footnote_num=citation.footnote_num,
        citation_num=citation.citation_num,
        position="middle"
    )

    if rules_context:
        user_prompt = f"{rules_context}\n\n---\n\n{user_prompt}"

    # Call Assistant API
    result = llm.call_assistant_with_search(user_prompt, response_format="json", max_retries=2)

    if result["success"]:
        validation = result["data"]
        print(f"\n✓ SUCCESS")
        print(f"Is Correct: {validation.get('is_correct')}")
        print(f"Errors Found: {len(validation.get('errors', []))}")
        if validation.get('errors'):
            for i, err in enumerate(validation['errors'][:3], 1):  # Show first 3
                print(f"  {i}. {err.get('error_type')}: {err.get('description')[:80]}...")
        print(f"Tokens: {result.get('tokens', 0)}")
        print(f"Cost: ${result.get('cost', 0):.4f}")
        return validation
    else:
        print(f"\n✗ FAILED: {result.get('error')}")
        return None

def test_with_gpt_plus_bluebook(llm, citation, prompt_template, retriever, bluebook_json):
    """Test using regular GPT with full Bluebook.json appended."""
    print(f"\n{'='*80}")
    print(f"TESTING WITH GPT + FULL BLUEBOOK.JSON: FN{citation.footnote_num}-{citation.citation_num}")
    print(f"{'='*80}")

    # Get retrieved rules (for deterministic pre-filtering)
    retrieved_rules, _ = retriever.retrieve_rules(citation.full_text)
    rules_context = retriever.format_rules_for_prompt(retrieved_rules)

    # Format prompt
    user_prompt = prompt_template.format(
        citation_text=citation.full_text,
        citation_type=citation.type,
        footnote_num=citation.footnote_num,
        citation_num=citation.citation_num,
        position="middle"
    )

    # Add retrieved rules first
    if rules_context:
        user_prompt = f"{rules_context}\n\n---\n\n{user_prompt}"

    # Add full Bluebook.json at the end
    bluebook_text = json.dumps(bluebook_json, indent=2)
    user_prompt = f"{user_prompt}\n\n---\n\n## FULL BLUEBOOK.JSON FOR REFERENCE:\n```json\n{bluebook_text}\n```"

    # System prompt
    system_prompt = """You are an expert legal citation checker specialized in the Bluebook (21st edition).

Your task is to validate legal citations and identify formatting errors.

You have been provided with:
1. Retrieved relevant rules (at the top)
2. The citation to check
3. The FULL Bluebook.json file (at the bottom)

Use ALL of these sources to validate the citation. Cross-reference the retrieved rules with the full JSON to ensure accuracy."""

    # Call regular GPT
    result = llm.call_gpt(system_prompt, user_prompt, response_format="json", max_retries=3)

    if result["success"]:
        validation = result["data"]
        print(f"\n✓ SUCCESS")
        print(f"Is Correct: {validation.get('is_correct')}")
        print(f"Errors Found: {len(validation.get('errors', []))}")
        if validation.get('errors'):
            for i, err in enumerate(validation['errors'][:3], 1):  # Show first 3
                print(f"  {i}. {err.get('error_type')}: {err.get('description')[:80]}...")
        print(f"Tokens: {result.get('tokens', 0)}")
        print(f"Cost: ${result.get('cost', 0):.4f}")
        return validation
    else:
        print(f"\n✗ FAILED: {result.get('error')}")
        return None

def compare_results(assistant_result, gpt_result, citation):
    """Compare the two validation results."""
    print(f"\n{'='*80}")
    print(f"COMPARISON FOR FN{citation.footnote_num}-{citation.citation_num}")
    print(f"{'='*80}")

    if not assistant_result or not gpt_result:
        print("⚠ Cannot compare - one or both methods failed")
        return

    # Compare is_correct
    assistant_correct = assistant_result.get('is_correct')
    gpt_correct = gpt_result.get('is_correct')

    print(f"\nIs Correct:")
    print(f"  Assistant API: {assistant_correct}")
    print(f"  GPT+Bluebook:  {gpt_correct}")
    if assistant_correct == gpt_correct:
        print(f"  ✓ MATCH")
    else:
        print(f"  ✗ MISMATCH")

    # Compare error counts
    assistant_errors = len(assistant_result.get('errors', []))
    gpt_errors = len(gpt_result.get('errors', []))

    print(f"\nError Count:")
    print(f"  Assistant API: {assistant_errors}")
    print(f"  GPT+Bluebook:  {gpt_errors}")
    if assistant_errors == gpt_errors:
        print(f"  ✓ MATCH")
    else:
        print(f"  ✗ MISMATCH (difference: {abs(assistant_errors - gpt_errors)})")

    # Compare error types
    if assistant_errors > 0 or gpt_errors > 0:
        assistant_types = set(e.get('error_type') for e in assistant_result.get('errors', []))
        gpt_types = set(e.get('error_type') for e in gpt_result.get('errors', []))

        print(f"\nError Types:")
        print(f"  Assistant API: {assistant_types}")
        print(f"  GPT+Bluebook:  {gpt_types}")

        common = assistant_types & gpt_types
        only_assistant = assistant_types - gpt_types
        only_gpt = gpt_types - assistant_types

        if common:
            print(f"  Common: {common}")
        if only_assistant:
            print(f"  Only in Assistant: {only_assistant}")
        if only_gpt:
            print(f"  Only in GPT: {only_gpt}")

def main():
    print("="*80)
    print("ASSISTANT API vs GPT+BLUEBOOK.JSON COMPARISON TEST")
    print("Testing citations: FN78-1, FN78-2, FN78-3")
    print("="*80)

    # Initialize
    llm = LLMInterface(use_vector_store=True)
    retriever = BluebookRuleRetriever(str(BLUEBOOK_JSON_PATH))
    bluebook_json = load_bluebook_json()
    prompt_template = load_prompt_template()

    # Extract citations
    citations = extract_citations()
    print(f"\nExtracted {len(citations)} citations from FN78")

    # Test each citation with both methods
    for citation in citations:
        print(f"\n\n{'#'*80}")
        print(f"CITATION {citation.citation_num}: {citation.full_text[:80]}...")
        print(f"{'#'*80}")

        # Test with Assistant API
        assistant_result = test_with_assistant(llm, citation, prompt_template, retriever)

        # Wait a bit between tests
        import time
        time.sleep(5)

        # Test with GPT + Bluebook
        gpt_result = test_with_gpt_plus_bluebook(llm, citation, prompt_template, retriever, bluebook_json)

        # Compare
        compare_results(assistant_result, gpt_result, citation)

        # Wait between citations
        time.sleep(5)

    print(f"\n\n{'='*80}")
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
