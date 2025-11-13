#!/usr/bin/env python3
"""
Complete Test Suite for Bluebook Citation Validator
Tests ALL conditional states, edge cases, and rule combinations
"""

import json
from pathlib import Path
from bluebook_complete_validator import BluebookValidator, DocumentContext, CitationType

class ComprehensiveTestSuite:
    """Comprehensive test suite for all Bluebook rules"""
    
    def __init__(self):
        self.validator = BluebookValidator()
        self.test_cases = self._create_test_cases()
        self.results = []
        
    def _create_test_cases(self):
        """Create comprehensive test cases covering all scenarios"""
        return {
            # ==================== CASE CITATIONS ====================
            'case_citations': [
                {
                    'description': 'Basic federal case - correct',
                    'citation': '_Smith v. Jones_, 123 F.3d 456 (2d Cir. 2020)',
                    'context': {'document_context': DocumentContext.LAW_REVIEW_FOOTNOTE},
                    'expected_valid': True
                },
                {
                    'description': 'Federal case missing italics',
                    'citation': 'Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)',
                    'context': {'document_context': DocumentContext.LAW_REVIEW_FOOTNOTE},
                    'expected_valid': False,
                    'expected_violations': ['italics']
                },
                {
                    'description': 'United States as party - incorrect abbreviation',
                    'citation': 'U.S. v. Smith, 456 U.S. 789 (1982)',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['abbreviation']
                },
                {
                    'description': 'State case with parallel citations',
                    'citation': 'State v. Brown, 123 Cal. App. 4th 456, 789 P.3d 123 (2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with subsequent history',
                    'citation': 'Johnson v. State, 456 F.2d 789 (9th Cir. 1999), rev\'d, 534 U.S. 123 (2001)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with prior history',
                    'citation': 'Miller v. City, 534 U.S. 123 (2001), rev\'g 456 F.2d 789 (9th Cir. 1999)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with weight of authority parenthetical',
                    'citation': 'Davis v. County, 789 F.3d 456 (5th Cir. 2015) (en banc)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with explanatory parenthetical',
                    'citation': 'Wilson v. State, 321 F.3d 654 (7th Cir. 2010) (holding that defendant waived appeal)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with quoting parenthetical',
                    'citation': 'Taylor v. United States, 495 U.S. 575, 580 (1990) (quoting Chapman v. California, 386 U.S. 18, 24 (1967))',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with alteration parenthetical',
                    'citation': 'Lee v. State, 234 F.3d 789, 791 (3d Cir. 2000) (emphasis added)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Case with multiple parentheticals - wrong order',
                    'citation': 'Garcia v. City, 567 F.3d 890 (9th Cir. 2018) (explaining jurisdiction) (en banc)',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['parenthetical_order']
                }
            ],
            
            # ==================== STATUTORY CITATIONS ====================
            'statutory_citations': [
                {
                    'description': 'Federal statute - correct',
                    'citation': '42 U.S.C. § 1983 (2018)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Federal statute with subsections',
                    'citation': '26 U.S.C. § 501(c)(3) (2018)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Federal statute range',
                    'citation': '18 U.S.C. §§ 1961–1968 (2018)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'State statute - California',
                    'citation': 'Cal. Penal Code § 187 (West 2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'State statute - New York',
                    'citation': 'N.Y. C.P.L.R. § 3211 (McKinney 2019)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Statute with supplement',
                    'citation': '42 U.S.C. § 1983 (2018 & Supp. II 2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Statute missing year',
                    'citation': '42 U.S.C. § 1983',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['year_required']
                },
                {
                    'description': 'Statute with bad section spacing',
                    'citation': '42 U.S.C. §1983 (2018)',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['section_spacing']
                }
            ],
            
            # ==================== REGULATORY CITATIONS ====================
            'regulatory_citations': [
                {
                    'description': 'CFR citation - correct',
                    'citation': '45 C.F.R. § 164.502 (2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Federal Register citation',
                    'citation': '85 Fed. Reg. 54,876 (Sept. 3, 2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Federal Register to be codified',
                    'citation': '85 Fed. Reg. 54,876, 54,880 (Sept. 3, 2020) (to be codified at 45 C.F.R. pt. 164)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'State regulation',
                    'citation': 'Cal. Code Regs. tit. 22, § 51003.1 (2020)',
                    'context': {},
                    'expected_valid': True
                }
            ],
            
            # ==================== CONSTITUTIONAL CITATIONS ====================
            'constitutional_citations': [
                {
                    'description': 'U.S. Constitution article',
                    'citation': 'U.S. Const. art. I, § 8, cl. 3',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'U.S. Constitution amendment',
                    'citation': 'U.S. Const. amend. XIV, § 1',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'State constitution',
                    'citation': 'Cal. Const. art. IV, § 2',
                    'context': {},
                    'expected_valid': True
                }
            ],
            
            # ==================== SIGNALS ====================
            'signal_citations': [
                {
                    'description': 'See signal',
                    'citation': 'See Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'See also signal',
                    'citation': 'See also Brown v. Board of Educ., 347 U.S. 483 (1954)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Cf. signal',
                    'citation': 'Cf. Johnson v. State, 789 P.2d 123 (Cal. 1990)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Compare signal',
                    'citation': 'Compare Smith v. Jones, 123 F.3d 456 (2d Cir. 2020), with Brown v. Board, 347 U.S. 483 (1954)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'But see signal',
                    'citation': 'But see Miller v. California, 413 U.S. 15 (1973)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'String cite with wrong signal order',
                    'citation': 'But see Case1; See Case2',
                    'context': {'is_string_cite': True},
                    'expected_valid': False,
                    'expected_violations': ['signal_order']
                }
            ],
            
            # ==================== SHORT FORMS ====================
            'short_form_citations': [
                {
                    'description': 'Id. citation',
                    'citation': 'Id.',
                    'context': {'previous_citations': ['Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)']},
                    'expected_valid': True
                },
                {
                    'description': 'Id. with pinpoint',
                    'citation': 'Id. at 458',
                    'context': {'previous_citations': ['Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)']},
                    'expected_valid': True
                },
                {
                    'description': 'Id. without previous citation',
                    'citation': 'Id. at 458',
                    'context': {'previous_citations': []},
                    'expected_valid': False,
                    'expected_violations': ['id_usage']
                },
                {
                    'description': 'Supra for article',
                    'citation': 'Smith, supra note 5, at 123',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Supra for case (incorrect)',
                    'citation': 'Smith v. Jones, supra note 5',
                    'context': {'citation_type': CitationType.CASE},
                    'expected_valid': False,
                    'expected_violations': ['supra_usage']
                },
                {
                    'description': 'Short case form',
                    'citation': 'Smith, 123 F.3d at 458',
                    'context': {'is_short_form': True},
                    'expected_valid': True
                }
            ],
            
            # ==================== ELECTRONIC SOURCES ====================
            'electronic_citations': [
                {
                    'description': 'Website with permalink',
                    'citation': 'John Doe, Article Title, WEBSITE (Jan. 1, 2024), https://example.com/article [https://perma.cc/ABCD-1234]',
                    'context': {'document_context': DocumentContext.LAW_REVIEW_MAIN},
                    'expected_valid': True
                },
                {
                    'description': 'Website without permalink in law review',
                    'citation': 'John Doe, Article Title, WEBSITE (Jan. 1, 2024), https://example.com/article',
                    'context': {'document_context': DocumentContext.LAW_REVIEW_MAIN},
                    'expected_valid': False,
                    'expected_violations': ['permalink_required']
                },
                {
                    'description': 'Website with last visited date',
                    'citation': 'Article Title, https://example.com/article (last visited Jan. 1, 2024)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Database citation',
                    'citation': 'Smith v. Jones, No. 20-1234, 2020 WL 123456, at *5 (S.D.N.Y. Jan. 1, 2020)',
                    'context': {},
                    'expected_valid': True
                }
            ],
            
            # ==================== BOOKS AND ARTICLES ====================
            'book_article_citations': [
                {
                    'description': 'Book citation',
                    'citation': 'JOHN DOE, TITLE OF BOOK 123 (2d ed. 2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Book with multiple authors',
                    'citation': 'JOHN DOE & JANE SMITH, TITLE OF BOOK (2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Law review article',
                    'citation': 'John Doe, Article Title, 100 HARV. L. REV. 1234 (2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Article with pinpoint',
                    'citation': 'John Doe, Article Title, 100 HARV. L. REV. 1234, 1245 (2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Student note',
                    'citation': 'Note, Title of Note, 100 HARV. L. REV. 1234 (2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Forthcoming article',
                    'citation': 'John Doe, Article Title, 100 HARV. L. REV. (forthcoming 2024)',
                    'context': {},
                    'expected_valid': True
                }
            ],
            
            # ==================== INTERNATIONAL SOURCES ====================
            'international_citations': [
                {
                    'description': 'Treaty citation',
                    'citation': 'Treaty Name, Jan. 1, 2020, Country1-Country2, 123 U.N.T.S. 456',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'UN document',
                    'citation': 'U.N. Doc. A/RES/75/123 (Dec. 15, 2020)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'ICJ case',
                    'citation': 'Case Name (Country1 v. Country2), 2020 I.C.J. 123 (Jan. 1)',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'EU directive',
                    'citation': 'Council Directive 2020/123, 2020 O.J. (L 45) 67',
                    'context': {},
                    'expected_valid': True
                }
            ],
            
            # ==================== COMPLEX EDGE CASES ====================
            'edge_cases': [
                {
                    'description': 'Citation with multiple violations',
                    'citation': 'u.s. v smith 123 F3d 456',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['capitalization', 'punctuation', 'abbreviation', 'formatting']
                },
                {
                    'description': 'Nested parentheticals',
                    'citation': 'Case v. State, 123 F.3d 456 (2d Cir. 2020) (quoting Other v. Case, 789 F.2d 123 (3d Cir. 2019) (emphasis added))',
                    'context': {},
                    'expected_valid': True
                },
                {
                    'description': 'Page range with hyphen instead of en dash',
                    'citation': 'Smith v. Jones, 123 F.3d 456, 458-461 (2d Cir. 2020)',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['page_span']
                },
                {
                    'description': 'Ordinal with improper spacing',
                    'citation': 'Smith v. Jones, 123 F. 3d 456 (2 nd Cir. 2020)',
                    'context': {},
                    'expected_valid': False,
                    'expected_violations': ['ordinal_spacing']
                },
                {
                    'description': 'Mixed language citation',
                    'citation': 'Cour de cassation [Cass.] [supreme court for judicial matters] crim., June 15, 2020, Bull. crim., No. 123 (Fr.)',
                    'context': {'language': 'french'},
                    'expected_valid': True
                }
            ]
        }
    
    def run_all_tests(self):
        """Run all test cases"""
        print("COMPREHENSIVE BLUEBOOK VALIDATOR TEST SUITE")
        print("=" * 80)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category, tests in self.test_cases.items():
            print(f"\n{category.upper().replace('_', ' ')}")
            print("-" * 60)
            
            for test in tests:
                total_tests += 1
                result = self._run_single_test(test)
                
                if result['passed']:
                    passed_tests += 1
                    print(f"✓ {test['description']}")
                else:
                    failed_tests += 1
                    print(f"✗ {test['description']}")
                    print(f"  Citation: {test['citation']}")
                    print(f"  Reason: {result['reason']}")
                
                self.results.append(result)
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return self.results
    
    def _run_single_test(self, test):
        """Run a single test case"""
        result = {
            'description': test['description'],
            'citation': test['citation'],
            'passed': False,
            'reason': ''
        }
        
        try:
            validation = self.validator.validate_citation(
                test['citation'],
                **test.get('context', {})
            )
            
            expected_valid = test.get('expected_valid', True)
            
            if validation['valid'] == expected_valid:
                # Check if expected violations are present
                if 'expected_violations' in test:
                    found_violations = [v['rule'] for v in validation['violations']]
                    expected = test['expected_violations']
                    
                    if all(exp in str(found_violations) for exp in expected):
                        result['passed'] = True
                    else:
                        result['reason'] = f"Expected violations {expected}, got {found_violations}"
                else:
                    result['passed'] = True
            else:
                result['reason'] = f"Expected valid={expected_valid}, got valid={validation['valid']}"
                if validation['violations']:
                    result['reason'] += f". Violations: {[v['message'] for v in validation['violations']]}"
        
        except Exception as e:
            result['reason'] = f"Exception: {str(e)}"
        
        return result
    
    def save_results(self, filename='test_results.json'):
        """Save test results to file"""
        output_file = Path(f"/Users/ben/app/SLRinator/{filename}")
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nTest results saved to: {output_file}")

def main():
    """Run comprehensive test suite"""
    suite = ComprehensiveTestSuite()
    results = suite.run_all_tests()
    suite.save_results()

if __name__ == "__main__":
    main()