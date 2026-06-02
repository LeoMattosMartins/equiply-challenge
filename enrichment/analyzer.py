import re

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def analyze_format_consistency(raw_rows):
    """
    Dynamically identifies prefix patterns across (manufacturer, model) groups,
    identifies model name inconsistencies (spacing, minor spelling differences),
    calculates self-healing corrections, and returns them.
    """
    mfg_groups = {}
    for r in raw_rows:
        mfg = r["mfg"]
        model = r["model"]
        mfg_lower = mfg.lower().strip()
        if mfg_lower not in mfg_groups:
            mfg_groups[mfg_lower] = {
                "original_mfg": mfg,
                "models": {}
            }
        
        model_lower = model.lower().strip()
        if model_lower not in mfg_groups[mfg_lower]["models"]:
            mfg_groups[mfg_lower]["models"][model_lower] = {
                "original_model": model,
                "serials": []
            }
        mfg_groups[mfg_lower]["models"][model_lower]["serials"].append(r["sn"])

    serial_corrections = {}
    model_corrections = {}
    
    for mfg_lower, mfg_data in mfg_groups.items():
        original_mfg = mfg_data["original_mfg"]
        models_dict = mfg_data["models"]
        
        normalized_models = {}
        for model_lower, model_data in models_dict.items():
            norm_key = re.sub(r'[^a-z0-9]', '', model_lower)
            if not norm_key:
                continue
            if norm_key not in normalized_models:
                normalized_models[norm_key] = []
            normalized_models[norm_key].append(model_data)
            
        for norm_key, variants in normalized_models.items():
            if len(variants) > 1:
                variants_sorted = sorted(variants, key=lambda x: len(x["serials"]), reverse=True)
                dominant = variants_sorted[0]
                dominant_name = dominant["original_model"]
                
                for var in variants_sorted[1:]:
                    orig_name = var["original_model"]
                    key = f"{mfg_lower}|{orig_name.lower()}"
                    model_corrections[key] = {
                        "corrected": dominant_name,
                        "reason": f"Standardized model spelling '{orig_name}' to match dominant variant '{dominant_name}' for manufacturer '{original_mfg}'"
                    }
                    
        norm_keys = list(normalized_models.keys())
        for i in range(len(norm_keys)):
            for j in range(i + 1, len(norm_keys)):
                k1, k2 = norm_keys[i], norm_keys[j]
                dist = levenshtein_distance(k1, k2)
                if 1 <= dist <= 2:
                    vars1 = normalized_models[k1]
                    vars2 = normalized_models[k2]
                    count1 = sum(len(v["serials"]) for v in vars1)
                    count2 = sum(len(v["serials"]) for v in vars2)
                    
                    if count1 >= 5 and count2 <= 2:
                        dominant_name = vars1[0]["original_model"]
                        for var in vars2:
                            orig_name = var["original_model"]
                            key = f"{mfg_lower}|{orig_name.lower()}"
                            model_corrections[key] = {
                                "corrected": dominant_name,
                                "reason": f"Corrected spelling typo '{orig_name}' to dominant model '{dominant_name}' for manufacturer '{original_mfg}' (Levenshtein distance: {dist})"
                            }
                    elif count2 >= 5 and count1 <= 2:
                        dominant_name = vars2[0]["original_model"]
                        for var in vars1:
                            orig_name = var["original_model"]
                            key = f"{mfg_lower}|{orig_name.lower()}"
                            model_corrections[key] = {
                                "corrected": dominant_name,
                                "reason": f"Corrected spelling typo '{orig_name}' to dominant model '{dominant_name}' for manufacturer '{original_mfg}' (Levenshtein distance: {dist})"
                            }

    for mfg_lower, mfg_data in mfg_groups.items():
        original_mfg = mfg_data["original_mfg"]
        for model_lower, model_data in mfg_data["models"].items():
            original_model = model_data["original_model"]
            serials = [s.strip() for s in model_data["serials"] if s and s.strip()]
            if len(serials) < 3:
                continue
                
            prefixes = []
            for sn in serials:
                sn_clean = re.sub(r'^\(\d+\)\s*', '', sn)
                m = re.match(r'^([A-Za-z]+)', sn_clean)
                prefixes.append(m.group(1).upper() if m else "")
                
            prefix_counts = {}
            for p in prefixes:
                if p:
                    prefix_counts[p] = prefix_counts.get(p, 0) + 1
                    
            if prefix_counts:
                dominant_prefix = max(prefix_counts, key=prefix_counts.get)
                dom_count = prefix_counts[dominant_prefix]
                total_with_serials = len(serials)
                
                if dom_count / total_with_serials >= 0.6:
                    for sn in serials:
                        sn_clean = re.sub(r'^\(\d+\)\s*', '', sn)
                        if not sn_clean.upper().startswith(dominant_prefix):
                            corrected_sn = dominant_prefix + sn_clean
                            parentheses_match = re.match(r'^(\(\d+\)\s*)', sn)
                            if parentheses_match:
                                corrected_sn = parentheses_match.group(1) + corrected_sn
                                
                            serial_corrections[sn] = {
                                "corrected": corrected_sn,
                                "manufacturer": original_mfg,
                                "model": original_model,
                                "reason": f"Prepended missing dominant prefix '{dominant_prefix}' to serial '{sn}' to match dominant format under '{original_mfg}' (model: '{original_model}')"
                            }
                            
            parentheses_count = sum(1 for sn in serials if re.match(r'^\(\d+\)', sn))
            if 0 < parentheses_count <= 2 and (len(serials) - parentheses_count) >= 3:
                for sn in serials:
                    if re.match(r'^\(\d+\)', sn):
                        corrected_sn = re.sub(r'^\(\d+\)\s*', '', sn)
                        serial_corrections[sn] = {
                            "corrected": corrected_sn,
                            "manufacturer": original_mfg,
                            "model": original_model,
                            "reason": f"Stripped unexpected prefix '{re.match(r'^(\(\d+\))', sn).group(1)}' from serial '{sn}' for manufacturer '{original_mfg}'"
                        }
                        
            lengths = [len(re.sub(r'^\(\d+\)\s*', '', sn)) for sn in serials]
            length_counts = {}
            for l in lengths:
                length_counts[l] = length_counts.get(l, 0) + 1
            if length_counts:
                dominant_len = max(length_counts, key=length_counts.get)
                dom_len_count = length_counts[dominant_len]
                if dom_len_count / len(serials) >= 0.70:
                    for sn in serials:
                        sn_clean = re.sub(r'^\(\d+\)\s*', '', sn)
                        if len(sn_clean) != dominant_len:
                            if sn not in serial_corrections:
                                serial_corrections[sn] = {
                                    "corrected": sn,
                                    "manufacturer": original_mfg,
                                    "model": original_model,
                                    "reason": f"Serial length mismatch ({len(sn_clean)} chars vs dominant length of {dominant_len} chars) for '{original_mfg}' (model: '{original_model}')"
                                }

    return {
        "serial_corrections": serial_corrections,
        "model_corrections": model_corrections
    }
