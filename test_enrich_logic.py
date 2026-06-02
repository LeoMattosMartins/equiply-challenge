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

if __name__ == '__main__':
    unittest.main()
