import os
import csv
import re
import sys
import json

from enrichment.utils import load_json_cache, save_json_cache, TYPES_CACHE_FILE, DATES_CACHE_FILE, MANUFACTURERS_CACHE_FILE, normalize_date
from enrichment.parsers import local_parse_serial_date
from enrichment.analyzer import analyze_format_consistency
from enrichment.llm import resolve_device_type_consensus, resolve_serial_dates_consensus, resolve_manufacturer_consensus
from enrichment.metadata import guess_manufacturer_locally, validate_mfg_date, get_model_metadata

def write_typos_report(types_cache, corrections):
    typo_models = []
    for key, val in types_cache.items():
        if val.get("probable_typo"):
            parts = key.split("|", 1)
            mfg = parts[0]
            model = parts[1] if len(parts) > 1 else ""
            typo_models.append(f"Manufacturer: {mfg.upper()} | Model: {model.upper()} (Flagged as probable typo)")
            
    # Include model corrections in the typos file as well
    model_corr = corrections.get("model_corrections", {})
    for key, info in model_corr.items():
        typo_models.append(f"Model Inconsistency: {info['reason']}")
        
    try:
        with open("probable_typos.txt", "w", encoding="utf-8") as f:
            if typo_models:
                f.write("The following medical device models are flagged as probable typos or formatting inconsistencies:\n\n")
                f.write("\n".join(typo_models))
                f.write("\n")
            else:
                f.write("No probable model typos found in the dataset.\n")
        print(f"Probable typos report written to probable_typos.txt (flagged {len(typo_models)} items).")
    except Exception as e:
        print(f"Error writing probable_typos.txt: {e}", file=sys.stderr)

def write_corrections_report(corrections):
    lines = []
    
    # Model corrections
    model_corr = corrections.get("model_corrections", {})
    if model_corr:
        lines.append("=== Model Name Spelling & Spacing Corrections ===")
        for key, info in model_corr.items():
            lines.append(f"- {info['reason']}")
        lines.append("")
        
    # Serial corrections
    serial_corr = corrections.get("serial_corrections", {})
    if serial_corr:
        lines.append("=== Serial Number Formatting Corrections ===")
        for raw_sn, info in serial_corr.items():
            if info["corrected"] != raw_sn:
                lines.append(f"- Corrected serial '{raw_sn}' to '{info['corrected']}' for manufacturer '{info['manufacturer']}' (model '{info['model']}'): {info['reason']}")
            else:
                lines.append(f"- Serial formatting mismatch noted for '{raw_sn}' under '{info['manufacturer']}' (model '{info['model']}'): {info['reason']}")
                
    try:
        with open("formatting_corrections.txt", "w", encoding="utf-8") as f:
            if lines:
                f.write("The Equiply Enrichment engine dynamically identified and corrected the following formatting inconsistencies:\n\n")
                f.write("\n".join(lines))
                f.write("\n")
            else:
                f.write("No formatting corrections were necessary for this dataset.\n")
        print("Formatting corrections report written to formatting_corrections.txt.")
    except Exception as e:
        print(f"Error writing formatting_corrections.txt: {e}", file=sys.stderr)

def enrich_csv(input_path, output_path, api_key=None):
    if not api_key:
        api_key = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI_API_KEY")
        
    if not api_key:
        print("Error: No OpenAI API key found. Running in local fallback mode.", file=sys.stderr)
        
    types_cache_raw = load_json_cache(TYPES_CACHE_FILE)
    types_cache = {}
    for k, v in types_cache_raw.items():
        if isinstance(v, dict):
            types_cache[k] = {
                "device_type": v.get("device_type", "Medical Device"),
                "probable_typo": v.get("probable_typo", False),
                "confidence": v.get("confidence", 1.0)
            }
        else:
            types_cache[k] = {
                "device_type": v,
                "probable_typo": False,
                "confidence": 1.0
            }
            
    dates_cache_raw = load_json_cache(DATES_CACHE_FILE)
    dates_cache = {}
    for k, v in dates_cache_raw.items():
        if isinstance(v, dict):
            dates_cache[k] = {
                "date": normalize_date(v.get("date")),
                "confidence": v.get("confidence", 1.0)
            }
        else:
            dates_cache[k] = {
                "date": normalize_date(v),
                "confidence": 1.0
            }
    save_json_cache(DATES_CACHE_FILE, dates_cache)

    # Load manufacturers cache (for Pass 0 results)
    manufacturers_cache = load_json_cache(MANUFACTURERS_CACHE_FILE)
    
    # Step 1: Read input and remove duplicate rows based on (manufacturer, model, serial_number)
    raw_rows = []
    seen_signatures = set()
    duplicates_removed = 0
    
    with open(input_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            headers = {k.lower().strip(): k for k in row.keys()}
            mfg_key = headers.get('manufacturer')
            model_key = headers.get('model')
            sn_key = headers.get('serial number') or headers.get('serial_number')
            
            mfg = row[mfg_key].strip() if mfg_key else ""
            model = row[model_key].strip() if model_key else ""
            sn = row[sn_key].strip() if sn_key else ""
            
            sig = (mfg.lower(), model.lower(), sn.lower())
            if sig in seen_signatures:
                duplicates_removed += 1
                continue
            seen_signatures.add(sig)
            
            raw_rows.append({
                "row_dict": dict(row),
                "mfg": mfg,
                "model": model,
                "sn": sn,
                "sn_original": sn,
                "mfg_key": mfg_key,
                "model_key": model_key,
                "sn_key": sn_key
            })
            
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate rows from the dataset.")

    # ─── Pass 0: Manufacturer Inference ───────────────────────────────────────
    # For rows with empty/unknown manufacturer, attempt local inference first,
    # then fall back to the web+LLM consensus. Results are persisted in cache.
    mfg_resolved = 0
    rows_needing_llm_mfg = []

    for r in raw_rows:
        if r["mfg"].strip():
            continue  # already known

        cache_key = f"{r['model'].lower()}|{r['sn'].lower()}"
        if cache_key in manufacturers_cache:
            guessed = manufacturers_cache[cache_key]
        else:
            guessed = guess_manufacturer_locally(r["model"], r["sn"])

        if guessed:
            r["mfg"] = guessed
            if r["mfg_key"]:
                r["row_dict"][r["mfg_key"]] = guessed
            manufacturers_cache[cache_key] = guessed
            mfg_resolved += 1
        else:
            rows_needing_llm_mfg.append(r)

    # LLM fallback for rows still missing a manufacturer
    if rows_needing_llm_mfg and api_key:
        print(f"Pass 0: Using LLM to infer manufacturer for {len(rows_needing_llm_mfg)} rows...")
        for r in rows_needing_llm_mfg:
            cache_key = f"{r['model'].lower()}|{r['sn'].lower()}"
            guessed = resolve_manufacturer_consensus(r["model"], r["sn"], api_key)
            if guessed and guessed != "Unknown Manufacturer":
                r["mfg"] = guessed
                if r["mfg_key"]:
                    r["row_dict"][r["mfg_key"]] = guessed
                manufacturers_cache[cache_key] = guessed
                mfg_resolved += 1

        save_json_cache(MANUFACTURERS_CACHE_FILE, manufacturers_cache)

    if mfg_resolved:
        print(f"Pass 0: Resolved manufacturer for {mfg_resolved} rows.")

    # Analyze format outliers dynamically
    corrections = analyze_format_consistency(raw_rows)
    
    # Apply self-healing corrections to raw_rows dynamically!
    for r in raw_rows:
        mfg_lower = r["mfg"].lower().strip()
        model_lower = r["model"].lower().strip()
        
        # 1. Correct model name if needed
        model_key = f"{mfg_lower}|{model_lower}"
        if model_key in corrections["model_corrections"]:
            corrected_model = corrections["model_corrections"][model_key]["corrected"]
            r["model"] = corrected_model
            if r["model_key"]:
                r["row_dict"][r["model_key"]] = corrected_model
                
        # 2. Correct serial number if needed
        sn_raw = r["sn_original"]
        if sn_raw in corrections["serial_corrections"]:
            corrected_sn = corrections["serial_corrections"][sn_raw]["corrected"]
            r["sn"] = corrected_sn
            if r["sn_key"]:
                r["row_dict"][r["sn_key"]] = corrected_sn
        
    # Step 2: Determine which models need device type resolution (Pass 1)
    unresolved_types = {}
    for r in raw_rows:
        type_key = f"{r['mfg'].lower()}|{r['model'].lower()}"
        if type_key not in types_cache:
            unresolved_types[type_key] = (r['mfg'], r['model'])
            
    # Step 3: Run Pass 1 (Device Type & Typo detection)
    if unresolved_types and api_key:
        print(f"Pass 1: Resolving device types and typos for {len(unresolved_types)} models...")
        for key, (mfg, model) in unresolved_types.items():
            res = resolve_device_type_consensus(mfg, model, api_key)
            types_cache[key] = {
                "device_type": res.get("device_type", "Medical Device"),
                "probable_typo": res.get("probable_typo", False),
                "confidence": res.get("confidence", 0.95)
            }
        save_json_cache(TYPES_CACHE_FILE, types_cache)
        
    # Step 4: Write typos and corrections reports
    write_typos_report(types_cache, corrections)
    write_corrections_report(corrections)
    
    # Step 5: Determine which serial numbers need date resolution (Pass 2)
    unresolved_dates = {}
    for r in raw_rows:
        date_key = f"{r['mfg'].lower()}|{r['model'].lower()}|{r['sn'].lower()}"
        
        # Struct checks: try parsing locally first on corrected serial!
        local_date = local_parse_serial_date(r['mfg'], r['model'], r['sn'])
        # If the serial number has a length mismatch or unresolved issue, treat it as outlier
        is_unresolved_outlier = (r['sn_original'] in corrections["serial_corrections"]) and not local_date
        
        if date_key not in dates_cache:
            if local_date and not is_unresolved_outlier:
                dates_cache[date_key] = {
                    "date": local_date,
                    "confidence": 1.0
                }
            else:
                # Date is off. Fallback to LLM!
                type_key = f"{r['mfg'].lower()}|{r['model'].lower()}"
                if type_key not in unresolved_dates:
                    unresolved_dates[type_key] = {
                        "mfg": r['mfg'],
                        "model": r['model'],
                        "serials": set()
                    }
                if r['sn']:
                    unresolved_dates[type_key]["serials"].add(r['sn'])
                    
    save_json_cache(DATES_CACHE_FILE, dates_cache)
                
    # Step 6: Run Pass 2 (Manufactured Date Resolution) only if local parsing failed
    if unresolved_dates and api_key:
        print(f"Pass 2: Resolving manufacturing dates for {len(unresolved_dates)} models...")
        for key, info in unresolved_dates.items():
            mfg = info["mfg"]
            model = info["model"]
            serials_list = list(info["serials"])

            # Fetch metadata bounds so we can validate LLM-returned dates
            meta = get_model_metadata(mfg, model)
            min_year = meta["product_start_year"] if meta else 1900
            min_year_str = f"{min_year}-01-01"
            
            batch_size = 30
            for i in range(0, len(serials_list), batch_size):
                batch_serials = serials_list[i:i+batch_size]
                res = resolve_serial_dates_consensus(mfg, model, batch_serials, api_key)
                serial_dates = res.get("serial_dates", {})
                confidence = res.get("confidence", 0.90)
                for sn, date_str in serial_dates.items():
                    normalized = normalize_date(date_str)
                    # Validate the date the LLM returned against metadata bounds
                    m = re.match(r'^(\d{4})', normalized)
                    if m:
                        llm_year = int(m.group(1))
                        is_valid, reason = validate_mfg_date(mfg, model, llm_year)
                        if not is_valid:
                            print(f"  ⚠ LLM date {normalized} for {mfg}|{model}|{sn} failed validation: {reason}. Falling back to {min_year_str}.", file=sys.stderr)
                            normalized = min_year_str
                            confidence = max(0.3, confidence - 0.2)
                    d_key = f"{mfg.lower()}|{model.lower()}|{sn.lower()}"
                    dates_cache[d_key] = {
                        "date": normalized,
                        "confidence": confidence
                    }
                    
        save_json_cache(DATES_CACHE_FILE, dates_cache)
        
    # Step 7: Build final output rows (keep only original columns + manufactured_date + device_type)
    enriched_rows = []
    for r in raw_rows:
        mfg_clean = r["mfg"]
        model_clean = r["model"]
        sn_clean = r["sn"]
        
        type_key = f"{mfg_clean.lower()}|{model_clean.lower()}"
        date_key = f"{mfg_clean.lower()}|{model_clean.lower()}|{sn_clean.lower()}"
        
        cached_type = types_cache.get(type_key, {"device_type": "Medical Device", "probable_typo": False, "confidence": 0.1})
        date_info = dates_cache.get(date_key)
        
        if not date_info:
            m_year = re.search(r'\b((?:18|19|20)\d{2})\b', sn_clean)
            if m_year:
                mdate = f"{m_year.group(1)}-01-01"
            else:
                mdate = "1900-01-01"
        else:
            mdate = normalize_date(date_info.get("date"))
            
        row_enriched = {}
        for k, v in r["row_dict"].items():
            k_clean = k.lower().strip()
            if k_clean not in ("manufactured_date", "device_type", "is_duplicate", "probable_typo"):
                row_enriched[k] = v
                
        row_enriched["manufactured_date"] = mdate
        row_enriched["device_type"] = cached_type.get("device_type", "Medical Device")
        
        enriched_rows.append(row_enriched)
        
    enriched_rows.sort(key=lambda x: x.get('manufactured_date', ''))
    
    if enriched_rows:
        fieldnames = list(enriched_rows[0].keys())
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched_rows)
            
    print(f"Enriched and sorted {len(enriched_rows)} rows. Saved to {output_path}")
