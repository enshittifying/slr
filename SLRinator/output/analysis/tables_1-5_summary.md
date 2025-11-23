# Bluebook Tables T1-T5: Comprehensive Summary

**Source:** `/home/user/slr/SLRinator/config/rules/Bluebook.json`
**Generated:** 2025-11-23
**Purpose:** Citation validation for court names, jurisdictions, and international citations

---

## Table of Contents

1. [Table T1: United States Jurisdictions](#table-t1-united-states-jurisdictions)
2. [Table T2: Foreign Jurisdictions](#table-t2-foreign-jurisdictions)
3. [Table T3: Intergovernmental Organizations](#table-t3-intergovernmental-organizations)
4. [Table T4: Treaty Sources](#table-t4-treaty-sources)
5. [Table T5: Arbitral Reporters](#table-t5-arbitral-reporters)
6. [Cross-Table Validation Rules](#cross-table-validation-rules)
7. [Quick Reference: Common Errors](#quick-reference-common-errors)

---

## Table T1: United States Jurisdictions

### Overview
Table T1 covers **all U.S. federal and state jurisdictions** including:
- Federal judicial and legislative materials
- Federal administrative and executive materials
- All 50 states
- District of Columbia
- U.S. territories (Puerto Rico, Guam, Virgin Islands, etc.)

**Total Jurisdictions:** 58 (50 states + DC + 7 territories)

### Federal Courts

#### Supreme Court (U.S.)
- **Preferred Reporter:** `U.S.`
- **Other Reporters:** `S. Ct.`, `L. Ed.`, `U.S.L.W.`
- **Format:** `[Volume] U.S. [Page] ([Year])`
- **Example:** `Brown v. Board of Education, 347 U.S. 483 (1954)`
- **Common Errors:**
  - Using `US` instead of `U.S.` (missing periods)
  - Using unofficial reporter when U.S. is available
  - Missing year in parentheses

#### Courts of Appeals (Circuit Courts)
- **Reporters:** `F.`, `F.2d`, `F.3d`, `F. App'x`
- **Format:** `[Volume] F.3d [Page] ([Circuit] Cir. [Year])`
- **Example:** `United States v. Smith, 123 F.3d 456 (5th Cir. 1997)`
- **Common Errors:**
  - Using `F.2nd` or `F.3rd` instead of `F.2d` or `F.3d`
  - Missing circuit designation
  - Using `F. Appx` instead of `F. App'x` (apostrophe required)
  - Incorrectly using `2nd Cir.` instead of `2d Cir.`

#### District Courts
- **Reporters:** `F. Supp.`, `F. Supp. 2d`, `F. Supp. 3d`, `F.R.D.`, `B.R.`
- **Format:** `[Volume] F. Supp. 2d [Page] ([District] [Year])`
- **Example:** `Smith v. Jones, 789 F. Supp. 2d 123 (S.D.N.Y. 2011)`
- **Common Errors:**
  - Omitting space: `F.Supp.` instead of `F. Supp.`
  - Using `F. Supp. 2nd` instead of `F. Supp. 2d`
  - Missing district designation (e.g., `S.D.N.Y.`)

#### Specialized Federal Courts
- **Federal Circuit:** `F.3d` with `(Fed. Cir. [Year])`
- **Court of Federal Claims:** `Fed. Cl.` (post-1992)
- **Court of International Trade:** `Ct. Int'l Trade` (note apostrophe)

### Federal Legislation & Administration

- **United States Code:** `U.S.C.` → Format: `[Title] U.S.C. § [Section]`
- **Statutes at Large:** `Stat.` → Format: `Pub. L. No. XXX-YYY, [Vol] Stat. [Page]`
- **Code of Federal Regulations:** `C.F.R.` → Format: `[Title] C.F.R. § [Section] ([Year])`
- **Federal Register:** `Fed. Reg.` → Format: `[Vol] Fed. Reg. [Page] (Month Day, Year)`

### State Courts: Regional Reporters

States use **regional reporters** and must include state/court designation in parenthetical:

| Reporter | Regions | Format Note |
|----------|---------|-------------|
| **P.**, **P.2d**, **P.3d** | Pacific (AK, AZ, CA, CO, HI, ID, KS, MT, NV, NM, OK, OR, UT, WA, WY) | Must specify state |
| **A.**, **A.2d**, **A.3d** | Atlantic (CT, DE, ME, MD, NH, NJ, PA, RI, VT, D.C.) | Must specify state |
| **N.E.**, **N.E.2d** | North Eastern (IL, IN, MA, NY, OH) | Must specify state |
| **N.W.**, **N.W.2d** | North Western (IA, MI, MN, NE, ND, SD, WI) | Must specify state |
| **S.E.**, **S.E.2d** | South Eastern (GA, NC, SC, VA, WV) | Must specify state |
| **S.W.**, **S.W.2d**, **S.W.3d** | South Western (AR, KY, MO, TN, TX) | Must specify state |
| **So.**, **So. 2d**, **So. 3d** | Southern (AL, FL, LA, MS) | Must specify state |

### State Court Naming Variations

**Important:** States use different names for their highest courts:
- **Court of Appeals:** Maryland, New York (highest court in these states!)
- **Supreme Judicial Court:** Maine, Massachusetts
- **Supreme Court of Appeals:** West Virginia
- **Supreme Court:** Most other states

**Intermediate Appellate Courts:**
- Most states: "Court of Appeals"
- California: "Court of Appeal" (no 's')
- Pennsylvania: "Superior Court" and "Commonwealth Court" (two separate intermediate courts)
- New York: "Appellate Division"

### State Statutory Compilations (Selected Examples)

- **California:** `Cal. [Code type]` (e.g., `Cal. Civ. Code`, `Cal. Penal Code`)
- **Georgia:** `O.C.G.A.` (Official Code of Georgia Annotated)
- **New York:** `N.Y. Consol. Laws`
- **Texas:** `Tex. Code Ann.`

### U.S. Territories

- **Puerto Rico:** `P.R.` (with periods)
- **Virgin Islands:** `V.I.` (with periods)
- **Guam:** `Guam` (not abbreviated)
- **Northern Mariana Islands:** `N. Mar. I.`
- **American Samoa:** `Am. Samoa` (not `A.S.`)
- **Navajo Nation:** `Navajo Nation` (not abbreviated)

---

## Table T2: Foreign Jurisdictions

### Overview
Table T2 provides citation formats for **non-U.S. jurisdictions worldwide**. The full table is available online at the Bluebook website.

### Key Points
- **Each country has unique citation rules** - do not apply U.S. format to foreign cases
- **Consult country-specific requirements** in online Table T2
- **Common foreign jurisdictions:** United Kingdom, Canada, Australia, European Union member states, etc.

### Example Formats (by Country)

#### United Kingdom
- **Format:** `[Case Name] [Year] [Court] [Number]`
- **Example:** `R v. Smith [2020] UKSC 15`
- **Courts:** UKSC (Supreme Court), UKHL (House of Lords), EWCA (Court of Appeal), EWHC (High Court)

#### Canada
- **Format:** `[Case Name], [Year] [Volume] [Reporter] [Page]`
- **Example:** `R. v. Jones, [2020] 1 S.C.R. 123`
- **Supreme Court Reporter:** `S.C.R.`

#### Australia
- **Format:** `[Case Name] ([Year]) [Volume] [Reporter] [Page]`
- **Example:** `Smith v. Jones (2020) 264 CLR 123`
- **High Court Reporter:** `CLR` (Commonwealth Law Reports)

#### European Union
- See Table T3.3 for EU Court citations
- Format varies by court and time period

### Common Errors with Foreign Citations
- Applying U.S. citation format to foreign cases
- Not consulting country-specific rules
- Incorrect abbreviations for foreign courts
- Missing required elements (e.g., case numbers, court designations)

---

## Table T3: Intergovernmental Organizations

### Overview
Citations for **international and intergovernmental organization materials**, including:
- United Nations and specialized agencies
- International courts and tribunals
- Regional organizations (EU, OAS, etc.)

### T3.1 United Nations

#### UN Documents
- **Format:** `U.N. Doc. [Symbol] (Date)`
- **Example:** `G.A. Res. 70/1, U.N. Doc. A/RES/70/1 (Sept. 25, 2015)`
- **Common Errors:** Missing `Doc.` or incorrect document symbol format

#### Official Records
- **General Assembly:** `U.N. GAOR`
- **Security Council:** `U.N. SCOR`
- **Economic and Social Council:** `U.N. ESCOR`
- **Trusteeship Council:** `U.N. TCOR` (historical - suspended 1994)

#### International Court of Justice (I.C.J.)
- **Judgments/Opinions:** `[Year] I.C.J. [Page]`
- **Example:** `Corfu Channel (U.K. v. Alb.), 1949 I.C.J. 4 (Apr. 9)`
- **Pleadings:** `[Year] I.C.J. Pleadings [Page]`
- **Acts & Documents:** `[Year] I.C.J. Acts & Docs. [Page]`
- **Common Errors:** Using `ICJ` without periods, missing year

#### UN Treaty Series
- **Format:** `[Volume] U.N.T.S. [Page]`
- **Example:** `Vienna Convention on the Law of Treaties, May 23, 1969, 1155 U.N.T.S. 331`
- **Common Errors:** Using `UNTS` without periods

### T3.2 League of Nations (Historical)

#### Permanent Court of International Justice (P.C.I.J.)
- **Format:** `[Year] P.C.I.J. (ser. [Letter]) No. [X]`
- **Example:** `S.S. Lotus (Fr. v. Turk.), 1927 P.C.I.J. (ser. A) No. 10 (Sept. 7)`
- **Series:** A (Judgments), B (Advisory Opinions), A/B (combined), C, D, E, F
- **Note:** Historical only - P.C.I.J. dissolved 1946

#### League of Nations Treaty Series
- **Format:** `[Volume] L.N.T.S. [Page] ([Year])`
- **Coverage:** 1920-1946

### T3.3 European Union

#### EU Courts (C.J.E.U. & General Court)
- **European Court Reports (through 2011):** `[Year] E.C.R. [Page]`
- **Example:** `Case C-26/62, Van Gend en Loos, 1963 E.C.R. 1`
- **Post-2011:** Cite to ECLI or official website (E.C.R. ceased publication)
- **Unofficial Reporters:** `C.M.L.R.` (Common Market Law Reports)

#### EU Legislative Acts - Official Journal
- **Format:** `[Year] O.J. ([L/C]) [Issue] [Page]`
- **Example:** `Council Regulation 1234/2020, 2020 O.J. (L 280) 5`
- **Series:**
  - **L Series:** Legislation
  - **C Series:** Information and Notices
- **Common Errors:** Missing series designation, incorrect format

### T3.4 European Commission of Human Rights
- **Abbreviation:** `Eur. Comm'n H.R.`
- **Note:** Abolished 1998; cases now heard by European Court of Human Rights
- **Format:** `[Volume] Eur. Comm'n H.R. Dec. & Rep. [Page]`

### T3.5 European Court of Human Rights
- **Abbreviation:** `Eur. Ct. H.R.`
- **Format:** `[Case Name] v. [Country], App. No. [XXXXX/XX], Eur. Ct. H.R. ([Year])`
- **Example:** `Pretty v. United Kingdom, App. No. 2346/02, Eur. Ct. H.R. (2002)`
- **Must Include:** Application number
- **Common Errors:** Missing application number, incorrect abbreviation

### T3.6 Inter-American Commission on Human Rights
- **Abbreviation:** `Inter-Am. Comm'n H.R.`
- **Format:** `Case [No.], Report No. [XX/YY], Inter-Am. Comm'n H.R., [OAS Doc.] ([Year])`

### T3.7 Inter-American Court of Human Rights
- **Abbreviation:** `Inter-Am. Ct. H.R.`
- **Series:**
  - **Series A:** Judgments and Opinions (pre-2000)
  - **Series C:** Decisions and Judgments (current)
- **Format:** `[Case Name], Inter-Am. Ct. H.R. (ser. C) No. [XXX], ¶ [para] (Month Day, Year)`
- **Example:** `Velásquez Rodríguez Case, Inter-Am. Ct. H.R. (ser. A) No. 1, ¶ 164 (July 29, 1988)`

### T3.8 International Tribunal for the Law of the Sea
- **Abbreviation:** `ITLOS`
- **Format:** `[Case Name], Case No. [X], [Year] ITLOS Rep. [Page] (Month Day)`
- **Example:** `The M/V 'Saiga' (No. 2) Case (St. Vincent v. Guinea), Case No. 2, 1999 ITLOS Rep. 10 (July 1)`

### T3.9 Other Intergovernmental Organizations
Abbreviations for major IGOs:
- **IAEA:** International Atomic Energy Agency
- **ICSID:** International Centre for Settlement of Investment Disputes
- **ICAO:** International Civil Aviation Organization
- **FAO:** Food and Agriculture Organization
- **IPCC:** Intergovernmental Panel on Climate Change
- **INTERPOL:** International Criminal Police Organization

**General Rule:** Use organization's standard abbreviation and cite to official documents with document numbers and dates.

### Common Errors (All T3)
- Missing periods in abbreviations (e.g., `UN` instead of `U.N.`)
- Incorrect document symbol formats
- Not including required date information
- Confusing different court reporters (I.C.J. vs. P.C.I.J.)
- Missing series designations
- Incorrect spacing in multi-part abbreviations

---

## Table T4: Treaty Sources

### Overview
Citation formats for **international treaties and agreements** with preference hierarchy:
1. **Official U.S. sources** (when U.S. is a party)
2. **Intergovernmental sources** (multilateral treaties)
3. **Unofficial sources** (when official unavailable)

### T4.1 Official U.S. Treaty Sources

#### United States Treaties and Other International Agreements
- **Abbreviation:** `U.S.T.`
- **Coverage:** 1950-1984 (publication ceased)
- **Format:** `[Treaty Name], [Parties], Month Day, Year, [Vol] U.S.T. [Page]`
- **Example:** `Treaty of Friendship, U.S.-Japan, Sept. 8, 1951, 3 U.S.T. 3169`
- **Common Error:** Using U.S.T. for post-1984 treaties (unavailable)

#### Statutes at Large (Treaties)
- **Abbreviation:** `Stat.`
- **Coverage:** Treaties prior to 1950
- **Format:** `[Treaty Name], Month Day, Year, [Vol] Stat. [Page]`
- **Example:** `Treaty of Paris, U.S.-Gr. Brit., Sept. 3, 1783, 8 Stat. 80`

#### Treaties and Other International Acts Series
- **Abbreviation:** `T.I.A.S.`
- **Coverage:** 1945-present
- **Format:** `[Treaty Name], [Parties], Month Day, Year, T.I.A.S. No. [XXXX]`
- **Example:** `Agreement on Trade Relations, U.S.-China, July 7, 1979, T.I.A.S. No. 9630`
- **Common Error:** Missing `No.` in citation

#### Treaty Series / Executive Agreement Series
- **Treaty Series (T.S.):** 1778-1945
- **Executive Agreement Series (E.A.S.):** 1922-1945
- **Format:** `T.S. No. [X]` or `E.A.S. No. [X]`

#### Senate Treaty Documents
- **Post-1981:** `S. Treaty Doc. No. [Congress-Number]`
- **Pre-1981:** `S. Exec. Doc. No. [Letter-Number]`
- **Example:** `Convention on Climate Change, S. Treaty Doc. No. 102-38 (1992)`
- **Common Error:** Not including Congress number

### T4.2 Intergovernmental Treaty Sources

#### United Nations Treaty Series
- **Abbreviation:** `U.N.T.S.`
- **Format:** `[Treaty Name], Month Day, Year, [Vol] U.N.T.S. [Page]`
- **Example:** `Vienna Convention on the Law of Treaties, May 23, 1969, 1155 U.N.T.S. 331`
- **Note:** Primary source for multilateral treaties
- **Common Errors:** Using `UNTS` without periods, missing volume/page

#### Other Intergovernmental Sources
- **League of Nations Treaty Series:** `L.N.T.S.` (1920-1946, historical)
- **European Treaty Series:** `E.T.S. No. [X]`
- **Council of Europe Treaty Series:** `C.E.T.S. No. [X]`
- **OAS Treaty Series:** `O.A.S.T.S. No. [X]`
- **Pan-American Treaty Series:** `Pan-Am. T.S.`

### T4.3 Unofficial Treaty Sources

**Use only when official sources unavailable**

- **International Legal Materials:** `I.L.M.` → `[Vol] I.L.M. [Page]`
- **Parry's Consolidated Treaty Series:** `Consol. T.S.` (historical, 1648-1919)
- **Bevans:** Compilation of U.S. treaties 1776-1949
- **Hein's Treaties:** `Hein's No. KAV[XXXX]`
- **LEXIS Treaties:** Cite with database identifier

### General Treaty Citation Format

**Essential Elements:**
1. Treaty name (**not italicized**)
2. Parties (if bilateral) or indication of multilateral
3. Signing date (Month Day, Year)
4. Citation to source(s)
5. Ratification/entry into force date (if relevant)

**Example:** `Vienna Convention on the Law of Treaties, May 23, 1969, 1155 U.N.T.S. 331`

### Common Errors (All T4)
- **Italicizing treaty names** (should NOT be italicized - unlike case names)
- Using unofficial source when official is available
- Missing periods in abbreviations
- Not identifying parties for bilateral treaties
- Omitting signing date
- Using wrong source for time period

---

## Table T5: Arbitral Reporters

### Overview
Citation formats for **international arbitration decisions and awards** from various tribunals and reporting services.

### Major Arbitral Reporters

#### ICSID (Investment Disputes)
- **ICSID Reports:** `ICSID Rep.` (official reporter)
  - **Format:** `[Case Name], ICSID Case No. ARB/XX/X, [Vol] ICSID Rep. [Page] ([Year])`
  - **Example:** `Compañía de Aguas del Aconquija S.A. v. Argentine Republic, ICSID Case No. ARB/97/3, 5 ICSID Rep. 3 (2000)`
- **ICSID Review:** `ICSID Rev.` (journal, not official reporter - use only if unavailable in ICSID Rep.)
- **Common Error:** Confusing ICSID Rep. with ICSID Rev.

#### Hague Court Reports
- **First Series:** `Hague Ct. Rep. (Scott)`
- **Second Series:** `Hague Ct. Rep. 2d (Scott)`
- **Note:** Must include `(Scott)` designation (editor's name)
- **Example:** `The Pious Fund Case (U.S. v. Mex.), Hague Ct. Rep. (Scott) 1 (1902)`

#### UN Reports of International Arbitral Awards
- **Abbreviation:** `R.I.A.A.`
- **Format:** `[Case Name], [Vol] R.I.A.A. [Page] (Tribunal, Year)`
- **Example:** `Island of Palmas Case (Neth. v. U.S.), 2 R.I.A.A. 829 (Perm. Ct. Arb. 1928)`
- **Common Errors:** Using `RIAA` without periods, missing tribunal designation

#### ITLOS Reports
- **Abbreviation:** `ITLOS Rep.`
- **Format:** `[Case Name], Case No. [X], [Year] ITLOS Rep. [Page] (Month Day)`
- **Example:** `The M/V 'Saiga' (No. 2) Case, Case No. 2, 1999 ITLOS Rep. 10 (July 1)`
- **Note:** Also covered in Table T3.8

#### ICC Arbitration
- **Abbreviation:** `Int'l Comm. Arb.`
- **Format:** `ICC Case No. [XXXX], [Award Type], Int'l Comm. Arb. ([Year])`
- **Example:** `ICC Case No. 1234, Final Award, Int'l Comm. Arb. (1990)`
- **Common Error:** Missing apostrophe in `Int'l`

#### Permanent Court of Arbitration
- **Abbreviation:** `PCA Case Repository`
- **Format:** `[Case Name], PCA Case No. [XXXX-XX], [Award/Decision] (Date)`
- **Example:** `Abyei Arbitration (Sudan v. SPLM/A), PCA Case No. 2008-7, Final Award (July 22, 2009)`
- **Note:** Specify arbitration rules (UNCITRAL, bilateral treaty, etc.)

#### Other Arbitral Sources
- **World Arbitration Reporter:** `World Arb. Rep. (Issue No.)`
- **Arbitration Materials:** `Arb. Mat'l`
- **ITA Investment Treaty Cases:** `ITA Inv. Treaty Cases` (online resource)

### General Arbitration Citation Elements
1. Case name (parties)
2. Case number (if applicable)
3. Decision type (Award, Interim Award, Decision on Jurisdiction, etc.)
4. Citation to reporter or repository
5. Tribunal/arbitration body
6. Date of decision

### Unpublished Awards
For unpublished awards, cite to:
- Party materials
- Publicly available repository (PCA, ITA)
- Include descriptive parenthetical with case number, tribunal, and date

### Common Errors (All T5)
- Not distinguishing ICSID Rep. (reporter) from ICSID Rev. (journal)
- Missing case numbers for institutional arbitrations
- Omitting tribunal designation
- Not specifying type of decision (Award vs. Interim vs. Jurisdictional)
- Using unofficial sources when official reporter available
- Missing periods in abbreviations
- Not including date of award

---

## Cross-Table Validation Rules

### Materials Appearing in Multiple Tables

Some international materials appear in multiple tables:

| Material | Primary Table | Also In | Note |
|----------|---------------|---------|------|
| **ITLOS** | T3.8 (IGO) | T5 (Arbitral) | Same citation format |
| **I.C.J.** | T3.1 (UN) | - | Part of UN system |
| **U.N.T.S.** | T3.1 (UN) | T4 (Treaties) | Primary treaty source |
| **ICSID** | T3.9 (IGO) | T5 (Arbitral) | Both organizational info and case citations |

### Citation Hierarchy by Material Type

#### Courts and Tribunals
1. **Official reporter** (when available)
2. **Regional/unofficial reporters** (secondary)
3. **Online repositories** (when print unavailable)

#### Treaties
1. **Official national source** (e.g., U.S.T., T.I.A.S.)
2. **Intergovernmental source** (e.g., U.N.T.S.)
3. **Unofficial source** (e.g., I.L.M., electronic databases)

#### Arbitral Awards
1. **Official arbitral reporter** (e.g., ICSID Rep., R.I.A.A.)
2. **Compilations** (e.g., Hague Ct. Rep.)
3. **Repositories** (e.g., PCA Case Repository, ITA)

---

## Quick Reference: Common Errors

### Abbreviation Errors

| ❌ Incorrect | ✅ Correct | Note |
|--------------|-----------|------|
| US | U.S. | Missing periods |
| F.2nd | F.2d | Use 'd' not 'nd' |
| F.3rd | F.3d | Use 'd' not 'rd' |
| F.Supp. | F. Supp. | Missing space after F. |
| So.2d | So. 2d | Missing space before series |
| ICJ | I.C.J. | Missing periods |
| UN | U.N. | Missing periods |
| UNTS | U.N.T.S. | Missing periods |
| ICSID | I.C.S.I.D. or ICSID Rep. | Context-dependent |
| Int'l Trade | Int'l Trade | ✅ Apostrophe correct |
| DC | D.C. | Missing periods |

### Series Number Abbreviations

| Series | ✅ Correct | ❌ Incorrect |
|--------|-----------|--------------|
| Second | 2d | 2nd, 2D, II |
| Third | 3d | 3rd, 3D, III |
| Fourth | 4th | 4d, IV |
| Fifth+ | 5th, 6th, etc. | - |

**Rule:** Only 2d and 3d use 'd'; all others use 'th'

### Regional Reporters - Spacing

| ✅ Correct | ❌ Incorrect |
|-----------|--------------|
| F. Supp. | F.Supp., F.Supp |
| S.W.2d | S.W.2d (no space), SW2d |
| N.E.2d | N.E.2d, NE2d |
| So. 2d | So.2d, So2d |

**Rule:** Space after each period; space before series number for some reporters

### Parenthetical Requirements

#### Federal Cases
- **Supreme Court:** `([Year])`
- **Circuit Courts:** `([Circuit] Cir. [Year])` → `(5th Cir. 1997)`
- **District Courts:** `([District] [Year])` → `(S.D.N.Y. 2011)`
- **Federal Circuit:** `(Fed. Cir. [Year])`

#### State Cases (using regional reporters)
- **Format:** `([State Court] [Year])` → `(Ala. 1995)`, `(Cal. Ct. App. 2000)`
- **Must include:** State abbreviation + court designation (if not highest court) + year

### Treaty vs. Case Name Formatting

| Type | Formatting | Example |
|------|------------|---------|
| **Case Names** | *Italicized* or underlined | *Brown v. Board of Education* |
| **Treaty Names** | **NOT** italicized | Vienna Convention on the Law of Treaties |
| **Statutory Names** | **NOT** italicized | Civil Rights Act of 1964 |

### Citation Preference Order

**Always prefer:**
1. **Official sources** over unofficial
2. **Print reporters** over online (when both available)
3. **Preferred reporters** over alternative reporters (per T1)
4. **Table abbreviations** exactly as shown

---

## Validation Checklists

### ✅ Federal Case Citation Checklist
- [ ] Reporter abbreviation has proper periods and spacing
- [ ] Series uses `2d` and `3d` (not `2nd` or `3rd`)
- [ ] Volume and page numbers present
- [ ] Parenthetical includes court (if not Supreme Court) and year
- [ ] Circuit or district properly designated
- [ ] Case name italicized

### ✅ State Case Citation Checklist
- [ ] Regional reporter properly abbreviated
- [ ] State abbreviation matches Table T1 exactly
- [ ] Court designation included (if not highest court)
- [ ] Year in parentheses
- [ ] Proper spacing in reporter abbreviation

### ✅ Statutory Citation Checklist
- [ ] Code abbreviation matches table (U.S.C., C.F.R., etc.)
- [ ] Section symbol (§) present for codes
- [ ] Title/volume number included
- [ ] Year in parentheses (for codes)
- [ ] Not italicized

### ✅ Treaty Citation Checklist
- [ ] Treaty name NOT italicized
- [ ] Parties identified (if bilateral)
- [ ] Complete date (Month Day, Year)
- [ ] Appropriate source for time period
- [ ] Abbreviation has periods (U.N.T.S., T.I.A.S., etc.)
- [ ] Volume and page or series number included

### ✅ International Organization Citation Checklist
- [ ] Organization abbreviation has periods (U.N., I.C.J., etc.)
- [ ] Document symbol or case number correct format
- [ ] Series designation included (if applicable)
- [ ] Complete date information
- [ ] All required elements present

### ✅ Arbitral Award Citation Checklist
- [ ] Case number included (if institutional)
- [ ] Award type specified (Final Award, Interim Award, etc.)
- [ ] Reporter abbreviation correct (ICSID Rep., R.I.A.A., etc.)
- [ ] Tribunal identified
- [ ] Date of award included
- [ ] Not using journal (ICSID Rev.) when reporter (ICSID Rep.) available

---

## GPT Validation Prompts

### For All Citations
```
Analyze this legal citation for Bluebook compliance:
1. Check abbreviations for proper periods and spacing
2. Verify series numbers use '2d' and '3d' not '2nd' or '3rd'
3. Confirm all required elements present (volume, page, year, etc.)
4. Validate court/jurisdiction designation in parenthetical
5. Check italicization (cases yes, treaties/statutes no)
6. Verify abbreviation matches exact Table format
7. Confirm using preferred/official source when available
```

### For U.S. Case Citations (T1)
```
Validate this U.S. case citation:
1. Reporter: Is abbreviation correct with proper spacing? (F. Supp. not F.Supp.)
2. Series: Using '2d'/'3d' not '2nd'/'3rd'?
3. Court: Is court designation required and correct?
4. Circuit/District: Properly abbreviated? (5th Cir., S.D.N.Y.)
5. Year: Present in parenthetical?
6. Case name: Italicized?
7. State cases: Does state appear in parenthetical with regional reporter?
```

### For Treaties (T4)
```
Validate this treaty citation:
1. Treaty name: NOT italicized?
2. Parties: Identified for bilateral treaties?
3. Date: Complete format (Month Day, Year)?
4. Source: Appropriate for time period? (U.S.T. only 1950-1984, T.I.A.S. 1945+)
5. Abbreviation: Has periods? (U.N.T.S., T.I.A.S.)
6. Citation hierarchy: Using official before unofficial?
```

### For International Organizations (T3)
```
Validate this international organization citation:
1. Organization: Abbreviation has periods? (U.N., I.C.J.)
2. Document: Symbol/case number in correct format?
3. Series: Designation included if required?
4. Date: Complete and properly formatted?
5. Court/tribunal: Properly identified?
6. Reporter: Using official when available?
```

### For Arbitral Awards (T5)
```
Validate this arbitral award citation:
1. Case number: Included for institutional arbitrations?
2. Award type: Specified? (Final Award, Interim Award, Jurisdictional Decision)
3. Reporter: Correct abbreviation? (ICSID Rep. not ICSID Rev. when available)
4. Tribunal: Identified in citation or parenthetical?
5. Date: Award date included?
6. Format: All periods present in abbreviations?
```

---

## Summary Statistics

### Table Coverage
- **T1:** 58 U.S. jurisdictions (50 states + DC + 7 territories)
- **T2:** All foreign jurisdictions (available online)
- **T3:** 9+ subsections covering major international organizations
- **T4:** 3 subsections covering official, intergovernmental, and unofficial treaty sources
- **T5:** 10+ arbitral reporters and repositories

### Key Validation Points (All Tables)
1. ✅ All abbreviations must have proper periods and spacing
2. ✅ Series numbers: use `2d` and `3d` not `2nd` or `3rd`
3. ✅ Regional reporters require state/court designation in parenthetical
4. ✅ Year must be included in parenthetical for case citations
5. ✅ Treaty names are NOT italicized; case names ARE italicized
6. ✅ Prefer official/primary sources over unofficial/secondary
7. ✅ State abbreviations must exactly match Table T1
8. ✅ International citations require organization-specific formatting per T3-T5

---

## Additional Resources

### For Implementation
- **Regex Patterns:** See JSON analysis file for validation regex patterns by citation type
- **GPT Prompts:** Detailed prompts provided for each citation type in JSON file
- **Error Detection:** Common error lists provided for each table and citation type

### Recommended Validation Workflow
1. **Identify citation type** (case, statute, treaty, international)
2. **Determine jurisdiction** (federal, state, foreign, international)
3. **Select appropriate table** (T1-T5)
4. **Check abbreviation** against table
5. **Verify required elements** using checklists above
6. **Apply GPT validation prompt** for comprehensive check
7. **Cross-reference** if material appears in multiple tables

---

**End of Summary**

For detailed JSON structure with regex patterns, complete error lists, and specific GPT prompts for each jurisdiction and citation type, see:
`/home/user/slr/SLRinator/output/analysis/tables_1-5_analysis.json`
