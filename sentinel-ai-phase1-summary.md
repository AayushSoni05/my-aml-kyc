# Sentinel AI — Project Summary (End of Phase 1)

**Status:** Phase 1 CLOSED (agreed) — Phase 2 starts next session
**Repo:** github.com/AayushSoni05/my-aml-kyc
**Local path:** `C:\Users\Aayush\Desktop\Sentinal AI`

---

## What It Is

An AML/KYC compliance tool that screens individuals, sole proprietors, and
companies against sanctions, PEP, adverse media, and country risk sources,
using structured APIs plus web search for discovery, and precise mathematical
scoring (not LLM guesswork) to produce an auditable, explainable risk score.

---

## The Core Model

```
SEARCH (API + web search)
    -> SCORE each candidate (attribute-weighted formula)
    -> CLASSIFY (MATCH / POSSIBLE_MATCH / NO_MATCH)
    -> LLM reviews borderline cases, writes explanations
    -> COMBINE across sources (CRI formula)
    -> STORE (full audit trail)
```

### The Four Screens

| Screen | Search method |
|---|---|
| Sanctions | OpenSanctions API (primary) + web search (backup) |
| PEP | Same as sanctions |
| Adverse media | Web/news search + LLM reads and judges relevance |
| Country risk | Static table lookup (OFAC country programs, FATF lists, conflict zones, corruption index) — no search/LLM needed |

Screens run against **all countries/sources**, executed concurrently — not
just the customer's known countries.

---

## Scoring Formulas (Locked)

### 1. Candidate Match Score (per candidate, per source)

```
S = sum(score_i * weight_i) / sum(weight_i)
```

Only available attributes are included; weights renormalize accordingly.

| Attribute | Weight |
|---|---|
| Name | 0.35 |
| Identifier | 0.30 |
| Date of birth | 0.10 |
| Birth year | 0.05 |
| Country | 0.05 |
| Entity type | 0.05 |
| Gender | 0.10 |

**Classification:**
- `S >= 0.85` → MATCH
- `0.65 <= S < 0.85` → POSSIBLE_MATCH
- `S < 0.65` → NO_MATCH

### 2. CRI — Composite Risk Index (combines across sources)

```
CRI = [1 - product(1 - (S_i * W_i))] * 100
```

Treats each source as an independent probability of a true hit. More
independent hits push CRI higher rather than diluting it (this is NOT an
average or max — it's a probabilistic OR combination). This becomes the
overall risk score (0-100).

**LLM's role:** reviews borderline/POSSIBLE_MATCH cases and writes
plain-English explanations. It does not calculate scores and does not decide
matches alone — the formulas decide, the LLM explains and sanity-checks.

---

## Data Model (core tables, finalized in Phase 2)

- **customers** — individuals, sole proprietors, companies (with type field)
- **company_members** — links a company to its individually-screened
  members/officers
- **sanction_sources** — registry of sources (API-based and/or discovered),
  country, weight
- **screening_results** — one row per candidate per source: matched_name,
  attribute_scores (JSON), match_score (S), status, confidence, explanation,
  found_via (api/web_search); full history kept
- **overall_scores** — CRI value, risk band, per-source scores used, weights
  used, timestamp
- **country_risk** — static table: country, risk_level, score, reason,
  last_reviewed
- **investigations** — analyst case notes, status
- **kyc_submissions** — document data, verification status

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| ORM | SQLModel |
| Database | SQLite (build) → PostgreSQL (production, swapped later) |
| LLM | Claude API — explains and reviews, never decides alone |
| Sanctions/PEP data | OpenSanctions API + web search backup |
| Adverse media | Web/news search |
| Name matching | Attribute-weighted formula (above); fuzzy string matching for the Name attribute specifically |
| Frontend | Simple HTML first → React later |
| Deployment | Docker |

---

## Build Order

| Phase | Focus | Status |
|---|---|---|
| 0 | Environment: Python, Git, VS Code, venv | Done |
| 1 | Planning: product, features, stack, scoring formulas | Done (agreed) |
| 2 | Database: all core tables, SQLite | Next |
| 3 | API: FastAPI endpoints over the database | Pending |
| 4 | Engine: search + scoring pipeline, KYC, company/member roll-up | Pending |
| 5 | Frontend + remaining backend + optimization | Pending |
| 6 | Docker + deployment | Pending |

---

## Key Decisions Log

1. AML monitoring + KYC/sanctions screening — one combined product
2. Synthetic/demo data only, no real customer data
3. Screen **all countries/sources**, run concurrently — not just customer's
   known countries
4. Matching uses the **attribute-weighted S formula**, not simple string
   equality
5. Overall risk uses the **CRI complement-product formula**, not
   average/max
6. LLM explains and reviews borderline cases; formulas and rules decide,
   never the LLM alone
7. Every result stores full history, matched name, source, confidence, and
   discovery method — fully auditable
8. Companies screened as an entity + each member individually, then rolled
   up
9. Python + FastAPI + SQLModel + SQLite → Postgres later

---

## Open Items Carried Into Phase 2/4

1. Source weights (`W_i` in the CRI formula) — need actual values, or start
   equal-weighted and tune later
2. Attribute-scoring functions (how Name similarity, DOB match, etc. are
   each scored 0-1) — need definitions
3. OpenSanctions API — pricing/rate limits not yet researched
4. Fuzzy-match thresholds for the Name attribute specifically — defaults
   suggested 60/85 (or aligned to the 0.65/0.85 S-thresholds)

---

## Handoff Template (paste into a new chat if needed)

```
PROJECT: Sentinel AI (repo: github.com/AayushSoni05/my-aml-kyc)
LOCAL PATH: C:\Users\Aayush\Desktop\Sentinal AI
PHASE: 1 complete (agreed). Phase 2 (database) starts next.
[See full document for formulas, schema, stack, and decisions log]
NEXT STEP: Phase 2 Step 1 — folder structure, install SQLModel,
           build Customer table with a test script
```
