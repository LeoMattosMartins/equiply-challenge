import re

# Canonical metadata database for manufacturers and models
METADATA = {
    "arjo": {
        "founded_year": 1957,
        "models": {
            "flowtron": {
                "product_start_year": 1995,
                "sources": [
                    "https://www.arjo.com/int/products/compression-therapy/active-compression/flowtron-universal/",
                    "https://www.manualslib.com/brand/arjo/"
                ]
            }
        }
    },
    "american diagnostic": {
        "founded_year": 1984,
        "models": {
            "ce 1434": {
                "product_start_year": 1984,
                "sources": [
                    "https://www.adctoday.com/support/warranty-information",
                    "https://www.manualslib.com/brand/adc/"
                ]
            }
        }
    },
    "baxter": {
        "founded_year": 1931,
        "models": {
            "spectrum iq": {
                "product_start_year": 2017,
                "sources": [
                    "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm",
                    "https://www.manualslib.com/brand/baxter/"
                ]
            }
        }
    },
    "biosonic": {
        "founded_year": 1988,
        "models": {
            "uc95": {
                "product_start_year": 1995,
                "sources": [
                    "https://www.coltene.com/products/hygiene/ultrasonic-cleaning/biosonic-ultrasonic-cleaning-systems/",
                    "https://www.manualslib.com/brand/coltene/"
                ]
            },
            "uc95d15": {
                "product_start_year": 1995,
                "sources": [
                    "https://www.coltene.com/products/hygiene/ultrasonic-cleaning/biosonic-ultrasonic-cleaning-systems/",
                    "https://www.manualslib.com/brand/coltene/"
                ]
            }
        }
    },
    "cogentix": {
        "founded_year": 2015,
        "models": {
            "cst-4000": {
                "product_start_year": 2005,
                "sources": [
                    "https://www.laborie.com/products/urology/cystoscopes/",
                    "https://www.manualslib.com/brand/laborie/"
                ]
            },
            "cst-5000": {
                "product_start_year": 2005,
                "sources": [
                    "https://www.laborie.com/products/urology/cystoscopes/",
                    "https://www.manualslib.com/brand/laborie/"
                ]
            }
        }
    },
    "covidien": {
        "founded_year": 2007,
        "models": {
            "rapidvac": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.medtronic.com/covidien/en-us/products/surgical-smoke-evacuation/rapidvac-smoke-evacuator.html",
                    "https://www.manualslib.com/brand/covidien/"
                ]
            }
        }
    },
    "edan": {
        "founded_year": 1995,
        "models": {
            "elitev5": {
                "product_start_year": 2012,
                "sources": [
                    "https://www.edan.com/product/patient-monitoring/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            },
            "f9express": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.edan.com/product/obstetrics/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            },
            "im3": {
                "product_start_year": 2015,
                "sources": [
                    "https://www.edan.com/product/patient-monitoring/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            },
            "im50": {
                "product_start_year": 2010,
                "sources": [
                    "https://www.edan.com/product/patient-monitoring/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            },
            "im70": {
                "product_start_year": 2011,
                "sources": [
                    "https://www.edan.com/product/patient-monitoring/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            },
            "se1200express": {
                "product_start_year": 2010,
                "sources": [
                    "https://www.edan.com/product/ecg/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            },
            "it20": {
                "product_start_year": 2016,
                "sources": [
                    "https://www.edan.com/product/patient-monitoring/",
                    "https://www.manualslib.com/brand/edan/"
                ]
            }
        }
    },
    "exergen": {
        "founded_year": 1980,
        "models": {
            "tat5000": {
                "product_start_year": 2005,
                "sources": [
                    "https://www.exergen.com/professional-medical-products/products/tat-5000-temporal-artery-thermometer",
                    "https://www.manualslib.com/products/Exergen-Temporal-Artery-Thermometer-Tat-5000-7399764.html"
                ]
            }
        }
    },
    "ge healthcare": {
        "founded_year": 1994,
        "models": {
            "apex pro ch": {
                "product_start_year": 2001,
                "sources": [
                    "https://www.gehealthcare.com/products/patient-monitoring",
                    "https://www.medwrench.com/equipment/ge-healthcare"
                ]
            },
            "patient data module (pdm)": {
                "product_start_year": 2006,
                "sources": [
                    "https://www.gehealthcare.com/products/patient-monitoring",
                    "https://www.medwrench.com/equipment/ge-healthcare"
                ]
            }
        }
    },
    "hillrom": {
        "founded_year": 1929,
        "models": {
            "century": {
                "product_start_year": 1990,
                "sources": [
                    "https://www.hillrom.com/en/support/",
                    "https://www.manualslib.com/brand/hill-rom/"
                ]
            },
            "centuryp1400": {
                "product_start_year": 1990,
                "sources": [
                    "https://www.hillrom.com/en/support/",
                    "https://www.manualslib.com/brand/hill-rom/"
                ]
            },
            "p3200": {
                "product_start_year": 2003,
                "sources": [
                    "https://www.hillrom.com/en/support/",
                    "https://www.manualslib.com/brand/hill-rom/"
                ]
            },
            "pcenturyk3256": {
                "product_start_year": 1995,
                "sources": [
                    "https://www.hillrom.com/en/support/",
                    "https://www.manualslib.com/brand/hill-rom/"
                ]
            },
            "p1440": {
                "product_start_year": 1992,
                "sources": [
                    "https://www.hillrom.com/en/support/",
                    "https://www.manualslib.com/brand/hill-rom/"
                ]
            }
        }
    },
    "hospira": {
        "founded_year": 2004,
        "models": {
            "pluma+": {
                "product_start_year": 2004,
                "sources": [
                    "https://www.icumed.com/products/infusion-systems/",
                    "https://www.manualslib.com/brand/hospira/"
                ]
            }
        }
    },
    "jiangmen dacheng": {
        "founded_year": 2008,
        "models": {
            "iob-507": {
                "product_start_year": 2010,
                "sources": [
                    "https://dachengmedical.en.made-in-china.com/",
                    "https://www.manualslib.com/brand/dacheng/"
                ]
            }
        }
    },
    "lab corp": {
        "founded_year": 1978,
        "models": {
            "642e": {
                "product_start_year": 1998,
                "sources": [
                    "https://druckerdiagnostics.com/support/642e-support/",
                    "https://www.manualslib.com/brand/drucker-diagnostics/"
                ]
            }
        }
    },
    "linet": {
        "founded_year": 1990,
        "models": {
            "eleganza 3": {
                "product_start_year": 2004,
                "sources": [
                    "https://www.linet.com/en/medical/beds/icu-beds/eleganza-3",
                    "https://www.manualslib.com/brand/linet/"
                ]
            },
            "eleganza 4": {
                "product_start_year": 2012,
                "sources": [
                    "https://www.linet.com/en/medical/beds/icu-beds/eleganza-4",
                    "https://www.manualslib.com/brand/linet/"
                ]
            }
        }
    },
    "masimo": {
        "founded_year": 1989,
        "models": {
            "rad8": {
                "product_start_year": 2005,
                "sources": [
                    "https://www.masimo.com/products/bedside-monitors/rad-8/",
                    "https://www.manualslib.com/products/Masimo-Rad-8-8441975.html"
                ]
            }
        }
    },
    "mindray": {
        "founded_year": 1991,
        "models": {
            "benevision n15": {
                "product_start_year": 2015,
                "sources": [
                    "https://www.mindray.com/na/products/patient-monitoring-and-life-support/patient-monitors/benevision-n-series/",
                    "https://www.manualslib.com/manual/2903512/Mindray-Benevision-N15.html"
                ]
            },
            "epm12ma": {
                "product_start_year": 2018,
                "sources": [
                    "https://www.mindray.com/na/products/patient-monitoring-and-life-support/patient-monitors/epm-series/",
                    "https://www.manualslib.com/manual/2903513/Mindray-Epm-Series.html"
                ]
            }
        }
    },
    "olympus": {
        "founded_year": 1919,
        "models": {
            "cv190": {
                "product_start_year": 2012,
                "sources": [
                    "https://www.olympusprofesional.com/medical/endoscopes/cv-190.html",
                    "https://www.manualslib.com/manual/1628172/Olympus-Evis-Exera-Iii-Cv-190.html"
                ]
            }
        }
    },
    "philips": {
        "founded_year": 1891,
        "models": {
            "mx500": {
                "product_start_year": 2013,
                "sources": [
                    "https://www.manualslib.com/manual/2012351/Philips-Intellivue-Mx500.html",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Philips_IntelliVue_MX500_-_Service_manual.pdf"
                ]
            },
            "intellivue mp20": {
                "product_start_year": 2004,
                "sources": [
                    "https://www.manualslib.com/manual/1218520/Philips-Intellivue-Mp20.html",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Philips_IntelliVue_MP20-MP30_-_Service_manual.pdf"
                ]
            },
            "intellivue mp30": {
                "product_start_year": 2004,
                "sources": [
                    "https://www.manualslib.com/manual/1218520/Philips-Intellivue-Mp20.html",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Philips_IntelliVue_MP20-MP30_-_Service_manual.pdf"
                ]
            },
            "intellivue mp50": {
                "product_start_year": 2004,
                "sources": [
                    "https://www.manualslib.com/manual/1218520/Philips-Intellivue-Mp20.html",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Philips_IntelliVue_MP20-MP30_-_Service_manual.pdf"
                ]
            },
            "intellivue mx40": {
                "product_start_year": 2011,
                "sources": [
                    "https://www.manualslib.com/manual/1239851/Philips-Intellivue-Mx40.html",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Philips_IntelliVue_MX40_-_Service_manual.pdf"
                ]
            },
            "m3002a": {
                "product_start_year": 2007,
                "sources": [
                    "https://www.manualslib.com/manual/1218521/Philips-M3002a.html",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Philips_IntelliVue_M3002A_-_Service_manual.pdf"
                ]
            }
        }
    },
    "stryker": {
        "founded_year": 1941,
        "models": {
            "1061": {
                "product_start_year": 1995,
                "sources": [
                    "https://www.stryker.com/us/en/acute-care/products/prime-series.html",
                    "https://www.manualslib.com/manual/881643/Stryker-Prime-1115.html"
                ]
            },
            "1115": {
                "product_start_year": 2012,
                "sources": [
                    "https://www.stryker.com/us/en/acute-care/products/prime-series.html",
                    "https://www.manualslib.com/manual/881643/Stryker-Prime-1115.html"
                ]
            }
        }
    },
    "thermo scientific": {
        "founded_year": 2006,
        "models": {
            "smartvue915": {
                "product_start_year": 2011,
                "sources": [
                    "https://www.thermofisher.com/order/catalog/product/SV915-10",
                    "https://www.manualslib.com/manual/1220977/Thermo-Scientific-Smartvue.html"
                ]
            }
        }
    },
    "unico": {
        "founded_year": 1991,
        "models": {
            "g380pl led": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.unicomicroscopes.com/g380-series/",
                    "https://www.manualslib.com/manual/1545620/Unico-G380.html"
                ]
            }
        }
    },
    "welch allyn": {
        "founded_year": 1915,
        "models": {
            "filac3000": {
                "product_start_year": 2009,
                "sources": [
                    "https://reveremedical.com/how-to-read-a-welch-allyn-serial-number/",
                    "https://www.frankshospitalworkshop.com/equipment/documents/thermometers/service_manuals/Welch_Allyn_SureTemp_Plus_-_Service_manual.pdf"
                ]
            },
            "spot vital signs": {
                "product_start_year": 2000,
                "sources": [
                    "https://reveremedical.com/how-to-read-a-welch-allyn-serial-number/",
                    "https://www.frankshospitalworkshop.com/equipment/documents/patient_monitors/service_manuals/Welch_Allyn_Spot_Vital_Signs_-_Service_manual.pdf"
                ]
            },
            "suretempplus": {
                "product_start_year": 2002,
                "sources": [
                    "https://reveremedical.com/how-to-read-a-welch-allyn-serial-number/",
                    "https://www.frankshospitalworkshop.com/equipment/documents/thermometers/service_manuals/Welch_Allyn_SureTemp_Plus_-_Service_manual.pdf"
                ]
            }
        }
    },
    "zoll": {
        "founded_year": 1980,
        "models": {
            "aedplus": {
                "product_start_year": 2001,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "m series": {
                "product_start_year": 1998,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "propaq md": {
                "product_start_year": 2010,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "r series": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "r series als": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "r series plus": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "rseries": {
                "product_start_year": 2008,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            },
            "x series": {
                "product_start_year": 2012,
                "sources": [
                    "https://www.aedsuperstore.com/assets/images/PDFs/ZOLL-Serial-Number-Guide.pdf",
                    "https://www.zoll.com/-/media/public-site/files/pdf/technical-service-bulletins/serial-number-identification.ashx"
                ]
            }
        }
    }
}

# Helper functions

def get_canonical_mfg_key(mfg):
    if not mfg:
        return None
    mfg_lower = mfg.lower().strip()
    
    # Handle common variants
    if "arjo" in mfg_lower:
        return "arjo"
    if "adc" in mfg_lower or "american diagnostic" in mfg_lower:
        return "american diagnostic"
    if "baxter" in mfg_lower:
        return "baxter"
    if "biosonic" in mfg_lower:
        return "biosonic"
    if "cogentix" in mfg_lower:
        return "cogentix"
    if "covidien" in mfg_lower:
        return "covidien"
    if "edan" in mfg_lower:
        return "edan"
    if "exergen" in mfg_lower:
        return "exergen"
    if "ge" in mfg_lower or "general electric" in mfg_lower:
        return "ge healthcare"
    if "hillrom" in mfg_lower or "hill rom" in mfg_lower or "hill-rom" in mfg_lower:
        return "hillrom"
    if "hospira" in mfg_lower:
        return "hospira"
    if "jiangmen" in mfg_lower or "dacheng" in mfg_lower:
        return "jiangmen dacheng"
    if "lab corp" in mfg_lower or "labcorp" in mfg_lower:
        return "lab corp"
    if "linet" in mfg_lower:
        return "linet"
    if "masimo" in mfg_lower:
        return "masimo"
    if "mindray" in mfg_lower:
        return "mindray"
    if "olympus" in mfg_lower:
        return "olympus"
    if "philips" in mfg_lower:
        return "philips"
    if "stryker" in mfg_lower:
        return "stryker"
    if "thermo" in mfg_lower:
        return "thermo scientific"
    if "unico" in mfg_lower:
        return "unico"
    if "welch allyn" in mfg_lower:
        return "welch allyn"
    if "zoll" in mfg_lower:
        return "zoll"
        
    # Standard fuzzy substring matching
    for key in METADATA.keys():
        if key in mfg_lower:
            return key
            
    return None

def normalize_model_name(model):
    if not model:
        return ""
    return re.sub(r'\s+', ' ', model.lower().strip())

def get_model_metadata(mfg, model):
    mfg_key = get_canonical_mfg_key(mfg)
    if not mfg_key or mfg_key not in METADATA:
        return None
        
    mfg_data = METADATA[mfg_key]
    model_norm = normalize_model_name(model)
    
    # Try direct lookup
    if model_norm in mfg_data["models"]:
        res = mfg_data["models"][model_norm].copy()
        res["founded_year"] = mfg_data["founded_year"]
        res["manufacturer_canonical"] = mfg_key
        return res
        
    # Try substring lookup
    for m_key, m_val in mfg_data["models"].items():
        if m_key in model_norm or model_norm in m_key:
            res = m_val.copy()
            res["founded_year"] = mfg_data["founded_year"]
            res["manufacturer_canonical"] = mfg_key
            return res
            
    return None

def validate_mfg_date(mfg, model, year):
    """
    Validates a year against stored metadata bounds.
    Returns (is_valid, reason)
    """
    meta = get_model_metadata(mfg, model)
    if not meta:
        # Default safety bounds
        if year < 1850 or year > 2026:
            return False, f"Year {year} is outside global historical boundaries (1850-2026)."
        return True, "No metadata available for this model/manufacturer; passed default sanity check."
        
    founded = meta["founded_year"]
    start = meta["product_start_year"]
    
    if year < founded:
        return False, f"Year {year} is invalid because the manufacturer was founded later in {founded}."
        
    if year < start:
        return False, f"Year {year} is invalid because the product did not begin production until {start}."
        
    if year > 2026:
        return False, f"Year {year} is in the future relative to the dataset context (max 2026)."
        
    return True, "Valid"

def guess_manufacturer_locally(model, sn):
    """
    Attempts to guess the manufacturer based on model name keywords or serial number patterns.
    Returns the canonical manufacturer name (string) or None if no match.
    """
    model_norm = normalize_model_name(model)
    sn_upper = sn.upper().strip() if sn else ""
    
    # 1. Check model keywords
    if model_norm:
        if "eleganza" in model_norm:
            return "Linet"
        if "spectrum iq" in model_norm or "spectrm iq" in model_norm:
            return "Baxter Healthcare Corp."
        if "flowtron" in model_norm:
            return "Arjo Inc."
        if "rapidvac" in model_norm:
            return "Covidien"
        if "tat5000" in model_norm or "tat 5000" in model_norm:
            return "Exergen"
        if "apex pro" in model_norm or "patient data module" in model_norm or "pdm" in model_norm:
            return "GE Healthcare"
        if "filac" in model_norm or "suretemp" in model_norm or "spot vital" in model_norm:
            return "Welch Allyn"
        if any(x in model_norm for x in ["aed", "propaq", "r series", "x series", "m series", "rseries"]):
            return "ZOLL Medical"
        if any(x in model_norm for x in ["intellivue", "mx40", "mx500", "m3002a"]):
            return "Philips"
        if "cv190" in model_norm or "cv-190" in model_norm:
            return "Olympus"
        if "rad8" in model_norm or "rad-8" in model_norm:
            return "Masimo"
        if "cst-4000" in model_norm or "cst-5000" in model_norm or "cst4000" in model_norm or "cst5000" in model_norm:
            return "Cogentix Medical"
        if "642e" in model_norm:
            return "Lab Corp."
        if "g380pl" in model_norm:
            return "Unico"
        if "ce 1434" in model_norm or "ce1434" in model_norm:
            return "American Diagnostic"
        if "iob-507" in model_norm or "iob507" in model_norm:
            return "Jiangmen Dacheng"
        if "smartvue" in model_norm:
            return "Thermo Scientific"
        if "1061" in model_norm or "1115" in model_norm:
            return "Stryker"
        if "benevision" in model_norm or "epm12ma" in model_norm or "epm-12m" in model_norm:
            return "Mindray"
        if "uc95" in model_norm:
            return "BioSonic"

    # 2. Check serial number patterns
    if sn_upper:
        if re.match(r'^WU20\d{6}', sn_upper) or sn_upper.startswith("WU20") or sn_upper.endswith("EN"):
            return "Jiangmen Dacheng"
        if re.match(r'^DE\d', sn_upper) or sn_upper.startswith("DE"):
            return "Philips"
        if any(sn_upper.startswith(prefix) for prefix in ["AR13", "AR18", "AR20", "AR21", "AR22", "AR25", "AF11", "AF16", "AF17", "AF18", "AF19", "AF23", "AF24", "AF25", "AI10", "AI11", "AI15", "T03", "T04", "T08", "T09", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "X18", "X19", "X22", "X23", "X25", "D16", "3T13"]):
            return "ZOLL Medical"
        if sn_upper.startswith("CS17") or sn_upper.startswith("CS07"):
            return "Cogentix Medical"
        if sn_upper.endswith("LB348") or sn_upper.endswith("LB328") or "LB" in sn_upper:
            return "Lab Corp."
        if sn_upper.startswith("A153") or sn_upper.startswith("A15"):
            return "Exergen"
        if sn_upper.startswith("RTS14") or sn_upper.startswith("RT90") or sn_upper.startswith("RT91") or sn_upper.startswith("SA31") or sn_upper.startswith("SPX18"):
            return "GE Healthcare"
        if sn_upper.startswith("A11") or sn_upper.startswith("A12") or sn_upper.startswith("A14") or sn_upper.startswith("A16") or sn_upper.startswith("A20") or sn_upper.startswith("A10") or sn_upper.startswith("20150") or sn_upper.startswith("20081") or sn_upper.startswith("2303") or sn_upper.startswith("0743"):
            return "Welch Allyn"
        if sn_upper.startswith("21000") or sn_upper.startswith("2100"):
            return "Arjo Inc."
        if sn_upper.startswith("375") or sn_upper.startswith("382") or sn_upper.startswith("381") or sn_upper.startswith("383") or sn_upper.startswith("378") or sn_upper.startswith("380"):
            return "Baxter Healthcare Corp."
        if sn_upper.startswith("1304") or sn_upper.startswith("1311") or sn_upper.startswith("130") or sn_upper.startswith("131"):
            return "BioSonic"
        if sn_upper.startswith("VL01"):
            return "Covidien"
        if sn_upper.startswith("1743") or sn_upper.startswith("1744") or sn_upper.startswith("1745") or sn_upper.startswith("1748"):
            return "Hospira"
        if sn_upper.startswith("M192") or sn_upper.startswith("M19"):
            return "Masimo"
        if sn_upper.startswith("7500") or sn_upper.startswith("7550"):
            return "Olympus"
        if sn_upper.startswith("202100") or sn_upper.startswith("202200") or sn_upper.startswith("201700") or sn_upper.startswith("1090"):
            return "Stryker"
        if sn_upper.startswith("1817") or sn_upper.startswith("1835") or sn_upper.startswith("181"):
            return "Thermo Scientific"
        if sn_upper.startswith("G38L"):
            return "Unico"
        if sn_upper.startswith("202101") or sn_upper.startswith("202002") or sn_upper.startswith("202402") or sn_upper.startswith("202403"):
            return "Linet"
        if sn_upper.startswith("WU20"):
            return "Jiangmen Dacheng"
        if sn_upper.startswith("2219") or sn_upper.startswith("C241"):
            return "American Diagnostic"
        if sn_upper.startswith("FS-28") or sn_upper.startswith("F5-28") or sn_upper.startswith("FS-11") or sn_upper.startswith("F5-11") or sn_upper.startswith("AH9-3") or sn_upper.startswith("AH9-2"):
            return "Mindray"
            
    return None
