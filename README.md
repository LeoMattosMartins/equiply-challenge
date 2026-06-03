# Equiply Data Enrichment Portal

Equiply is a hospital equipment enrichment dashboard and CLI. It cleans messy inventory CSVs, standardizes metadata, and adds:

1. **Device type**: Defibrillator, Infusion Pump, Ventilator, and similar categories.
2. **Manufacture date**: Parsed from manufacturer serial-number rules, then checked against company and model date bounds.

VIDEO: https://www.youtube.com/watch?v=Ar72ZvwpCqo

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Enrichment Pipeline](#enrichment-pipeline)
- [Manufacturer Serial Number Sources](#manufacturer-serial-number-sources)
- [WCAG 2.2 AA Compliance](#wcag-22-aa-compliance)
- [Setup](#setup)
- [Usage](#usage)
- [Testing](#testing)
- [File Structure](#file-structure)
- [Future Improvements](#future-improvements)

## Project Overview

Hospital inventory exports often include:

- **Typos**: `M1722A` vs `M1722 A`, `American Diagnostcs`, and similar variants.
- **Missing fields**: Blank manufacturers, unknown device types, and serials without dates.
- **Different serial formats**: GE uses product/year/week fields, ZOLL uses product/date/sequence fields, and Welch Allyn/Hillrom models use model-specific label formats.

Equiply combines local parsers for 25+ medical manufacturers, dataset-level correction rules, and web/LLM fallback resolution. Local parsers handle known formats first; fallback logic is used only when parsing fails or metadata validation rejects the date.

## Key Features

- **Registry-based parser engine**: Manufacturer parsers are registered functions, avoiding long conditional chains.
- **Dataset self-healing**: Learns common serial prefixes and model spellings, applies outlier fixes, and writes `formatting_corrections.txt` and `probable_typos.txt`.
- **Web and LLM fallback**: Uses DuckDuckGo results plus OpenAI consensus prompts for unknown formats.
- **Thread-safe caches**: Locked JSON caches avoid repeated search and LLM calls.
- **Accessible dashboard**: Semantic HTML, keyboard support, visible focus states, and AA contrast in light and dark themes.
- **Interactive UI**: Uploads CSVs, shows metrics, displays paginated/searchable records, manages override rules, and downloads enriched output.

## System Architecture

```mermaid
graph TD
    subgraph Frontend [React SPA]
        App[App.jsx] --> Theme[Theme Controller]
        App --> Upload[Dropzone Uploader]
        App --> Table[Paginated Sortable Table]
        App --> Stats[Charts and Metrics]
        App --> Overrides[Override Rules]
    end

    subgraph Backend [FastAPI]
        server[server.py] --> static[Serve dist assets]
        server --> api_enrich[POST /api/enrich]
        server --> api_rules[/api/rules and overrides]
    end

    subgraph Pipeline [enrichment package]
        facade[enrich.py facade] --> pipeline[pipeline.py]
        pipeline --> parsers[parsers.py]
        pipeline --> analyzer[analyzer.py]
        pipeline --> llm[llm.py]
        pipeline --> utils[utils.py]
    end

    App -- HTTP --> server
    server -- calls --> facade
```

### Modules

1. **`enrich.py`**: Shared CLI and FastAPI entry point.
2. **`enrichment/pipeline.py`**: CSV read/write, deduplication, manufacturer inference, metrics, and reports.
3. **`enrichment/parsers.py`**: Manufacturer-specific serial parsers with metadata validation.
4. **`enrichment/analyzer.py`**: Levenshtein typo checks and serial-format consistency fixes.
5. **`enrichment/llm.py`**: Search and OpenAI consensus for unknown devices and dates.
6. **`enrichment/metadata.py`**: Company founding years, model start years, source URLs, date validation, and local manufacturer guessing.
7. **`enrichment/utils.py`**: Environment loading, cache locks, date normalization, and JSON cache helpers.

## Enrichment Pipeline

```text
Raw CSV -> Deduplicate -> Infer Manufacturer -> Analyze Formatting -> Local Parsers
        -> Metadata Validation -> Web/LLM Fallback -> Date Bounds -> Cache -> Output
```

0. **Manufacturer inference**: Missing manufacturers are resolved by local model/serial hints first, then DuckDuckGo plus LLM consensus. Results are cached in `manufacturers_cache.json`.
1. **Deduplication**: Exact duplicate rows are removed.
2. **Format analysis**: The analyzer fixes common serial prefixes, normalizes model spacing, detects near-match typos, and writes reports.
3. **Local parsing**: `parsers.py` maps serials to manufacturer rules, such as ZOLL `YYM` date codes or GE product/year/week fields.
4. **Metadata validation**: Parsed years must be later than the company founding year and model start year in `metadata.py`.
5. **Search/LLM fallback**: Failed or rejected parses trigger a date/type lookup using metadata context and `gpt-5.4-mini` / `gpt-5.4-nano` consensus.
6. **Caching**: Device types, dates, rules, and manufacturers are cached for faster reruns.

## Manufacturer Serial Number Sources

The previous README table mixed source types and had a broken column header. This version separates **verified serial-number decoding sources** from general product metadata. A source is listed here only if it explains how to read a serial number or label date field on that company's devices.

| Manufacturer | Covered model(s) | Serial/date rule used by parser | Verified source |
|---|---|---|---|
| GE Healthcare | MAC 3500; used as the GE Healthcare serial format basis for GE medical devices with product/year/week serials | Product code, 2-digit manufacture year, 2-digit fiscal week, sequence, site, and characteristic fields | [GE MAC 3500 Service Manual PDF](https://discountcardiology.com/documents/1357_MAC3500-MANUAL.pdf); [ManualsLib page 18](https://www.manualslib.com/manual/1719909/Ge-Mac-3500.html?page=18) |
| Hillrom / Welch Allyn | ELI 230 | `YYYWWSSSSSSS`: fixed leading `1`, 2-digit manufacture year, manufacture week, sequence number | [Hillrom ELI 230 Service Manual PDF](https://www.hillrom.com/content/dam/hillrom-aem/us/en/sap-documents/LIT/9515-/9515-175-50-ENGLITPDF.pdf) |
| Hillrom / Welch Allyn | Connex Spot Monitor | `MMMMXXXXWWYY`: plant, sequence, manufacture week, manufacture year | [ManualsLib Connex Spot Monitor service manual, device serial label](https://www.manualslib.com/manual/2875681/Hillrom-Welch-Allyn-Connex-Spot-Monitor.html) |
| Welch Allyn | Spot Vital Signs 420 Series | 9-digit serial: first 4 digits are manufacture year, last 5 are unit sequence | [Welch Allyn Spot Vital Signs service manual, serial numbering system](https://www.manualslib.com/manual/1391564/Welch-Allyn-Spot-Vital-Signs.html?page=75) |
| ZOLL Medical | AED Plus | Characters after `X`: 2 digits are manufacture year; following letter is month | [ZOLL AED Plus ZAS download page](https://www.zoll.com/en-us/products/software-and-data/public-access-software/aed-plus-software-download) |
| ZOLL Medical | R Series | 2-character product code, 3-character date-of-manufacture code, then unit serial; R Series product code is `AF`; date code is `YYM` | [ZOLL R Series service manual, serial number section](https://www.manualslib.com/manual/1200420/Zoll-R-Series.html?page=400) |
| ZOLL Medical | X Series / Propaq MD | 2-character product code, 3-character `YYM` date-of-manufacture code, then unit serial | [ZOLL X Series operator manual, serial number section](https://www.manualslib.com/manual/1283001/Zoll-X-Series.html?page=40); [ZOLL Propaq MD operator manual, serial number section](https://www.manualslib.com/manual/1225133/Zoll-Propaq-Md.html?page=39) |

### Current Parser Coverage

The parser registry also covers Arjo, American Diagnostic, Baxter, BioSonic, Cogentix, Covidien, Edan, Exergen, Hospira, Jiangmen Dacheng, Lab Corp/Drucker, LINET, Masimo, Mindray, Olympus, Philips, Stryker, Thermo Scientific, and Unico. For those manufacturers, the previous README links were removed from the serial-source table because they did not explicitly document serial-number date interpretation. Their parsers remain bounded by `metadata.py` founding and product-start years, and unresolved or invalid dates fall back to search/LLM consensus.

| Manufacturer | Model(s) | Founded | Product start |
|---|---|---:|---|
| Arjo | FLOWTRON | 1957 | 1995 |
| American Diagnostic (ADC) | CE 1434 | 1984 | 1984 |
| Baxter Healthcare | SPECTRUM IQ | 1931 | 2017 |
| BioSonic (Coltene) | UC95, UC95D15 | 1988 | 1995 |
| Cogentix Medical | CST-4000, CST-5000 | 2015 | 2005 |
| Covidien | RAPIDVAC | 2007 | 2008 |
| Edan Instruments | ELITEV5, F9EXPRESS, IM3, IM50, IM70, SE1200EXPRESS, iT20 | 1995 | 2008-2016 |
| Exergen | TAT5000 | 1980 | 2005 |
| GE Healthcare | APEX PRO CH, Patient Data Module (PDM) | 1994 | 2001-2006 |
| Hillrom / Hill-Rom | CENTURY, CENTURYP1400, P3200, P1440, PCENTURYK3256 | 1929 | 1990-2003 |
| Hospira / ICU Medical | PLUMA+ | 2004 | 2004 |
| Jiangmen Dacheng | IOB-507 | 2008 | 2010 |
| Lab Corp / Drucker Diagnostics | 642E | 1978 | 1998 |
| LINET | ELEGANZA 3, ELEGANZA 4 | 1990 | 2004-2012 |
| Masimo | RAD8 | 1989 | 2005 |
| Mindray | BENEVISION N15, EPM12MA | 1991 | 2015-2018 |
| Olympus | CV190 | 1919 | 2012 |
| Philips | INTELLIVUE MP20/MP30/MP50/MX40, MX500, M3002A | 1891 | 2004-2013 |
| Stryker | 1061, 1115 | 1941 | 1995-2012 |
| Thermo Scientific | SMARTVUE915 | 2006 | 2011 |
| Unico | G380PL LED | 1991 | 2008 |
| Welch Allyn | FILAC3000, SPOT VITAL SIGNS, SURETEMPPLUS | 1915 | 2000-2009 |
| ZOLL Medical | AEDPLUS, M SERIES, RSERIES, R Series ALS/Plus, X Series, Propaq MD | 1980 | 1998-2012 |

## WCAG 2.2 AA Compliance

The dashboard targets WCAG 2.2 AA:

- **Contrast**: Text, fields, and status badges meet 4.5:1 contrast; large text/icons meet 3:1.
- **Keyboard access**: Upload zones, sortable table headers, fields, buttons, and pagination controls are keyboard-operable.
- **Focus visibility**: Interactive elements use a high-contrast focus ring.
- **Semantics and ARIA**: Layout uses `<header>`, `<main>`, `<aside>`, `<section>`, and `<nav>`; icon buttons and controls have accessible names; decorative icons are hidden from screen readers; labels are connected to inputs.

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv)

### Installation

```bash
git clone <repository_url>
cd equiply-challenge
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
npm install
```

Create `.env` in the repo root:

```ini
OPENAI_API_KEY=your-openai-api-key-here
```

Standard `pip` also works:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### CLI Enrichment Engine

```bash
uv run python3 enrich.py <input_csv_path> <output_csv_path>
```

Example:

```bash
uv run python3 enrich.py challenge_data-v1.csv challenge_data_enriched.csv
```

The output adds `device_type` and `manufactured_date`. Reports are written to `formatting_corrections.txt` and `probable_typos.txt`.

### Local FastAPI and React Dashboard

```bash
npm run build
uv run python3 server.py
```

Open [http://localhost:8000](http://localhost:8000). The dashboard can upload equipment CSVs, show corrections, add manual overrides, display metrics, and download the enriched CSV.

Frontend-only work can use Vite HMR:

```bash
npm run dev
```

The frontend defaults to backend calls at `http://localhost:8000`.

## Testing

```bash
uv run python3 test_enrich_logic.py
```

The tests cover parser logic, metadata validation, and manufacturer guessing.

## File Structure

```text
equiply-challenge/
├── enrichment/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── llm.py
│   ├── metadata.py
│   ├── parsers.py
│   ├── pipeline.py
│   └── utils.py
├── src/
│   ├── assets/
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── dist/
├── enrich.py
├── server.py
├── test_enrich_logic.py
├── pyproject.toml
├── requirements.txt
├── package.json
├── .env
└── README.md
```

## Future Improvements

### Manufacturer Metadata

`enrichment/metadata.py` is a static Python dictionary. It works for this dataset but is hard for non-engineers to audit and can drift when manufacturers change serial formats.

**Recommendation**: Move metadata to `metadata.yaml` or SQLite with required fields for `founded_year`, `product_start_year`, and serial-specific sources. That would make updates reviewable as data changes.

### Source Verification

Sources are not checked at runtime, and manufacturer PDFs move over time.

**Recommendation**: Add a weekly CI link checker for source URLs and keep local archived copies for critical serial guides.

### LLM Date Risk

LLM fallback can return plausible wrong dates, especially for niche manufacturers or weak search results.

**Recommendation**: Show low-confidence date resolutions with a dashboard badge and allow user overrides with a logged reason.

### Cache Invalidation

JSON caches are indefinite. A corrected typo or similar new device may still reuse stale cached values.

**Recommendation**: Store cache timestamps, add a 30-day TTL, and add a `--clear-cache` CLI flag.

### Manufacturer Coverage

The registry covers manufacturers in `challenge_data-v1.csv`; real hospital exports may include Draeger, Spacelabs, Datascope, more Mindray lines, Nihon Kohden, and others.

**Recommendation**: Add `uv run python3 analyze_unknown.py` to scan an input CSV, identify unknown manufacturers, and output metadata stubs.

### Week-to-Month Precision

Several parsers approximate week-to-month conversion with `month = int(week * 7 / 30.4) + 1`, which can shift the month by one.

**Recommendation**: Use `datetime.fromisocalendar(year, week, 1)` and derive the exact month.

### User Feedback Loop

The dashboard cannot currently flag an incorrect resolved date.

**Recommendation**: Add a per-row "Report incorrect date" action that writes to `user_corrections.json`, then prefer those corrections on later runs.
