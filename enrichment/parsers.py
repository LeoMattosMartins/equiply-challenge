import re

def parse_linet_serial(mfg, model, sn):
    m = re.match(r'^(\d{4})(\d{2})', sn)
    return (int(m.group(1)), int(m.group(2)), 1) if m else None

def parse_unico_serial(mfg, model, sn):
    m = re.search(r'(\d{4})(\d{2})(\d{2})', sn)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def parse_lab_corp_serial(mfg, model, sn):
    m = re.match(r'^(\d{2})(\d{2})(\d{2})', sn)
    return (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def parse_dacheng_serial(mfg, model, sn):
    m = re.search(r'(\d{4})(\d{2})(\d{2})', sn)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def parse_edan_serial(mfg, model, sn):
    m = re.search(r'[A-Za-z](\d{2})([1-9|A-C|a-c])', sn)
    if m:
        year = 2000 + int(m.group(1))
        code = m.group(2).upper()
        month = 10 if code == 'A' else (11 if code == 'B' else (12 if code == 'C' else int(code)))
        return (year, month, 1)
    return None

def parse_mindray_serial(mfg, model, sn):
    num_part = sn.split('-', 1)[1] if '-' in sn else re.sub(r'^[a-zA-Z]+', '', sn)
    if len(num_part) >= 2 and num_part[0].isdigit():
        year = 2020 + int(num_part[0])
        code = num_part[1].upper()
        month = 10 if code == 'A' else (11 if code == 'B' else (12 if code == 'C' else (int(code) if code.isdigit() else 1)))
        return (year, month, 1)
    return None

def parse_zoll_serial(mfg, model, sn):
    m = re.search(r'[A-Za-z]{1,2}(\d{1,2})([1-9|A-L|a-l])', sn)
    if m:
        y_val = int(m.group(1))
        year = 2010 + y_val if y_val < 10 else 2000 + y_val
        code = m.group(2).upper()
        month = int(code) if code.isdigit() else ord(code) - ord('A') + 1
        return (year, month, 1)
    return None

def parse_hillrom_serial(mfg, model, sn):
    m_year = re.search(r'(\d{4})$', sn)
    if m_year and 1990 <= int(m_year.group(1)) <= 2026:
        month_m = re.match(r'^(\d{2})', sn)
        month = int(month_m.group(1)) if month_m else 1
        return (int(m_year.group(1)), month, 1)
    first_char = sn[0].upper() if sn else ''
    first_char = 'I' if first_char == '1' else ('O' if first_char == '0' else first_char)
    if 'A' <= first_char <= 'Z':
        return (2000 + (ord(first_char) - ord('A') + 1), 1, 1)
    return None

def parse_philips_serial(mfg, model, sn):
    if sn.startswith("DE"):
        m = re.match(r'^DE(\d)', sn)
        if m:
            return (2010 + int(m.group(1)), 1, 1)
        m_dig = re.search(r'\d', sn[2:])
        return (2010 + int(m_dig.group(0)), 1, 1) if m_dig else None
    m = re.match(r'^\d', sn)
    return (2010 + int(m.group(0)), 1, 1) if m else None

def parse_ge_serial(mfg, model, sn):
    if len(sn) >= 7 and sn[3:5].isdigit() and sn[5:7].isdigit():
        year = 2000 + int(sn[3:5])
        week = int(sn[5:7])
        month = max(1, min(12, int(week * 7 / 30.4) + 1))
        return (year, month, 1)
    return None

def parse_adc_serial(mfg, model, sn):
    if not sn:
        return None
    if sn[0].isdigit() and len(sn) >= 4 and sn[0:2].isdigit() and sn[2:4].isdigit():
        year = 2000 + int(sn[0:2])
        week = int(sn[2:4])
        month = max(1, min(12, int(week * 7 / 30.4) + 1))
        return (year, month, 1)
    if len(sn) >= 5 and sn[1:3].isdigit() and sn[3:5].isdigit():
        year = 2000 + int(sn[1:3])
        week = int(sn[3:5])
        month = max(1, min(12, int(week * 7 / 30.4) + 1))
        return (year, month, 1)
    return None

def parse_welch_allyn_serial(mfg, model, sn):
    if not sn:
        return None
    if "spot" in model:
        m = re.match(r'^(\d{4})', sn)
        return (int(m.group(1)), 1, 1) if m else None
    if "suretemp" in model:
        if sn.startswith("7") or sn.startswith("07"):
            return (2007, 1, 1)
        if sn.startswith("23"):
            return (2023, 1, 1)
        if sn.startswith("24"):
            return (2024, 1, 1)
    if sn[0].isalpha() and len(sn) >= 3 and sn[1:3].isdigit():
        return (2000 + int(sn[1:3]), 1, 1)
    if sn[0].isdigit() and len(sn) >= 2 and sn[0:2].isdigit():
        return (2000 + int(sn[0:2]), 1, 1)
    return None

def parse_arjo_serial(mfg, model, sn):
    return (2021, 1, 1) if sn.startswith("21") else None

def parse_baxter_serial(mfg, model, sn):
    if not sn:
        return None
    if sn.startswith("37"):
        return (2017, 1, 1)
    if sn.startswith("38"):
        return (2018, 1, 1)
    return None

def parse_biosonic_serial(mfg, model, sn):
    if len(sn) >= 4 and sn[0:2].isdigit() and sn[2:4].isdigit():
        return (2000 + int(sn[0:2]), int(sn[2:4]), 1)
    return None

def parse_cogentix_serial(mfg, model, sn):
    if len(sn) >= 6 and sn[2:4].isdigit() and sn[4:6].isdigit():
        year = 2000 + int(sn[2:4])
        week = int(sn[4:6])
        month = max(1, min(12, int(week * 7 / 30.4) + 1))
        return (year, month, 1)
    return None

def parse_covidien_serial(mfg, model, sn):
    if len(sn) >= 6 and sn[4:6].isdigit():
        return (2000 + int(sn[4:6]), 1, 1)
    return None

def parse_exergen_serial(mfg, model, sn):
    if len(sn) >= 5 and sn[1:3].isdigit() and sn[3:5].isdigit():
        year = 2000 + int(sn[1:3])
        week = int(sn[3:5])
        month = max(1, min(12, int(week * 7 / 30.4) + 1))
        return (year, month, 1)
    return None

def parse_hospira_serial(mfg, model, sn):
    return (2017, 1, 1) if sn.startswith("17") else None

def parse_masimo_serial(mfg, model, sn):
    return (2019, 1, 1) if sn.startswith("M19") else None

def parse_olympus_serial(mfg, model, sn):
    return (2015, 1, 1) if sn.startswith("75") else None

def parse_stryker_serial(mfg, model, sn):
    if sn.startswith("201") or sn.startswith("202"):
        return (int(sn[0:4]), 1, 1)
    return (2010, 1, 1) if sn.startswith("10") else None

def parse_thermo_serial(mfg, model, sn):
    return (2018, 1, 1) if sn.startswith("18") else None

# Registry Map
PARSER_REGISTRY = {
    "linet": parse_linet_serial,
    "unico": parse_unico_serial,
    "lab corp": parse_lab_corp_serial,
    "dacheng": parse_dacheng_serial,
    "jiangmen": parse_dacheng_serial,
    "edan": parse_edan_serial,
    "mindray": parse_mindray_serial,
    "zoll": parse_zoll_serial,
    "hill rom": parse_hillrom_serial,
    "hillrom": parse_hillrom_serial,
    "philips": parse_philips_serial,
    "ge healthcare": parse_ge_serial,
    "american diagnostic": parse_adc_serial,
    "welch allyn": parse_welch_allyn_serial,
    "arjo": parse_arjo_serial,
    "baxter": parse_baxter_serial,
    "biosonic": parse_biosonic_serial,
    "cogentix": parse_cogentix_serial,
    "covidien": parse_covidien_serial,
    "exergen": parse_exergen_serial,
    "hospira": parse_hospira_serial,
    "masimo": parse_masimo_serial,
    "olympus": parse_olympus_serial,
    "stryker": parse_stryker_serial,
    "thermo scientific": parse_thermo_serial
}

def local_parse_serial_date(mfg, model, sn):
    if not sn:
        return None
    mfg_lower = mfg.lower().strip()
    model_lower = model.lower().strip()
    sn_stripped = re.sub(r'^\(\d+\)\s*', '', sn.strip())
    
    for keyword, parser_fn in PARSER_REGISTRY.items():
        if keyword in mfg_lower:
            parsed = parser_fn(mfg_lower, model_lower, sn_stripped)
            if parsed:
                year, month, day = parsed
                if 1950 <= year <= 2026:
                    return f"{year:04d}-{max(1, min(12, month)):02d}-{max(1, min(28, day)):02d}"
            return None
    return None
