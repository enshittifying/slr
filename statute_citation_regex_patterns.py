"""
Bluebook Rule 12: Statutes - Comprehensive Regex Patterns and Validators

This module provides complete regex patterns for validating and extracting
statute citations according to the Bluebook Rule 12 citation format.

Author: Legal Citation System
Date: 2025-11-23
"""

import re
from typing import Dict, List, Tuple, Optional


class StatuteRegexPatterns:
    """Collection of all Bluebook Rule 12 regex patterns"""

    # ===== FEDERAL CODE PATTERNS =====

    # Pattern 1.1: Standard Federal Code (U.S.C.) - Basic form
    FEDERAL_USC_BASIC = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.\s+§+\s*\d+(?:\([A-Za-z0-9\s\-\.]+\))?\s*\(\d{4}\)?',
        re.IGNORECASE
    )

    # Pattern 1.1: Federal Code without year (current code)
    FEDERAL_USC_NO_YEAR = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.\s+§+\s*\d+(?:\([A-Za-z0-9\s\-\.]+\))?(?!\s*\(\d{4}\))',
        re.IGNORECASE
    )

    # Pattern 1.2: Federal Code with range
    FEDERAL_USC_RANGE = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.\s+§§\s*\d+(?:\s*[-–]\s*\d+)(?:\s*,\s*\d+(?:\s*[-–]\s*\d+))*\s*\(\d{4}\)?',
        re.IGNORECASE
    )

    # Pattern 1.3: Federal Code with supplement
    FEDERAL_USC_SUPPLEMENT = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.\s+§+\s*\d+(?:\([A-Za-z0-9\s\-\.]+\))?\s+\(Supp\.\s+(?:I{1,3}\s+)?\d{1,2}\s*\)?\s*\(\d{4}\)?',
        re.IGNORECASE
    )

    # Pattern 1.4: Unofficial Federal Code (U.S.C.A. - West)
    FEDERAL_USCA = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.A\.\s+§+\s*\d+(?:\([A-Za-z0-9\s\-\.]+\))?\s*\(West\s+\d{4}\)?',
        re.IGNORECASE
    )

    # Pattern 1.4: Unofficial Federal Code (U.S.C.S. - Lexis)
    FEDERAL_USCS = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.S\.\s+§+\s*\d+(?:\([A-Za-z0-9\s\-\.]+\))?\s*\((?:Lexis|LexisNexis)\s+\d{4}\)?',
        re.IGNORECASE
    )

    # Pattern 1.5: Federal Code with database currency
    FEDERAL_USC_DATABASE = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.\s+§+\s*\d+\s*\([A-Z]{4,}\s+through\s+Pub\.\s+L\.\s+No\.\s+\d{3}[-–]\d{1,3}\)',
        re.IGNORECASE
    )

    # ===== STATE CODE PATTERNS =====

    # Pattern 2.1: Standard State Code
    STATE_CODE_GENERAL = re.compile(
        r'\b(?:Ala\.|Alaska|Ariz\.|Ark\.|Cal\.|Colo\.|Conn\.|Del\.|Fla\.|Ga\.|Haw\.|Idaho|Ill\.|Ind\.|Iowa|Kan\.|Ky\.|La\.|Me\.|Md\.|Mass\.|Mich\.|Minn\.|Miss\.|Mo\.|Mont\.|Neb\.|Nev\.|N\.H\.|N\.J\.|N\.M\.|N\.Y\.|N\.C\.|N\.D\.|Ohio|Okla\.|Or\.|Pa\.|R\.I\.|S\.C\.|S\.D\.|Tenn\.|Tex\.|Utah|Vt\.|Va\.|Wash\.|W\.Va\.|Wis\.|Wyo\.)\s+(?:Code|Rev\.|Rev\.\s+Stat\.|Compiled\s+Stat\.|Penal\s+Code|Bus\.\s+&\s+Prof\.\s+Code|Fam\.\s+Code|Prob\.\s+Code|Veh\.\s+Code)(?:\s+Ann\.)?\.?\s+§+\s*[\d\.]+(?:\([a-z]\))?(?:\s*\(\d{4}\))?',
        re.IGNORECASE
    )

    # Pattern 2.2: State Code with Supplement
    STATE_CODE_SUPPLEMENT = re.compile(
        r'\b(?:Ala|Ariz|Ark|Colo|Conn|Fla|Ga|Haw|Idaho|Ill|Ind|Iowa|Kan|Ky|La|Me|Md|Mass|Mich|Minn|Miss|Mo|Mont|Neb|Nev|N\.H|N\.J|N\.M|N\.Y|N\.C|N\.D|Ohio|Okla|Or|Pa|R\.I|S\.C|S\.D|Tenn|Tex|Utah|Vt|Va|Wash|W\.Va|Wis|Wyo)\.?\s+(?:Code|Rev\.\s+Stat\.)\s+§+\s*\d+\s+\(Supp\.\s+\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 2.3: State Code with Publisher (West, Lexis, McKinney, Vernon)
    STATE_CODE_PUBLISHER = re.compile(
        r'\b(?:Ala\.|Alaska|Ariz\.|Ark\.|Cal\.|Colo\.|Conn\.|Del\.|Fla\.|Ga\.|Haw\.|Idaho|Ill\.|Ind\.|Iowa|Kan\.|Ky\.|La\.|Me\.|Md\.|Mass\.|Mich\.|Minn\.|Miss\.|Mo\.|Mont\.|Neb\.|Nev\.|N\.H\.|N\.J\.|N\.M\.|N\.Y\.|N\.C\.|N\.D\.|Ohio|Okla\.|Or\.|Pa\.|R\.I\.|S\.C\.|S\.D\.|Tenn\.|Tex\.|Utah|Vt\.|Va\.|Wash\.|W\.Va\.|Wis\.|Wyo\.)\s+(?:Code|Rev\.|Stat\.)\s+§+\s*\d+(?:\s+\((?:West|Lexis|Lexis\s+Nexis|McKinney|Vernon|Thomson\s+Reuters)\s+\d{4}\))?',
        re.IGNORECASE
    )

    # ===== SESSION LAW PATTERNS =====

    # Pattern 3.1: Federal Session Law (Statutes at Large)
    FEDERAL_SESSION_LAW = re.compile(
        r'\b(?:Pub\.\s+L\.\s+No\.|Public\s+Law\s+No\.)\s+\d{3}[-–]\d{1,4}\s*,\s*\d+\s+Stat\.\s+\d+\s*\(\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 3.2: Session Law with Act Name
    SESSION_LAW_WITH_NAME = re.compile(
        r'\b(?:[A-Z][a-zA-Z\s&]+Act)\s+(?:of\s+)?(?:Pub\.\s+L\.\s+No\.|Ch\.)\s+\d{3}[-–]\d{1,4}\s*,\s*\d+\s+(?:Stat\.|[A-Z]{2}\s+Stat\.)\s+\d+\s*\(\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 3.3: State Session Law
    STATE_SESSION_LAW = re.compile(
        r'\bAct\s+of\s+(?:Jan\.|Feb\.|Mar\.|Apr\.|May|June|July|Aug\.|Sept\.|Oct\.|Nov\.|Dec\.)\s+\d{1,2}\s*,\s*\d{4}\s*,\s*ch\.\s+\d+\s*,\s*\d{4}\s+(?:Ill\.|Tex\.|Cal\.|N\.Y\.)\s+Stat\.\s+\d+',
        re.IGNORECASE
    )

    # ===== INTERNAL REVENUE CODE PATTERNS =====

    # Pattern 4.1: I.R.C. Section Citation
    IRC_CITATION = re.compile(
        r'\bI\.R\.C\.\s+§+\s*\d+(?:\([a-z]\))?(?:\([A-Z]\))?(?:\([A-Z]\))?',
        re.IGNORECASE
    )

    # Pattern 4.2: Federal Code 26 (I.R.C. Alternative Form)
    FEDERAL_26_CODE = re.compile(
        r'\b26\s+U\.S\.C\.\s+§+\s*\d+(?:\([a-z]\))?(?:\s*\(\d{4}\))?',
        re.IGNORECASE
    )

    # ===== RULES OF PROCEDURE PATTERNS =====

    # Pattern 5.1: Federal Rules of Civil Procedure
    FED_RULES_CIV = re.compile(
        r'\bFed\.\s+R\.\s+Civ\.\s+P\.\s+\d+(?:\([a-z]\))?(?:\([A-Z]\))?',
        re.IGNORECASE
    )

    # Pattern 5.2: Federal Rules of Criminal Procedure
    FED_RULES_CRIM = re.compile(
        r'\bFed\.\s+R\.\s+Crim\.\s+P\.\s+\d+(?:\([a-z]\))?',
        re.IGNORECASE
    )

    # Pattern 5.3: Federal Rules of Evidence
    FED_RULES_EVID = re.compile(
        r'\bFed\.\s+R\.\s+Evid\.\s+\d+(?:\([a-z]\))?(?:\([A-Z]\))?',
        re.IGNORECASE
    )

    # Pattern 5.4: Federal Rules of Appellate Procedure
    FED_RULES_APP = re.compile(
        r'\bFed\.\s+R\.\s+App\.\s+P\.\s+\d+(?:\([a-z]\))?',
        re.IGNORECASE
    )

    # Pattern 5.5: State Rules of Procedure
    STATE_RULES_PROCEDURE = re.compile(
        r'\b(?:Ala\.|Alaska|Ariz\.|Ark\.|Cal\.|Colo\.|Conn\.|Del\.|Fla\.|Ga\.|Haw\.|Idaho|Ill\.|Ind\.|Iowa|Kan\.|Ky\.|La\.|Me\.|Md\.|Mass\.|Mich\.|Minn\.|Miss\.|Mo\.|Mont\.|Neb\.|Nev\.|N\.H\.|N\.J\.|N\.M\.|N\.Y\.|N\.C\.|N\.D\.|Ohio|Okla\.|Or\.|Pa\.|R\.I\.|S\.C\.|S\.D\.|Tenn\.|Tex\.|Utah|Vt\.|Va\.|Wash\.|W\.Va\.|Wis\.|Wyo\.)\s+(?:R\.\s+Civ\.\s+P\.|R\.\s+Crim\.\s+P\.|Sup\.\s+Ct\.\s+R\.)\s+[\d\.]+',
        re.IGNORECASE
    )

    # Pattern 5.6: District Court Rules
    DISTRICT_COURT_RULES = re.compile(
        r'\b(?:N\.D\.|S\.D\.|E\.D\.|W\.D\.)\s+(?:N\.Y\.|Ill\.|Ca\.|Tex\.|etc\.)\s+R\.\s+[\d\.]+',
        re.IGNORECASE
    )

    # ===== ORDINANCE PATTERNS =====

    # Pattern 6.1: Municipal Ordinance
    MUNICIPAL_ORDINANCE = re.compile(
        r'\b(?:[A-Z][a-z]+),\s+(?:Ill|N\.Y\.|Tex\.|Cal\.|Ohio|Fla\.)\s*,\s+(?:Municipal|City|County)\s+Code\s+§+\s*[\d\-\.]+\s*\(\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 6.2: Ordinance Number and Date
    ORDINANCE_NUMBER = re.compile(
        r'\bOrd\.\s+No\.\s+\d{1,5}\s*,\s*(?:adopted|passed)\s+(?:Jan\.|Feb\.|Mar\.|Apr\.|May|June|July|Aug\.|Sept\.|Oct\.|Nov\.|Dec\.)\s+\d{1,2}\s*,\s*\d{4}',
        re.IGNORECASE
    )

    # ===== RESTATEMENT AND MODEL CODE PATTERNS =====

    # Pattern 7.1: Restatement Citation
    RESTATEMENT = re.compile(
        r'\bRestatement\s+\((?:First|Second|Third|Fourth)\)\s+of\s+(?:[A-Za-z\s&]+)\s+§+\s*\d+\s*\((?:Am\.\s+Law\s+Inst\.|American\s+Law\s+Institute)\s+\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 7.2: Model Penal Code
    MODEL_PENAL_CODE = re.compile(
        r'\bModel\s+Penal\s+Code\s+§+\s*\d+\.\d+\s*\((?:Am\.\s+Law\s+Inst\.|American\s+Law\s+Institute)\s+\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 7.3: Uniform Commercial Code
    UCC_CODE = re.compile(
        r'\b(?:U\.C\.C\.|Uniform\s+Commercial\s+Code)\s+§+\s*\d[-–]\d+(?:\([a-z]\))?(?:\s+\((?:Am\.\s+Law\s+Inst|NCCUSL|UCC|Uniform\s+Law\s+Commission)\s+\d{4}\))?',
        re.IGNORECASE
    )

    # ===== SPECIAL CODES AND GUIDELINES =====

    # Pattern 8.1: U.S. Sentencing Guidelines
    SENTENCING_GUIDELINES = re.compile(
        r'\bU\.S\.\s+Sentencing\s+Guidelines\s+§+\s*\d+[A-Z]?\d*\.\d+\s*\(U\.S\.\s+Sentencing\s+Comm\'n\s+\d{4}\)',
        re.IGNORECASE
    )

    # Pattern 8.2: ABA Model Rules
    ABA_MODEL_RULES = re.compile(
        r'\b(?:ABA\s+)?Model\s+Rules\s+of\s+(?:Professional\s+)?Conduct\s+r\.\s+\d+\.\d+\s*\((?:Am\.\s+Bar\s+Ass\'n|American\s+Bar\s+Association)\s+\d{4}\)',
        re.IGNORECASE
    )

    # ===== ERROR PATTERNS (To identify incorrect citations) =====

    # Common Federal Code Errors
    FEDERAL_ERROR_MISSING_SYMBOL = re.compile(
        r'\b\d{1,3}\s+U\.S\.C\.\s+\d+',
        re.IGNORECASE
    )

    FEDERAL_ERROR_WRONG_ABBREV = re.compile(
        r'\b\d{1,3}\s+(?:USC|US\.C|USA)\s+§',
        re.IGNORECASE
    )

    FEDERAL_ERROR_SPACING = re.compile(
        r'\b\d{1,3}\s+U\s+S\s+C\.\s+§',
        re.IGNORECASE
    )

    # State Code Errors
    STATE_ERROR_NO_ABBREV = re.compile(
        r'\b(?:California|Texas|New York|Florida)\s+(?:Code|Statute|Penal\s+Code)\s+§',
        re.IGNORECASE
    )

    STATE_ERROR_UNCLEAR_JURISDICTION = re.compile(
        r'\b(?:Code|Penal\s+Code|Business\s+Code)\s+§\s*\d+\s*\(\d{4}\)',
        re.IGNORECASE
    )

    # Session Law Errors
    SESSION_ERROR_INCOMPLETE = re.compile(
        r'\bPub\.\s+L\.\s+No\.\s+\d{3}[-–]\d{1,4}(?!\s*,\s*\d+\s+Stat)',
        re.IGNORECASE
    )

    SESSION_ERROR_SPACING = re.compile(
        r'\bPub\.L\.\s+No\.|Pub\. L\.(?!\s+No\.)',
        re.IGNORECASE
    )

    # IRC Errors
    IRC_ERROR_NO_PERIODS = re.compile(
        r'\bIRC\s+§',
        re.IGNORECASE
    )

    # Rules Errors
    RULES_ERROR_MISSING_ABBREV = re.compile(
        r'\bFederal\s+Rule\s+(?:Civil|Criminal|Evidence)\s+Procedure\s+\d+',
        re.IGNORECASE
    )

    RULES_ERROR_SPACING = re.compile(
        r'\bFed\.R\.Civ\.P\.|Fed\.R\.Crim\.P\.|Fed\.R\.Evid\.',
        re.IGNORECASE
    )


class StatuteCitationValidator:
    """
    Validate statute citations against Bluebook Rule 12 standards.
    Provides methods to validate, extract, and analyze statute citations.
    """

    def __init__(self):
        """Initialize the validator with regex patterns"""
        self.patterns = StatuteRegexPatterns()

    # ===== FEDERAL CODE VALIDATION =====

    def validate_federal_usc(self, citation: str) -> bool:
        """Check if citation is valid federal U.S.C. citation"""
        if self.patterns.FEDERAL_USC_BASIC.search(citation):
            return True
        if self.patterns.FEDERAL_USC_NO_YEAR.search(citation):
            return True
        return False

    def validate_federal_code_range(self, citation: str) -> bool:
        """Check if citation is valid federal code range"""
        return bool(self.patterns.FEDERAL_USC_RANGE.search(citation))

    def validate_federal_supplement(self, citation: str) -> bool:
        """Check if citation includes valid supplement notation"""
        return bool(self.patterns.FEDERAL_USC_SUPPLEMENT.search(citation))

    def validate_unofficial_federal_code(self, citation: str) -> bool:
        """Check if citation is valid unofficial federal code (U.S.C.A. or U.S.C.S.)"""
        return bool(
            self.patterns.FEDERAL_USCA.search(citation) or
            self.patterns.FEDERAL_USCS.search(citation)
        )

    # ===== STATE CODE VALIDATION =====

    def validate_state_code(self, citation: str) -> bool:
        """Check if citation is valid state code citation"""
        return bool(self.patterns.STATE_CODE_GENERAL.search(citation))

    def validate_state_supplement(self, citation: str) -> bool:
        """Check if citation includes valid state supplement notation"""
        return bool(self.patterns.STATE_CODE_SUPPLEMENT.search(citation))

    def validate_state_publisher(self, citation: str) -> bool:
        """Check if citation includes state code with publisher"""
        return bool(self.patterns.STATE_CODE_PUBLISHER.search(citation))

    # ===== SESSION LAW VALIDATION =====

    def validate_federal_session_law(self, citation: str) -> bool:
        """Check if citation is valid federal session law"""
        return bool(
            self.patterns.FEDERAL_SESSION_LAW.search(citation) or
            self.patterns.SESSION_LAW_WITH_NAME.search(citation)
        )

    def validate_state_session_law(self, citation: str) -> bool:
        """Check if citation is valid state session law"""
        return bool(self.patterns.STATE_SESSION_LAW.search(citation))

    # ===== INTERNAL REVENUE CODE VALIDATION =====

    def validate_irc(self, citation: str) -> bool:
        """Check if citation is valid I.R.C. citation"""
        return bool(
            self.patterns.IRC_CITATION.search(citation) or
            self.patterns.FEDERAL_26_CODE.search(citation)
        )

    # ===== RULES VALIDATION =====

    def validate_federal_rules(self, citation: str) -> bool:
        """Check if citation is valid federal rules citation"""
        return bool(
            self.patterns.FED_RULES_CIV.search(citation) or
            self.patterns.FED_RULES_CRIM.search(citation) or
            self.patterns.FED_RULES_EVID.search(citation) or
            self.patterns.FED_RULES_APP.search(citation)
        )

    def validate_state_rules(self, citation: str) -> bool:
        """Check if citation is valid state rules citation"""
        return bool(self.patterns.STATE_RULES_PROCEDURE.search(citation))

    # ===== ORDINANCE VALIDATION =====

    def validate_ordinance(self, citation: str) -> bool:
        """Check if citation is valid municipal ordinance citation"""
        return bool(
            self.patterns.MUNICIPAL_ORDINANCE.search(citation) or
            self.patterns.ORDINANCE_NUMBER.search(citation)
        )

    # ===== RESTATEMENT AND MODEL CODE VALIDATION =====

    def validate_restatement(self, citation: str) -> bool:
        """Check if citation is valid Restatement citation"""
        return bool(self.patterns.RESTATEMENT.search(citation))

    def validate_model_code(self, citation: str) -> bool:
        """Check if citation is valid model code citation"""
        return bool(
            self.patterns.MODEL_PENAL_CODE.search(citation) or
            self.patterns.UCC_CODE.search(citation) or
            self.patterns.SENTENCING_GUIDELINES.search(citation) or
            self.patterns.ABA_MODEL_RULES.search(citation)
        )

    # ===== ERROR DETECTION =====

    def detect_federal_errors(self, citation: str) -> List[str]:
        """Identify common federal code citation errors"""
        errors = []
        if self.patterns.FEDERAL_ERROR_MISSING_SYMBOL.search(citation) and '§' not in citation:
            errors.append("Missing section symbol (§)")
        if self.patterns.FEDERAL_ERROR_WRONG_ABBREV.search(citation):
            errors.append("Incorrect U.S.C. abbreviation format")
        if self.patterns.FEDERAL_ERROR_SPACING.search(citation):
            errors.append("Incorrect spacing in U.S.C. abbreviation")
        return errors

    def detect_state_errors(self, citation: str) -> List[str]:
        """Identify common state code citation errors"""
        errors = []
        if self.patterns.STATE_ERROR_NO_ABBREV.search(citation):
            errors.append("State name not abbreviated (should use standard abbreviation)")
        if self.patterns.STATE_ERROR_UNCLEAR_JURISDICTION.search(citation):
            errors.append("Jurisdiction not clearly identified")
        return errors

    def detect_session_law_errors(self, citation: str) -> List[str]:
        """Identify common session law citation errors"""
        errors = []
        if self.patterns.SESSION_ERROR_INCOMPLETE.search(citation):
            errors.append("Incomplete session law citation (missing volume/page or year)")
        if self.patterns.SESSION_ERROR_SPACING.search(citation):
            errors.append("Incorrect spacing in Pub. L. No. abbreviation")
        return errors

    def detect_rules_errors(self, citation: str) -> List[str]:
        """Identify common rules citation errors"""
        errors = []
        if self.patterns.RULES_ERROR_MISSING_ABBREV.search(citation):
            errors.append("Federal rules not abbreviated (should use Fed. R. [Type] P.)")
        if self.patterns.RULES_ERROR_SPACING.search(citation):
            errors.append("Incorrect spacing in federal rules abbreviation")
        return errors

    # ===== EXTRACTION METHODS =====

    def extract_all_statute_citations(self, text: str) -> Dict[str, List[str]]:
        """Extract all statute citations from text by type"""
        return {
            'federal_codes': self.patterns.FEDERAL_USC_BASIC.findall(text),
            'federal_code_ranges': self.patterns.FEDERAL_USC_RANGE.findall(text),
            'unofficial_federal_codes': (
                self.patterns.FEDERAL_USCA.findall(text) +
                self.patterns.FEDERAL_USCS.findall(text)
            ),
            'state_codes': self.patterns.STATE_CODE_GENERAL.findall(text),
            'session_laws': (
                self.patterns.FEDERAL_SESSION_LAW.findall(text) +
                self.patterns.SESSION_LAW_WITH_NAME.findall(text) +
                self.patterns.STATE_SESSION_LAW.findall(text)
            ),
            'irc_citations': self.patterns.IRC_CITATION.findall(text),
            'federal_rules': (
                self.patterns.FED_RULES_CIV.findall(text) +
                self.patterns.FED_RULES_CRIM.findall(text) +
                self.patterns.FED_RULES_EVID.findall(text) +
                self.patterns.FED_RULES_APP.findall(text)
            ),
            'ordinances': (
                self.patterns.MUNICIPAL_ORDINANCE.findall(text) +
                self.patterns.ORDINANCE_NUMBER.findall(text)
            ),
            'restatements': self.patterns.RESTATEMENT.findall(text),
            'model_codes': (
                self.patterns.MODEL_PENAL_CODE.findall(text) +
                self.patterns.UCC_CODE.findall(text)
            ),
            'sentencing_guidelines': self.patterns.SENTENCING_GUIDELINES.findall(text),
            'aba_rules': self.patterns.ABA_MODEL_RULES.findall(text),
        }

    def extract_citations_with_context(self, text: str, context_chars: int = 50) -> List[Tuple[str, str]]:
        """Extract citations with surrounding context"""
        citations_with_context = []
        all_patterns = [
            self.patterns.FEDERAL_USC_BASIC,
            self.patterns.FEDERAL_USCA,
            self.patterns.FEDERAL_USCS,
            self.patterns.FEDERAL_SESSION_LAW,
            self.patterns.STATE_CODE_GENERAL,
            self.patterns.IRC_CITATION,
            self.patterns.FED_RULES_CIV,
            self.patterns.FED_RULES_CRIM,
            self.patterns.FED_RULES_EVID,
            self.patterns.MUNICIPAL_ORDINANCE,
            self.patterns.RESTATEMENT,
            self.patterns.MODEL_PENAL_CODE,
        ]

        for pattern in all_patterns:
            for match in pattern.finditer(text):
                start = max(0, match.start() - context_chars)
                end = min(len(text), match.end() + context_chars)
                context = text[start:end]
                citations_with_context.append((match.group(), context))

        return citations_with_context

    # ===== ANALYSIS METHODS =====

    def classify_citation(self, citation: str) -> Optional[str]:
        """Identify the type of citation"""
        if self.validate_federal_usc(citation):
            return "Federal Code (U.S.C.)"
        elif self.validate_unofficial_federal_code(citation):
            return "Unofficial Federal Code (U.S.C.A./U.S.C.S.)"
        elif self.validate_state_code(citation):
            return "State Code"
        elif self.validate_federal_session_law(citation) or self.validate_state_session_law(citation):
            return "Session Law"
        elif self.validate_irc(citation):
            return "Internal Revenue Code (I.R.C.)"
        elif self.validate_federal_rules(citation) or self.validate_state_rules(citation):
            return "Rules of Procedure"
        elif self.validate_ordinance(citation):
            return "Municipal Ordinance"
        elif self.validate_restatement(citation):
            return "Restatement"
        elif self.validate_model_code(citation):
            return "Model Code/Guidelines"
        return None

    def get_citation_details(self, citation: str) -> Dict[str, str]:
        """Extract detailed components of a citation"""
        details = {
            'full_citation': citation,
            'type': self.classify_citation(citation),
            'errors': [],
        }

        # Add type-specific errors
        if 'Federal' in str(details['type']):
            details['errors'].extend(self.detect_federal_errors(citation))
        elif 'State' in str(details['type']):
            details['errors'].extend(self.detect_state_errors(citation))
        elif 'Session' in str(details['type']):
            details['errors'].extend(self.detect_session_law_errors(citation))
        elif 'Procedure' in str(details['type']):
            details['errors'].extend(self.detect_rules_errors(citation))

        return details


# ===== USAGE EXAMPLES =====

if __name__ == "__main__":
    # Initialize validator
    validator = StatuteCitationValidator()

    # Test citations
    test_citations = [
        # Correct citations
        ("42 U.S.C. § 1983 (2018)", True),
        ("42 U.S.C. § 1983", True),
        ("42 U.S.C.A. § 1983 (West 2020)", True),
        ("42 U.S.C. §§ 9601-9675 (2010)", True),
        ("Cal. Penal Code § 187 (West 2018)", True),
        ("Fla. Stat. § 776.031 (2021)", True),
        ("Fed. R. Civ. P. 56", True),
        ("I.R.C. § 61", True),
        ("Civil Rights Act of 1964, Pub. L. No. 88-352, 78 Stat. 241 (1964)", True),
        ("Chicago, Ill., Municipal Code § 8-4-015 (2020)", True),
        ("Restatement (Second) of Contracts § 90 (Am. Law Inst. 1981)", True),
        ("Model Penal Code § 210.3 (Am. Law Inst. 1962)", True),

        # Incorrect citations
        ("42 USC 1983 (2018)", False),
        ("42 U.S.C. 1983 (2018)", False),
        ("Cal Penal Code 187 (2018)", False),
        ("Fed. R. Civ P. 56", False),
        ("IRC § 61", False),
    ]

    print("=" * 80)
    print("STATUTE CITATION VALIDATION TEST")
    print("=" * 80)

    for citation, expected_valid in test_citations:
        citation_type = validator.classify_citation(citation)

        # Check if citation is valid based on its type
        is_valid = (
            validator.validate_federal_usc(citation) or
            validator.validate_unofficial_federal_code(citation) or
            validator.validate_state_code(citation) or
            validator.validate_federal_session_law(citation) or
            validator.validate_state_session_law(citation) or
            validator.validate_irc(citation) or
            validator.validate_federal_rules(citation) or
            validator.validate_state_rules(citation) or
            validator.validate_ordinance(citation) or
            validator.validate_restatement(citation) or
            validator.validate_model_code(citation)
        )

        status = "✓ PASS" if is_valid == expected_valid else "✗ FAIL"
        validity = "VALID" if is_valid else "INVALID"
        citation_info = f"Type: {citation_type}" if citation_type else "Type: UNKNOWN"

        print(f"\n{status}")
        print(f"Citation: {citation}")
        print(f"Status: {validity}")
        print(f"{citation_info}")

        details = validator.get_citation_details(citation)
        if details['errors']:
            print(f"Errors: {'; '.join(details['errors'])}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
