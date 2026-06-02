import io
import os
import csv
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from enrich import load_json_cache, save_json_cache, TYPES_CACHE_FILE, DATES_CACHE_FILE, enrich_csv

app = FastAPI(title="Equiply Equipment Data Enrichment API")

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RuleOverride(BaseModel):
    key: str  # mfg|model lowercased
    device_type: str

@app.get("/api/rules")
def get_rules():
    """
    Returns the current cached rules/mappings.
    """
    return load_json_cache(TYPES_CACHE_FILE)

@app.post("/api/rules/override")
def override_rule(override: RuleOverride):
    """
    Allows the user to manually override a device type mapping.
    """
    cache = load_json_cache(TYPES_CACHE_FILE)
    key = override.key.lower().strip()
    if key in cache:
        cache[key]["device_type"] = override.device_type
    else:
        cache[key] = {
            "device_type": override.device_type,
            "probable_typo": False
        }
    save_json_cache(TYPES_CACHE_FILE, cache)
    return {"status": "success", "message": f"Rule updated for {key}"}

@app.post("/api/enrich")
async def enrich_file(file: UploadFile = File(...), x_openai_key: str = Header(None)):
    """
    Upload a CSV, enrich it using the Python engine, and return sorted JSON data and stats.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
        
    try:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_input:
            shutil.copyfileobj(file.file, temp_input)
            temp_input_path = temp_input.name
            
        temp_output_path = temp_input_path + "_enriched.csv"
        
        # Run the enrichment engine
        api_key = x_openai_key or os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI_API_KEY")
        enrich_csv(temp_input_path, temp_output_path, api_key)
        
        # Read the enriched CSV back to return JSON
        rows = []
        device_counts = {}
        total_count = 0
        total_confidence = 0.0
        
        types_cache = load_json_cache(TYPES_CACHE_FILE)
        dates_cache = load_json_cache(DATES_CACHE_FILE)
        
        with open(temp_output_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                dtype = row.get('device_type', 'Medical Device')
                device_counts[dtype] = device_counts.get(dtype, 0) + 1
                total_count += 1
                
                # Retrieve confidence for this row
                mfg = row.get('manufacturer', '')
                model = row.get('model', '')
                sn = row.get('serial number') or row.get('serial_number') or ''
                
                type_key = f"{mfg.lower()}|{model.lower()}"
                date_key = f"{mfg.lower()}|{model.lower()}|{sn.lower()}"
                
                type_info = types_cache.get(type_key, {})
                date_info = dates_cache.get(date_key, {})
                
                t_conf = type_info.get("confidence", 1.0) if isinstance(type_info, dict) else 1.0
                d_conf = date_info.get("confidence", 1.0) if isinstance(date_info, dict) else 1.0
                total_confidence += (t_conf + d_conf) / 2.0
                
        # Clean up temp files
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
            
        # Get probable typos
        probable_typos = []
        for key, val in types_cache.items():
            if val.get("probable_typo"):
                parts = key.split("|", 1)
                mfg = parts[0]
                model = parts[1] if len(parts) > 1 else ""
                probable_typos.append({
                    "key": key,
                    "manufacturer": mfg.upper(),
                    "model": model.upper(),
                    "device_type": val.get("device_type", "Medical Device"),
                    "confidence": round(val.get("confidence", 1.0) * 100, 1)
                })
                
        # Calculate metrics for the pie chart
        metrics = []
        for dtype, count in device_counts.items():
            percentage = round((count / total_count) * 100, 2) if total_count > 0 else 0
            metrics.append({
                "device_type": dtype,
                "count": count,
                "percentage": percentage
            })
            
        # Sort metrics by count descending
        metrics.sort(key=lambda x: x["count"], reverse=True)
        
        avg_conf = round((total_confidence / total_count) * 100, 2) if total_count > 0 else 100.0
            
        # Read formatting corrections from text file
        formatting_corrections = ""
        if os.path.exists("formatting_corrections.txt"):
            try:
                with open("formatting_corrections.txt", "r", encoding="utf-8") as f_corr:
                    formatting_corrections = f_corr.read()
            except Exception as e:
                print(f"Error reading formatting_corrections.txt: {e}")

        return {
            "total_records": total_count,
            "data": rows,
            "metrics": metrics,
            "probable_typos": probable_typos,
            "average_confidence": avg_conf,
            "formatting_corrections": formatting_corrections
        }
        
    except Exception as e:
        # Ensure cleanup in case of error
        try:
            if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if 'temp_output_path' in locals() and os.path.exists(temp_output_path):
                os.remove(temp_output_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

# Serve frontend build in production if available
frontend_dist_path = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
