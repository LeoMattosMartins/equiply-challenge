import sys

# Re-exporting all public interface items from sub-modules to maintain 100% backward compatibility
from enrichment.utils import (
    load_json_cache,
    save_json_cache,
    TYPES_CACHE_FILE,
    DATES_CACHE_FILE,
    normalize_date
)
from enrichment.parsers import local_parse_serial_date
from enrichment.analyzer import analyze_format_consistency, levenshtein_distance
from enrichment.pipeline import enrich_csv

if __name__ == '__main__':
    # CLI execution entrypoint
    input_file = 'challenge_data-v1.csv'
    output_file = 'challenge_data_enriched.csv'
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ('--help', '-h'):
            print("Usage: python enrich.py [input_csv] [output_csv]")
            sys.exit(0)
            
        args = sys.argv[1:]
        if len(args) >= 1:
            input_file = args[0]
        if len(args) >= 2:
            output_file = args[1]
            
    enrich_csv(input_file, output_file)
