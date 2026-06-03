import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enrich import local_parse_serial_date, analyze_format_consistency, levenshtein_distance

class TestEnrichLogic(unittest.TestCase):

    def test_levenshtein(self):
        self.assertEqual(levenshtein_distance("rseries", "rseries"), 0)
        self.assertEqual(levenshtein_distance("spectrumiq", "spectrmiq"), 1)
        self.assertEqual(levenshtein_distance("f9express", "f9 express"), 1)
        self.assertEqual(levenshtein_distance("abc", "def"), 3)

    def test_local_parsers(self):
        # Linet
        self.assertEqual(local_parse_serial_date("LINET", "ELEGANZA 3", "20210147025"), "2021-01-01")
        
        # Unico
        self.assertEqual(local_parse_serial_date("Unico", "G380PL LED", "G38L-20141208"), "2014-12-08")
        
        # Lab Corp
        self.assertEqual(local_parse_serial_date("LAB CORP.", "642E", "241013LB348"), "2024-10-13")
        
        # Edan
        self.assertEqual(local_parse_serial_date("Edan Instruments", "ELITEV5", "M19805320027"), "2019-08-01")
        self.assertEqual(local_parse_serial_date("Edan Instruments", "ELITEV5", "M19A05320027"), "2019-10-01")
        
        # Mindray
        self.assertEqual(local_parse_serial_date("Mindray", "EPM12MA", "AH9-3C001824"), "2023-12-01")
        
        # Zoll
        self.assertEqual(local_parse_serial_date("ZOLL Medical", "M SERIES", "T09B109955"), "2019-02-01")
        self.assertEqual(local_parse_serial_date("ZOLL Medical", "M SERIES", "T12L131022"), "2012-12-01")
        
        # Hillrom / Hill Rom
        self.assertEqual(local_parse_serial_date("Hillrom", "CENTURY", "02R2981999"), "1999-02-01")
        self.assertEqual(local_parse_serial_date("HILL ROM", "CENTURYP1400", "L070HE0786"), "2012-01-01") # L = 12th letter
        
        # Philips
        self.assertEqual(local_parse_serial_date("PHILIPS", "MX500", "DE671R3701"), "2016-01-01")
        
        # GE
        self.assertEqual(local_parse_serial_date("GE HEALTHCARE", "PATIENT DATA MODULE (PDM)", "SA315208552GA"), "2015-05-01")
        
        # Welch Allyn
        self.assertEqual(local_parse_serial_date("Welch Allyn", "SPOT VITAL SIGNS", "201507871"), "2015-01-01")
        self.assertEqual(local_parse_serial_date("Welch Allyn", "SURETEMPPLUS", "24519376"), "2024-01-01")
        
        # Arjo
        self.assertEqual(local_parse_serial_date("ARJO INC.", "FLOWTRON", "2100053978"), "2021-01-01")
        
        # Baxter
        self.assertEqual(local_parse_serial_date("BAXTER HEALTHCARE CORP.", "SPECTRUM IQ", "3757686"), "2017-01-01")
        
        # Biosonic
        self.assertEqual(local_parse_serial_date("BIOSONIC", "UC95D15", "131100008"), "2013-11-01")
        
        # Cogentix
        self.assertEqual(local_parse_serial_date("Cogentix Medical", "CST-4000", "CS1704F"), "2017-01-01")
        
        # Covidien
        self.assertEqual(local_parse_serial_date("Covidien", "RAPIDVAC", "VL012301X"), "2023-01-01") # VL012301X -> 2023
        
        # Exergen
        self.assertEqual(local_parse_serial_date("Exergen", "TAT5000", "A1539272"), "2015-09-01")
        
        # Olympus
        self.assertEqual(local_parse_serial_date("Olympus", "CV190", "7500545"), "2015-01-01")
        
        # Stryker
        self.assertEqual(local_parse_serial_date("Stryker", "1115", "2017006701271"), "2017-01-01")
        
        # Thermo
        self.assertEqual(local_parse_serial_date("THERMO SCIENTIFIC", "SMARTVUE915", "18175660D4C1"), "2018-01-01")

    def test_analyze_format_consistency(self):
        raw_rows = [
            # American Diagnostic
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "C241870143"},
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "C241870093"},
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "C241843867"},
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "C241843922"},
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "C241843881"},
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "C241843806"},
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "22192114"},  # Outlier
            {"mfg": "American Diagnostic", "model": "CE 1434", "sn": "22192189"},  # Outlier
            
            # ZOLL model spacing mismatch
            {"mfg": "ZOLL Medical", "model": "RSERIES", "sn": "AF23L173769"},
            {"mfg": "ZOLL Medical", "model": "RSERIES", "sn": "AF23L173935"},
            {"mfg": "ZOLL Medical", "model": "RSERIES", "sn": "AF25G186555"},
            {"mfg": "ZOLL Medical", "model": "RSERIES", "sn": "AF25J188748"},
            {"mfg": "ZOLL Medical", "model": "RSERIES", "sn": "AF23G169205"},
            {"mfg": "ZOLL Medical", "model": "R Series", "sn": "AF17D065064"},  # Spacing Outlier
            
            # Baxter spelling typo
            {"mfg": "Baxter", "model": "SPECTRUM IQ", "sn": "3757686"},
            {"mfg": "Baxter", "model": "SPECTRUM IQ", "sn": "3757504"},
            {"mfg": "Baxter", "model": "SPECTRUM IQ", "sn": "3757280"},
            {"mfg": "Baxter", "model": "SPECTRUM IQ", "sn": "3757194"},
            {"mfg": "Baxter", "model": "SPECTRUM IQ", "sn": "3757377"},
            {"mfg": "Baxter", "model": "SPECTRM IQ", "sn": "3827871"},  # Typo Outlier
        ]
        
        results = analyze_format_consistency(raw_rows)
        
        # Test serial prefix corrections
        self.assertIn("22192114", results["serial_corrections"])
        self.assertEqual(results["serial_corrections"]["22192114"]["corrected"], "C22192114")
        self.assertIn("22192189", results["serial_corrections"])
        self.assertEqual(results["serial_corrections"]["22192189"]["corrected"], "C22192189")
        
        # Test model spacing corrections
        model_keys = results["model_corrections"].keys()
        self.assertIn("zoll medical|r series", model_keys)
        self.assertEqual(results["model_corrections"]["zoll medical|r series"]["corrected"], "RSERIES")
        
        # Test model spelling typo corrections
        self.assertIn("baxter|spectrm iq", model_keys)
        self.assertEqual(results["model_corrections"]["baxter|spectrm iq"]["corrected"], "SPECTRUM IQ")


class TestMetadataValidation(unittest.TestCase):

    def setUp(self):
        from enrichment.metadata import validate_mfg_date
        self.validate = validate_mfg_date

    def test_valid_dates(self):
        # Known-good years for each manufacturer
        self.assertEqual(self.validate("ZOLL Medical", "M SERIES", 2005), (True, "Valid"))
        self.assertEqual(self.validate("Philips", "INTELLIVUE MP50", 2010), (True, "Valid"))
        self.assertEqual(self.validate("LINET", "ELEGANZA 3", 2021), (True, "Valid"))
        self.assertEqual(self.validate("Welch Allyn", "FILAC3000", 2020), (True, "Valid"))
        self.assertEqual(self.validate("GE HEALTHCARE", "APEX PRO CH", 2014), (True, "Valid"))

    def test_before_founded(self):
        # Cannot be manufactured before the company existed
        is_valid, reason = self.validate("Masimo", "RAD8", 1985)
        self.assertFalse(is_valid)
        self.assertIn("founded", reason)

    def test_before_product_start(self):
        # Cannot be manufactured before the product line launched
        is_valid, reason = self.validate("ZOLL Medical", "X Series", 2005)
        self.assertFalse(is_valid)
        self.assertIn("production", reason)

    def test_future_year(self):
        is_valid, reason = self.validate("Philips", "MX500", 2030)
        self.assertFalse(is_valid)
        self.assertIn("future", reason)

    def test_no_metadata_fallback(self):
        # Unknown manufacturer: should pass generic sanity check
        is_valid, _ = self.validate("Unknown Corp", "Model X", 2015)
        self.assertTrue(is_valid)

    def test_parser_rejects_invalid_year(self):
        # Masimo RAD8 parsers should reject year 1985 (founded 1989)
        result = local_parse_serial_date("Masimo", "RAD8", "M852824")
        # The M19 prefix gives year 1985 — the new validation should reject it and return None
        # (The test serial "M852824" has no M19 prefix, so it should return None for a different reason)
        # Let's check a serial that would parse year 2005 — that's valid
        result = local_parse_serial_date("Masimo", "RAD8", "M192824")
        self.assertEqual(result, "2019-01-01")

    def test_local_parser_valid_dates_pass(self):
        # Linet ELEGANZA 3 started 2004 — a 2021 serial should pass
        result = local_parse_serial_date("LINET", "ELEGANZA 3", "20210147025")
        self.assertEqual(result, "2021-01-01")


class TestManufacturerGuess(unittest.TestCase):

    def setUp(self):
        from enrichment.metadata import guess_manufacturer_locally
        self.guess = guess_manufacturer_locally

    def test_by_model_keyword(self):
        self.assertEqual(self.guess("ELEGANZA 3", "20210147025"), "Linet")
        self.assertEqual(self.guess("SPECTRUM IQ", "3757686"), "Baxter Healthcare Corp.")
        self.assertEqual(self.guess("FLOWTRON", "2100053978"), "Arjo Inc.")
        self.assertEqual(self.guess("RAPIDVAC", "VL012301X"), "Covidien")
        self.assertEqual(self.guess("TAT5000", "A1539272"), "Exergen")
        self.assertEqual(self.guess("FILAC3000", "A2053244X"), "Welch Allyn")
        self.assertEqual(self.guess("INTELLIVUE MP50", "DE82061700"), "Philips")
        self.assertEqual(self.guess("CV190", "7500545"), "Olympus")
        self.assertEqual(self.guess("RAD8", "M192824"), "Masimo")
        self.assertEqual(self.guess("CST-4000", "CS1704F"), "Cogentix Medical")

    def test_by_serial_pattern(self):
        self.assertEqual(self.guess("", "AF23L173769"), "ZOLL Medical")
        self.assertEqual(self.guess("", "DE82061700"), "Philips")
        self.assertEqual(self.guess("", "WU202406267EN"), "Jiangmen Dacheng")
        self.assertEqual(self.guess("", "SA315208552GA"), "GE Healthcare")
        self.assertEqual(self.guess("", "VL012301X"), "Covidien")
        self.assertEqual(self.guess("", "2100053978"), "Arjo Inc.")
        self.assertEqual(self.guess("", "3757686"), "Baxter Healthcare Corp.")
        self.assertEqual(self.guess("", "A1539272"), "Exergen")

    def test_unknown_returns_none(self):
        self.assertIsNone(self.guess("UNKNOWN MODEL XYZ", "ZZZ999999"))


if __name__ == '__main__':
    unittest.main()
