#!/usr/bin/env python3
"""
Enhance Redbook analysis with detailed regex patterns and comprehensive examples.
"""

import json
import re
from pathlib import Path

analysis_path = Path("/home/user/slr/SLRinator/output/analysis/redbook_ALL_115_RULES_FIXED.json")

with open(analysis_path, 'r') as f:
    analysis = json.load(f)

# Enhanced patterns and examples for specific rules
enhancements = {
    "1.1": {
        "patterns": {
            "detect": [
                {"regex": r'"[^"]*\'[^\']+\'[^"]*"[^(]*(?!\(quoting)', "description": "Detects quote with nested single quote missing (quoting ...)", "flags": "g"},
                {"regex": r'"[^"]*"[^"]*"[^"]*"[^(]*(?!\(quoting)', "description": "Detects quote with nested escaped quote missing (quoting ...)", "flags": "g"}
            ],
            "validate": [
                {"regex": r'"[^"]*[\'"][^\'"]+"[^"]*"\s*\(quoting\s+[^)]+\)', "description": "Validates proper (quoting ...) parenthetical format", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                '"The Court stated \'the rule is clear\' in its opinion." Smith v. Jones, 100 U.S. at 50.',
                '"As noted, \\"the principle stands.\\"" Brown, 200 U.S. at 10.',
                'The opinion held "they \'must comply\' with the statute."1'
            ],
            "correct": [
                '"The Court stated \'the rule is clear\' in its opinion." Smith v. Jones, 100 U.S. at 50 (quoting Earlier Case, 50 U.S. at 25).',
                '"As noted, \\"the principle stands.\\"" Brown, 200 U.S. at 10 (quoting Foundation v. State, 75 U.S. at 5).',
                'The opinion held "they \'must comply\' with the statute."1\n1. Statute Case, 300 U.S. 100, 105 (1990) (quoting Compliance Act, 42 U.S.C. § 1983).'
            ]
        }
    },
    "1.12": {
        "patterns": {
            "detect": [
                {"regex": r'See generally\s+[^(]+\.\s*$', "description": "Detects 'see generally' without parenthetical (REQUIRED)", "flags": "gim"},
                {"regex": r'See generally\s+[^(]+;\s+', "description": "Detects 'see generally' in string without parenthetical", "flags": "gi"},
                {"regex": r'Cf\.\s+[^.]+\([^)]+\)\.', "description": "Detects 'cf.' with parenthetical (should NOT have one)", "flags": "g"}
            ],
            "validate": [
                {"regex": r'See generally\s+[^(]+\([^)]{10,}\)', "description": "Validates 'see generally' has substantive parenthetical (10+ chars)", "flags": "gi"},
                {"regex": r'Cf\.\s+[^.()]+\.', "description": "Validates 'cf.' lacks explanatory parenthetical", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "See generally RICHARD POSNER, ECONOMIC ANALYSIS OF LAW (9th ed. 2014).",
                "See generally John Doe, Theory of Justice, 100 HARV. L. REV. 1 (2020).",
                "Cf. Brown v. Board, 347 U.S. 483 (1954) (holding segregation unconstitutional).",
                "See generally Smith (2019); Jones (2020).",
                "Cf. Roe v. Wade, 410 U.S. 113 (1973) (establishing framework)."
            ],
            "correct": [
                "See generally RICHARD POSNER, ECONOMIC ANALYSIS OF LAW (9th ed. 2014) (providing comprehensive economic framework for analyzing legal rules).",
                "See generally John Doe, Theory of Justice, 100 HARV. L. REV. 1 (2020) (tracing historical development of distributive justice theories from Aristotle to Rawls).",
                "Cf. Brown v. Board, 347 U.S. 483 (1954).",
                "See generally Smith (2019) (discussing background); Jones (2020) (analyzing implementation).",
                "Cf. Roe v. Wade, 410 U.S. 113 (1973)."
            ]
        }
    },
    "1.9": {
        "patterns": {
            "detect": [
                {"regex": r'\([^()]*\([^)]+\)[^)]*\)', "description": "Detects nested parentheses (should use square brackets)", "flags": "g"}
            ],
            "validate": [
                {"regex": r'\([^()]*\[[^\]]+\][^)]*\)', "description": "Validates square brackets used for nested content", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "(citing (for example, the Hippocratic Oath)).",
                "(noting the rule (as stated in section 5)).",
                "(see discussion (Part II.A))"
            ],
            "correct": [
                "(citing [for example, the Hippocratic Oath]).",
                "(noting the rule [as stated in section 5]).",
                "(see discussion [Part II.A])"
            ]
        }
    },
    "3.6": {
        "patterns": {
            "detect": [
                {"regex": r'\d+\s+U\.S\.\s+\d+\s+\(', "description": "Detects case citation without pinpoint cite", "flags": "g"},
                {"regex": r'\d+\s+F\.\d+d\s+\d+\s+\(', "description": "Detects F.2d/F.3d citation without pinpoint", "flags": "g"}
            ],
            "validate": [
                {"regex": r'\d+\s+U\.S\.\s+\d+,\s+\d+\s+\(', "description": "Validates case citation has pinpoint cite", "flags": "g"},
                {"regex": r'\d+\s+F\.\d+d\s+\d+,\s+\d+\s+\(', "description": "Validates F.2d/F.3d has pinpoint", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "Roe v. Wade, 410 U.S. 113 (1973).",
                "Brown v. Board of Educ., 347 U.S. 483 (1954).",
                "Smith v. Jones, 100 F.3d 200 (5th Cir. 2000)."
            ],
            "correct": [
                "Roe v. Wade, 410 U.S. 113, 153 (1973).",
                "Brown v. Board of Educ., 347 U.S. 483, 495 (1954).",
                "Smith v. Jones, 100 F.3d 200, 205 (5th Cir. 2000)."
            ]
        }
    },
    "4.1": {
        "patterns": {
            "detect": [
                {"regex": r'(\d+)\.\s+Id\.\s+at\s+\d+\.[\s\S]{0,500}\2\.\s+(?!Id\.)', "description": "Detects id. used when source cited >5 footnotes ago", "flags": "g"}
            ],
            "validate": []
        },
        "examples": {
            "incorrect": [
                "5. Brown v. Board, 347 U.S. 483, 495 (1954).\n6. Smith (2020).\n7. Jones (2019).\n8. Williams (2018).\n9. Davis (2017).\n10. Miller (2016).\n11. Id. at 496. [ERROR: Brown cited in fn. 5, more than 5 footnotes ago]"
            ],
            "correct": [
                "5. Brown v. Board, 347 U.S. 483, 495 (1954).\n6. Smith (2020).\n7. Jones (2019).\n8. Williams (2018).\n9. Davis (2017).\n10. Miller (2016).\n11. Brown, 347 U.S. at 496."
            ]
        }
    },
    "10.9": {
        "patterns": {
            "detect": [
                {"regex": r'(\d+)\.\s+([A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+),\s+\d+\s+U\.S\.\s+\d+[\s\S]{0,500}\1\+[6-9]\.\s+\2,\s+\d+\s+U\.S\.\s+at', "description": "Detects short form used when case cited >5 footnotes ago (should use full)", "flags": "g"}
            ],
            "validate": []
        },
        "examples": {
            "incorrect": [
                "1. Roe v. Wade, 410 U.S. 113, 153 (1973).\n2. Smith (2020).\n3. Jones (2019).\n4. Brown (2018).\n5. Davis (2017).\n6. Miller (2016).\n7. Roe, 410 U.S. at 160. [ERROR: >5 footnotes, need full cite]"
            ],
            "correct": [
                "1. Roe v. Wade, 410 U.S. 113, 153 (1973).\n2. Smith (2020).\n3. Jones (2019).\n4. Brown (2018).\n5. Davis (2017).\n6. Miller (2016).\n7. Roe v. Wade, 410 U.S. 113, 160 (1973)."
            ]
        }
    },
    "12.1": {
        "patterns": {
            "detect": [
                {"regex": r'\d+\s+U\.S\.C\.\s+§\s+\d+\s+\((201[0-79]|202[1-9])\)', "description": "Detects U.S.C. with incorrect year (should be 2018 or 2020 supplement)", "flags": "g"}
            ],
            "validate": [
                {"regex": r'\d+\s+U\.S\.C\.\s+§\s+\d+\s+\((2018|Supp\.\s+20(19|20|21|22))\)', "description": "Validates U.S.C. uses current edition year", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "42 U.S.C. § 1983 (2012).",
                "15 U.S.C. § 78 (2016).",
                "26 U.S.C. § 501 (2021). [Unless 2021 volume published for this title]"
            ],
            "correct": [
                "42 U.S.C. § 1983 (2018).",
                "15 U.S.C. § 78 (2018).",
                "26 U.S.C. § 501 (Supp. 2020)."
            ]
        }
    },
    "18.1": {
        "patterns": {
            "detect": [
                {"regex": r'\(20\d{2}\)\s*\.\s*$', "description": "Detects internet source citation ending without URL", "flags": "gm"},
                {"regex": r'https?://[^\s]+', "description": "Validates URL present", "flags": "g"}
            ],
            "validate": [
                {"regex": r'https?://[^\s)]+', "description": "Validates URL format", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "John Doe, Article Title, WEBSITE (Jan. 1, 2020).",
                "Press Release, Company Name (Mar. 5, 2021).",
                "Report Title, ORG. NAME (2019)."
            ],
            "correct": [
                "John Doe, Article Title, WEBSITE (Jan. 1, 2020), https://example.com/article.",
                "Press Release, Company Name (Mar. 5, 2021), https://company.com/press/release.",
                "Report Title, ORG. NAME (2019), https://perma.cc/XXXX-YYYY."
            ]
        }
    },
    "24.5": {
        "patterns": {
            "detect": [
                {"regex": r',\s+and\s+', "description": "Detects potential serial comma usage", "flags": "g"},
                {"regex": r',\s+[a-z]+,\s+and\s+', "description": "Validates serial comma present", "flags": "g"}
            ],
            "validate": [
                {"regex": r',\s+\w+,\s+and\s+', "description": "Validates Oxford comma in list", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "Courts consider X, Y and Z.",
                "The factors include speed, accuracy and completeness.",
                "She cited Smith, Jones and Brown."
            ],
            "correct": [
                "Courts consider X, Y, and Z.",
                "The factors include speed, accuracy, and completeness.",
                "She cited Smith, Jones, and Brown."
            ]
        }
    },
    "24.7": {
        "patterns": {
            "detect": [
                {"regex": r'\.\s{2,}[A-Z]', "description": "Detects double space after period (should be single)", "flags": "g"},
                {"regex": r':\s{2,}', "description": "Detects double space after colon", "flags": "g"}
            ],
            "validate": [
                {"regex": r'\.\s[A-Z]', "description": "Validates single space after period", "flags": "g"}
            ]
        },
        "examples": {
            "incorrect": [
                "The Court held.  The defendant appealed.",
                "Consider this:  the implications are clear.",
                "First, X.  Second, Y."
            ],
            "correct": [
                "The Court held. The defendant appealed.",
                "Consider this: the implications are clear.",
                "First, X. Second, Y."
            ]
        }
    }
}

# Apply enhancements
for rule in analysis['rules']:
    rule_id = rule['id']
    if rule_id in enhancements:
        rule['patterns'] = enhancements[rule_id]['patterns']
        rule['examples'] = enhancements[rule_id]['examples']

# Update total error count
analysis['total_error_types'] = sum(len(r['error_types']) for r in analysis['rules'])

# Write enhanced output
with open(analysis_path, 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"Enhanced analysis:")
print(f"- Total rules: {len(analysis['rules'])}")
print(f"- Total error types: {analysis['total_error_types']}")
print(f"- Enhanced {len(enhancements)} rules with detailed patterns and examples")
print(f"- Critical fix verified for RB 1.12: {any(r.get('critical_fix') for r in analysis['rules'] if r['id'] == '1.12')}")
