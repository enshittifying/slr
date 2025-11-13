"""
Utilities for handling markdown formatting in extracted text.
"""
import re


def normalize_markdown_spacing(text: str) -> str:
    """
    Normalize spacing around markdown formatting markers.

    Moves leading/trailing spaces outside of markdown markers:
    - `*supra *note` -> `*supra* note`
    - `* See*` -> `*See*`
    - `**bold **text` -> `**bold** text`
    - `[SC]text [/SC]` -> `[SC]text[/SC] `

    Also merges consecutive identical formatting:
    - `*See** *infra*` -> `*See infra*`
    - `**bold****text**` -> `**boldtext**`

    Args:
        text: Text with markdown notation

    Returns:
        Normalized text with proper spacing
    """
    # FIRST: Merge consecutive identical formatting markers
    # This fixes issues where Word XML splits a single italic run into multiple <w:t> elements

    # Merge consecutive italics: *word**space**word* -> *word space word*
    # Keep merging until no more consecutive pairs found
    max_iterations = 10
    for _ in range(max_iterations):
        old_text = text
        # Merge *text1** text2* -> *text1 text2* (space after **)
        text = re.sub(r'\*([^*]+)\*\* ([^*]+)\*', r'*\1 \2*', text)
        # Merge *text1**text2* -> *text1text2* (no space)
        text = re.sub(r'\*([^*]+)\*\*([^*]+)\*', r'*\1\2*', text)
        if text == old_text:
            break  # No more changes

    # Merge consecutive bold: **word****word** -> **wordword**
    for _ in range(max_iterations):
        old_text = text
        text = re.sub(r'\*\*([^\*]*?)\*\*\*\*([^\*]*?)\*\*', r'**\1\2**', text)
        text = re.sub(r'\*\*([^\*]*?)\*\*\s*\*\*([^\*]*?)\*\*', r'**\1 \2**', text)
        if text == old_text:
            break

    # Merge consecutive small caps: [SC]word[/SC][SC]word[/SC] -> [SC]wordword[/SC]
    for _ in range(max_iterations):
        old_text = text
        text = re.sub(r'\[SC\]([^\[]*?)\[/SC\]\[SC\]([^\[]*?)\[/SC\]', r'[SC]\1\2[/SC]', text)
        text = re.sub(r'\[SC\]([^\[]*?)\[/SC\]\s*\[SC\]([^\[]*?)\[/SC\]', r'[SC]\1 \2[/SC]', text)
        if text == old_text:
            break

    # THEN: Fix italic markers: move spaces outside
    # Pattern: *word space* -> *word* space
    text = re.sub(r'\*([^\*]+?)\s+\*', r'*\1* ', text)
    # Pattern: * space word* -> space *word*
    text = re.sub(r'\*\s+([^\*]+?)\*', r' *\1*', text)

    # Fix bold markers: move spaces outside
    # Pattern: **word space** -> **word** space
    text = re.sub(r'\*\*([^\*]+?)\s+\*\*', r'**\1** ', text)
    # Pattern: ** space word** -> space **word**
    text = re.sub(r'\*\*\s+([^\*]+?)\*\*', r' **\1**', text)

    # Fix small caps markers: move spaces outside
    # Pattern: [SC]word space[/SC] -> [SC]word[/SC] space
    text = re.sub(r'\[SC\]([^\[]+?)\s+\[/SC\]', r'[SC]\1[/SC] ', text)
    # Pattern: [SC] space word[/SC] -> space [SC]word[/SC]
    text = re.sub(r'\[SC\]\s+([^\[]+?)\[/SC\]', r' [SC]\1[/SC]', text)

    # Clean up any double spaces created
    text = re.sub(r'\s{2,}', ' ', text)

    return text


def strip_markdown(text: str) -> str:
    """
    Remove all markdown formatting markers, leaving only plain text.

    Args:
        text: Text with markdown notation

    Returns:
        Plain text without markdown markers
    """
    # Remove bold
    text = re.sub(r'\*\*([^\*]+?)\*\*', r'\1', text)
    # Remove italic
    text = re.sub(r'\*([^\*]+?)\*', r'\1', text)
    # Remove small caps
    text = re.sub(r'\[SC\]([^\[]+?)\[/SC\]', r'\1', text)

    return text


def markdown_to_word_format(text: str) -> dict:
    """
    Parse markdown text into segments with formatting info for Word document.

    Args:
        text: Text with markdown notation

    Returns:
        List of dicts with 'text' and formatting flags (is_italic, is_bold, is_smallcaps)
    """
    segments = []
    current_pos = 0

    # Pattern to match any markdown notation
    pattern = r'(\*\*.*?\*\*|\*.*?\*|\[SC\].*?\[/SC\])'

    for match in re.finditer(pattern, text):
        # Add any plain text before this match
        if match.start() > current_pos:
            plain_text = text[current_pos:match.start()]
            if plain_text:
                segments.append({
                    'text': plain_text,
                    'is_italic': False,
                    'is_bold': False,
                    'is_smallcaps': False
                })

        # Add the formatted text
        matched_text = match.group(0)

        if matched_text.startswith('**'):
            # Bold
            content = matched_text[2:-2]
            segments.append({
                'text': content,
                'is_italic': False,
                'is_bold': True,
                'is_smallcaps': False
            })
        elif matched_text.startswith('*'):
            # Italic
            content = matched_text[1:-1]
            segments.append({
                'text': content,
                'is_italic': True,
                'is_bold': False,
                'is_smallcaps': False
            })
        elif matched_text.startswith('[SC]'):
            # Small caps
            content = matched_text[4:-5]
            segments.append({
                'text': content,
                'is_italic': False,
                'is_bold': False,
                'is_smallcaps': True
            })

        current_pos = match.end()

    # Add any remaining plain text
    if current_pos < len(text):
        plain_text = text[current_pos:]
        if plain_text:
            segments.append({
                'text': plain_text,
                'is_italic': False,
                'is_bold': False,
                'is_smallcaps': False
            })

    return segments
