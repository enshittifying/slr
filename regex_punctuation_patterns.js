/**
 * BLUEBOOK PUNCTUATION ERROR DETECTION - REGEX PATTERNS
 * Extracted from: /home/user/slr/reference_files/Bluebook.json
 *
 * Usage: Apply these patterns to legal documents to detect common punctuation errors
 * Priority levels: CRITICAL > HIGH > MEDIUM > LOW
 */

// ============================================================================
// CRITICAL PRIORITY - Must Fix
// ============================================================================

const CRITICAL_PATTERNS = {
  // 1. Nested parentheses (must use square brackets for inner)
  nestedParentheses: {
    pattern: /\([^)]*\([^)]*\)[^)]*\)/g,
    description: 'Nested parentheses detected. Use square brackets for inner parenthetical.',
    example: 'Wrong: (citing (for example, ...)); Right: (citing [for example, ...])',
    fix: (text) => text.replace(/\([^)]*\(([^)]*)\)[^)]*\)/g, '(citing [$1])')
  },

  // 2. Four dots instead of three (ellipsis error)
  fourDots: {
    pattern: /\.\.\.\./g,
    description: 'Four dots detected. Use exactly three dots for ellipsis.',
    example: 'Wrong: ....; Right: ...',
    fix: (text) => text.replace(/\.\.\.\./g, '...')
  },

  // 3. Missing periods in degree abbreviations
  missingDegreesPeriods: {
    pattern: /\b(JD|PhD|MBA|LLM|LLD|MSL|BCL)(?!\.)/g,
    description: 'Degree abbreviation missing periods per SLR Rule.',
    example: 'Wrong: PhD; Right: Ph.D.',
    fix: (text) => text.replace(/\b(JD)(?!\.)/g, 'J.D.')
                        .replace(/\b(PhD)(?!\.)/g, 'Ph.D.')
                        .replace(/\b(MBA)(?!\.)/g, 'M.B.A.')
  },

  // 4. Citation comma vs semicolon error (signals)
  signalCommaVsSemicolon: {
    pattern: /(See|Accord|See also|But see)\s+[^;]*\d{1,4}\s*\)\s*,\s*(See|Accord|See also|But see)\s+/g,
    description: 'Multiple sources with same signal should be separated by semicolon, not comma.',
    example: 'Wrong: See X, Y; Right: See X; See Y or See X, Y, and Z',
    note: 'This depends on signal type. Provide context-aware checking.'
  },

  // 5. Compare/Contrast with comma instead of semicolon
  compareContrastComma: {
    pattern: /Compare\s+[^;]*\),\s*with\s+[^;]*\)/g,
    description: 'Compare/contrast citations must be separated by semicolon, not comma.',
    example: 'Wrong: Compare X, with Y; Right: Compare X, with Y'
  },

  // 6. Double section symbols with hyphenated range
  doubleSectionSymbolRange: {
    pattern: /§§\s*\d+-\d+/g,
    description: 'Hyphenated ranges use single § symbol, not double.',
    example: 'Wrong: §§ 4001-03; Right: § 4001-03',
    fix: (text) => text.replace(/§§(\s*\d+-\d+)/g, '§$1')
  },

  // 7. Missing comma between repeated statutory digits
  missingCommaRepeatedDigits: {
    pattern: /§\s*\d+([a-z])\1(?!\s*,)/g,
    description: 'Repeated digits in statute must be separated by comma.',
    example: 'Wrong: § 1490dd; Right: § 1490, dd',
    fix: (text) => text.replace(/§\s*(\d+)([a-z])\2/g, '§ $1, $2$2')
  }
};

// ============================================================================
// HIGH PRIORITY - Important Spacing & Formatting
// ============================================================================

const HIGH_PRIORITY_PATTERNS = {
  // 1. Period after section/paragraph symbol
  periodAfterSectionSymbol: {
    pattern: /([§¶]\s*\d+)\./g,
    description: 'No period after section or paragraph symbols.',
    example: 'Wrong: § 1234.; Right: § 1234',
    fix: (text) => text.replace(/([§¶]\s*\d+)\./g, '$1')
  },

  // 2. No space after comma
  noSpaceAfterComma: {
    pattern: /,([^\s\d.\n])/g,
    description: 'Missing space after comma.',
    example: 'Wrong: Smith,Johnson; Right: Smith, Johnson',
    fix: (text) => text.replace(/,([^\s])/g, ', $1')
  },

  // 3. Space before comma
  spaceBeforeComma: {
    pattern: /\s+,/g,
    description: 'Space before comma not allowed.',
    example: 'Wrong: text ,citation; Right: text, citation',
    fix: (text) => text.replace(/\s+,/g, ',')
  },

  // 4. No space after semicolon
  noSpaceAfterSemicolon: {
    pattern: /;([^\s.\n])/g,
    description: 'Missing space after semicolon.',
    example: 'Wrong: X;Y; Right: X; Y',
    fix: (text) => text.replace(/;([^\s])/g, '; $1')
  },

  // 5. Double punctuation (commas, periods, etc.)
  doublePunctuation: {
    pattern: /([.,;:?!])\1+/g,
    description: 'Consecutive duplicate punctuation marks.',
    example: 'Wrong: citation..; Right: citation.',
    fix: (text) => text.replace(/([.,;:?!])\1+/g, '$1')
  },

  // 6. Space before period (except ellipsis)
  spaceBeforePeriod: {
    pattern: /\s+\.(?!\.)/g,
    description: 'Space before period not allowed.',
    example: 'Wrong: text .; Right: text.',
    fix: (text) => text.replace(/\s+\.(?!\.)/g, '.')
  },

  // 7. Unmatched parentheses count
  unmatchedParentheses: {
    pattern: /(?:^|[^\\])(?:\((?:[^()]|\([^)]*\))*[^)]$|[^(](?:\)(?:[^()]|\([^)]*\))*\())/gm,
    description: 'Unmatched opening or closing parentheses.',
    note: 'Requires more sophisticated bracket matching algorithm'
  },

  // 8. Multiple spaces between words
  multipleSpaces: {
    pattern: /  +/g,
    description: 'Multiple consecutive spaces.',
    example: 'Wrong: text  citation; Right: text citation',
    fix: (text) => text.replace(/  +/g, ' ')
  },

  // 9. Em dash spacing issues
  emDashSpacing: {
    pattern: /(\w+)\s+—\s+(\()/g,
    description: 'Em dash before parenthetical should have single space.',
    example: 'Check em dash spacing around parentheticals',
    fix: (text) => text.replace(/(\w+)\s+—\s+(\()/g, '$1 — $2')
  }
};

// ============================================================================
// MEDIUM PRIORITY - Style & Consistency Issues
// ============================================================================

const MEDIUM_PRIORITY_PATTERNS = {
  // 1. Ellipsis at start of quote
  ellipsisAtQuoteStart: {
    pattern: /[""]\.\.\.[\s]/g,
    description: 'Do not start quote with ellipsis if material starts midsentence.',
    example: 'Wrong: "...the case"; Right: "[t]he case"',
    note: 'Requires context-aware checking'
  },

  // 2. Capital letter in parenthetical (should be lowercase)
  capitalInParenthetical: {
    pattern: /\(\s*[A-Z]/g,
    description: 'Parentheticals should start with lowercase unless proper noun.',
    example: 'Wrong: (Finding that...); Right: (finding that...)',
    fix: (text) => text.replace(/\(\s*([A-Z])/g, (match, letter) => {
      // Simple fix - may miss proper nouns
      return '(' + letter.toLowerCase();
    })
  },

  // 3. Missing "at" before page number in periodical
  missingAtPage: {
    pattern: /(\d+\s+[A-Z][\w\s]*)\s+(\d{4})\s+(\d+)/g,
    description: 'Missing "at" before page number in periodical citation.',
    example: 'Wrong: 23 Nat\'l L.J. (2020) 12; Right: 23 Nat\'l L.J., at 12 (2020)',
    note: 'Check format: Volume Name Year at Page'
  },

  // 4. Comma instead of period in citation sentence
  commaMissingSemicolon: {
    pattern: /(See|Accord|But see|Cf)\s+[^;]*\),\s+([A-Z](?:See|Accord|But|Cf))/g,
    description: 'Citations of same signal type should use semicolon, not comma.',
    example: 'Wrong: See X, But see Y; Right: See X; But see Y'
  },

  // 5. Mismatched quotation marks
  mismatchedQuotes: {
    pattern: /[""][^"]*'[^']*[""]|''[^']*"[^"]*''/g,
    description: 'Inconsistent quotation mark pairing.',
    example: 'Wrong: "...\' ...\'; Right: "...\' ...\'"'
  },

  // 6. Square bracket outside parenthetical context
  improperlySituatedBrackets: {
    pattern: /\[\s*[a-z][^[\]]*\s*\](?!\s*\))/g,
    description: 'Brackets should primarily appear within parentheticals.',
    note: 'May have false positives for other uses of brackets'
  },

  // 7. Question mark in title not preserved
  questionMarkInTitle: {
    pattern: /(Title:\s*[^?]*)\s*,/g,
    description: 'Question marks in titles must be preserved exactly as published.',
    example: 'Title: Subtitle? should keep the question mark'
  },

  // 8. Missing comma before "no." in periodical
  missingCommaBeforeNo: {
    pattern: /\d+\s+[A-Z][\w\s]*(?:no|number)\s+\d+/g,
    description: 'Comma required before issue number in periodicals.',
    example: 'Wrong: 23 Nat\'l L.J. no. 5; Right: 23 Nat\'l L.J., no. 5'
  },

  // 9. Colon vs dash in subtitle
  dashInsteadOfColonSubtitle: {
    pattern: /([A-Z][\w\s]*)\s+–\s+([A-Z][\w\s]*)/g,
    description: 'Subtitles should use colon, not dash or en-dash.',
    example: 'Wrong: Title – Subtitle; Right: Title: Subtitle',
    fix: (text) => text.replace(/([A-Z][\w\s]*)\s+–\s+([A-Z][\w\s]*)/g, '$1: $2')
  }
};

// ============================================================================
// LOW PRIORITY - Minor Style Preferences
// ============================================================================

const LOW_PRIORITY_PATTERNS = {
  // 1. Spacing in "U.S.C."
  usCSpacing: {
    pattern: /U\s*\.\s*S\s*\.\s*C\s*\./g,
    description: 'Correct spacing in U.S.C. abbreviation.',
    example: 'Should be: U.S.C. (with periods)',
    fix: (text) => text.replace(/U\s*\.\s*S\s*\.\s*C\s*\./g, 'U.S.C.')
  },

  // 2. Reporter abbreviation formatting
  reporterFormatting: {
    pattern: /(\d+)\s+([A-Z][\w\.\s]*)\s+(\d+)/g,
    description: 'Check reporter volume, name, and page formatting.',
    example: '410 U.S. 113 format should be consistent'
  },

  // 3. Supra/Infra references
  supraInfraFormatting: {
    pattern: /(?:supra|infra)\s+(?:note|at)\s+(\d+)/gi,
    description: 'Verify supra/infra citations format.',
    example: 'Should be: supra note 4 or supra, at 5'
  },

  // 4. Id. vs Ibid.
  idFormatting: {
    pattern: /\bId\b(?!\.)/g,
    description: 'Id. requires a period.',
    example: 'Wrong: Id; Right: Id.',
    fix: (text) => text.replace(/\bId\b(?!\.)/g, 'Id.')
  },

  // 5. Parenthetical length check
  longParenthetical: {
    pattern: /\([^)]{200,}\)/g,
    description: 'Parentheticals should be under 50 words (~300 characters).',
    example: 'Consider breaking into separate sentence if over 50 words'
  },

  // 6. Year formatting in citations
  yearInParentheses: {
    pattern: /([A-Z]\.S\.\s+\d+)\s+(\d{4})/g,
    description: 'Year should be in parentheses at end of citation.',
    example: 'Wrong: 410 U.S. 113 1973; Right: 410 U.S. 113 (1973)',
    fix: (text) => text.replace(/([A-Z]\.S\.\s+\d+)\s+(\d{4})/g, '$1 ($2)')
  }
};

// ============================================================================
// COMPOSITE PATTERNS - Multi-element checks
// ============================================================================

const COMPOSITE_PATTERNS = {
  // Full case citation format check
  caseCitationFormat: {
    pattern: /([A-Za-z\s]+v\.\s+[A-Za-z\s]+),\s+(\d+)\s+([A-Z]\.[\w\.]+)\s+(\d+)(?:\s*,?\s*(\d+))?\s+\(([^)]+)\)/,
    description: 'Verify complete case citation: Name, Vol. Reporter Page (Court Year)',
    components: {
      caseName: 1,
      volume: 2,
      reporter: 3,
      firstPage: 4,
      pinpoint: 5,
      courtYear: 6
    }
  },

  // Statute citation format
  statuteCitationFormat: {
    pattern: /(\d+)\s+(U\.S\.C\.(?:\s*\w+)?)\s+([§¶])\s+(\d+[\w\-\.]*)/,
    description: 'Verify statute format: Volume Code § Section',
    components: {
      volume: 1,
      code: 2,
      symbol: 3,
      section: 4
    }
  },

  // Periodical citation format
  periodicalCitationFormat: {
    pattern: /(\d+)\s+([A-Z][\w\'.\s]+?),\s+(?:no\.\s+(\d+),\s+)?at\s+(\d+)\s+\((\d{4})\)/,
    description: 'Verify periodical format: Vol. Name, [no. X,] at Page (Year)',
    components: {
      volume: 1,
      journal: 2,
      issueNum: 3,
      page: 4,
      year: 5
    }
  },

  // URL format check
  urlFormatting: {
    pattern: /(https?:\/\/[^\s)]+)(?:\s+\((?:last\s+visited\s+)?([^)]+)\))?/,
    description: 'Verify URL with optional date: http://...url... (last visited Date)',
    components: {
      url: 1,
      date: 2
    }
  }
};

// ============================================================================
// UTILITY FUNCTIONS FOR PATTERN MATCHING
// ============================================================================

/**
 * Find all matches with line numbers and context
 * @param {string} text - The text to search
 * @param {RegExp} pattern - The regex pattern
 * @param {number} contextLength - Characters before/after match
 * @returns {Array} Array of match objects with position and context
 */
function findPunctuationErrors(text, pattern, contextLength = 50) {
  const matches = [];
  let match;

  // Create a copy of the pattern with global flag
  const globalPattern = new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : pattern.flags + 'g');

  while ((match = globalPattern.exec(text)) !== null) {
    const lineNum = text.substring(0, match.index).split('\n').length;
    const start = Math.max(0, match.index - contextLength);
    const end = Math.min(text.length, match.index + match[0].length + contextLength);

    matches.push({
      index: match.index,
      line: lineNum,
      match: match[0],
      context: text.substring(start, end),
      fix: null // To be populated by fix function if available
    });
  }

  return matches;
}

/**
 * Apply all critical patterns to text and return errors
 * @param {string} text - The text to check
 * @returns {Array} Array of error objects
 */
function checkCriticalPunctuation(text) {
  const errors = [];

  for (const [key, patternObj] of Object.entries(CRITICAL_PATTERNS)) {
    const matches = findPunctuationErrors(text, patternObj.pattern);

    matches.forEach(match => {
      errors.push({
        priority: 'CRITICAL',
        type: key,
        description: patternObj.description,
        ...match
      });
    });
  }

  return errors;
}

/**
 * Generate a report of all punctuation issues
 * @param {string} text - The text to analyze
 * @returns {Object} Comprehensive error report
 */
function generatePunctuationReport(text) {
  const report = {
    timestamp: new Date().toISOString(),
    totalText: text.length,
    errors: {
      critical: [],
      high: [],
      medium: [],
      low: []
    },
    summary: {}
  };

  // Check all pattern levels
  for (const [key, patternObj] of Object.entries(CRITICAL_PATTERNS)) {
    report.errors.critical.push(...findPunctuationErrors(text, patternObj.pattern));
  }

  for (const [key, patternObj] of Object.entries(HIGH_PRIORITY_PATTERNS)) {
    report.errors.high.push(...findPunctuationErrors(text, patternObj.pattern));
  }

  for (const [key, patternObj] of Object.entries(MEDIUM_PRIORITY_PATTERNS)) {
    report.errors.medium.push(...findPunctuationErrors(text, patternObj.pattern));
  }

  for (const [key, patternObj] of Object.entries(LOW_PRIORITY_PATTERNS)) {
    report.errors.low.push(...findPunctuationErrors(text, patternObj.pattern));
  }

  // Generate summary
  report.summary = {
    criticalCount: report.errors.critical.length,
    highCount: report.errors.high.length,
    mediumCount: report.errors.medium.length,
    lowCount: report.errors.low.length,
    totalErrors: report.errors.critical.length +
                 report.errors.high.length +
                 report.errors.medium.length +
                 report.errors.low.length
  };

  return report;
}

// ============================================================================
// EXPORT FOR USE IN OTHER MODULES
// ============================================================================

module.exports = {
  CRITICAL_PATTERNS,
  HIGH_PRIORITY_PATTERNS,
  MEDIUM_PRIORITY_PATTERNS,
  LOW_PRIORITY_PATTERNS,
  COMPOSITE_PATTERNS,
  findPunctuationErrors,
  checkCriticalPunctuation,
  generatePunctuationReport
};
