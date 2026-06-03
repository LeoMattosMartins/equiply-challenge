import json
import sys
from concurrent.futures import ThreadPoolExecutor

def search_device_type_web(mfg, model):
    try:
        from duckduckgo_search import DDGS
        query = f'"{mfg}" "{model}" medical device product classification type'
        print(f"Searching web for type classification: {query}...")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        snippets = []
        for r in results:
            snippets.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}")
        return "\n\n".join(snippets)
    except Exception as e:
        print(f"Web search failed for type of {mfg} | {model}: {e}", file=sys.stderr)
        return "No web context found."

def search_serial_date_web(mfg, model):
    try:
        from duckduckgo_search import DDGS
        query = f'"{mfg}" "{model}" serial number format manufactured date coding'
        print(f"Searching web for serial date format: {query}...")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        snippets = []
        for r in results:
            snippets.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}")
        return "\n\n".join(snippets)
    except Exception as e:
        print(f"Web search failed for serial date of {mfg} | {model}: {e}", file=sys.stderr)
        return "No web context found."

def query_device_type(model_name, mfg, model, search_context, api_key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        We are determining the device type and typo status of a medical equipment model.
        We performed a web search for manufacturer '{mfg}' and model '{model}' and found these web snippets:
        {search_context}

        Please analyze the manufacturer, model, and search results to determine:
        1. The standardized 'device_type' (e.g. 'Pulse Oximeter', 'Infusion Pump', 'Hospital Bed').
           - If the search results are empty or do not mention the device type, or mention 'Unknown Device', you MUST use your internal LLM knowledge to make an educated guess.
           - DO NOT return 'Unknown Device' or 'Unknown' or generic 'Medical Device' if you can classify it. You are an expert in medical equipment.
           - Be concise (2-4 words).
        2. Whether the model '{model}' exists under '{mfg}' or is a 'probable_typo' (set to true if the web search context suggests it doesn't exist under this name/manufacturer, if the model name is mismatched or contains clear typos).

        Return ONLY a JSON object matching this structure:
        {{
            "device_type": "Standardized Name",
            "probable_typo": false
        }}
        """
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=1000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error querying type for model {model_name} on {mfg} | {model}: {e}", file=sys.stderr)
        return None

def resolve_device_type_consensus(mfg, model, api_key):
    search_context = search_device_type_web(mfg, model)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_mini = executor.submit(query_device_type, "gpt-5.4-mini", mfg, model, search_context, api_key)
        future_nano = executor.submit(query_device_type, "gpt-5.4-nano", mfg, model, search_context, api_key)
        
        res_mini = future_mini.result()
        res_nano = future_nano.result()
        
    if not res_mini and not res_nano:
        return {"device_type": "Medical Device", "probable_typo": False, "confidence": 0.1}
        
    if not res_nano:
        return {"device_type": res_mini.get("device_type", "Medical Device"), "probable_typo": res_mini.get("probable_typo", False), "confidence": 0.5}
    if not res_mini:
        return {"device_type": res_nano.get("device_type", "Medical Device"), "probable_typo": res_nano.get("probable_typo", False), "confidence": 0.5}
        
    concur_type = res_mini.get("device_type") == res_nano.get("device_type")
    concur_typo = res_mini.get("probable_typo") == res_nano.get("probable_typo")
    
    if concur_type and concur_typo:
        confidence = 0.95
    else:
        confidence = 0.60
        
    return {
        "device_type": res_mini.get("device_type", "Medical Device"),
        "probable_typo": res_mini.get("probable_typo", False),
        "confidence": confidence
    }

def query_serial_dates(model_name, mfg, model, sns, search_context, api_key):
    try:
        from openai import OpenAI
        from enrichment.metadata import get_model_metadata
        client = OpenAI(api_key=api_key)
        
        meta = get_model_metadata(mfg, model)
        metadata_context = ""
        if meta:
            metadata_context = f"""
        - Company Founded Year: {meta['founded_year']}
        - Product '{model}' Production Start Year: {meta['product_start_year']}
        - Documented Serial Format Reference Sources:
          * {meta['sources'][0]}
          * {meta['sources'][1]}
            """
        
        prompt = f"""
        We are extracting the manufacturing date for medical equipment serial numbers.
        We performed a web search for manufacturer '{mfg}' and model '{model}' to find serial number formats and found these snippets:
        {search_context}

        We have verified company and product metadata for context:
        {metadata_context}

        Here is a list of serial numbers:
        {json.dumps(sns)}

        Please analyze the serial numbers, verified metadata, and search snippets to extract or estimate the manufactured date for each serial number.
        - Validate the dates: The manufacturing year MUST NOT be before the company was founded ({meta['founded_year'] if meta else '1800'}) or before the product started production ({meta['product_start_year'] if meta else '1900'}). It must also not be after 2026.
        - Try all different date formats and coding schemes commonly used by '{mfg}' or in medical hardware (e.g., YYMMDD, YYYYMMDD, YYWW, YYMonthCode, year at the end, year at the beginning, week-to-month mapping, etc.) to extract the year and month.
        - If the date is not extractable from the serial number format, make an educated guess of the manufacture date based on the production years of '{model}'.
        - Format each date strictly in YYYY-MM-DD format (if day/month is not extractable, default to YYYY-MM-01 or YYYY-01-01).

        Return ONLY a JSON object matching this structure:
        {{
            "serial_dates": {{
                "SN1": "YYYY-MM-DD",
                "SN2": "YYYY-MM-DD"
            }}
        }}
        """
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=1000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error querying date for model {model_name} on {mfg} | {model}: {e}", file=sys.stderr)
        return None

def resolve_serial_dates_consensus(mfg, model, sns, api_key):
    search_context = search_serial_date_web(mfg, model)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_mini = executor.submit(query_serial_dates, "gpt-5.4-mini", mfg, model, sns, search_context, api_key)
        future_nano = executor.submit(query_serial_dates, "gpt-5.4-nano", mfg, model, sns, search_context, api_key)
        
        res_mini = future_mini.result()
        res_nano = future_nano.result()
        
    if not res_mini and not res_nano:
        return {"serial_dates": {sn: "1900-01-01" for sn in sns}, "confidence": 0.1}
        
    if not res_nano:
        return {"serial_dates": res_mini.get("serial_dates", {}), "confidence": 0.5}
    if not res_mini:
        return {"serial_dates": res_nano.get("serial_dates", {}), "confidence": 0.5}
        
    dates_mini = res_mini.get("serial_dates", {})
    dates_nano = res_nano.get("serial_dates", {})
    concur_dates = True
    for sn in sns:
        if dates_mini.get(sn) != dates_nano.get(sn):
            concur_dates = False
            break
            
    if concur_dates:
        confidence = 0.90
    else:
        confidence = 0.50
        
    return {
        "serial_dates": dates_mini,
        "confidence": confidence
    }

def search_manufacturer_web(model, sn):
    try:
        from duckduckgo_search import DDGS
        query = f'"{model}" "{sn}" medical device manufacturer brand name company'
        print(f"Searching web for manufacturer of model {model}: {query}...")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        snippets = []
        for r in results:
            snippets.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}")
        return "\n\n".join(snippets)
    except Exception as e:
        print(f"Web search failed for manufacturer of model {model}: {e}", file=sys.stderr)
        return "No web context found."

def query_manufacturer(model_name, model, sn, search_context, api_key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        We are trying to identify the manufacturer of a medical equipment model.
        The model is '{model}' and serial number is '{sn}'.
        We performed a web search and found these snippets:
        {search_context}

        Please analyze this information and your own knowledge to determine the manufacturer name.
        - Give the canonical name of the manufacturer (e.g., 'ZOLL Medical', 'Philips', 'Welch Allyn', etc.).
        - If you cannot find a specific match, make an educated guess.

        Return ONLY a JSON object matching this structure:
        {{
            "manufacturer": "Manufacturer Name"
        }}
        """
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=1000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error querying manufacturer for model {model_name} on {model}: {e}", file=sys.stderr)
        return None

def resolve_manufacturer_consensus(model, sn, api_key):
    search_context = search_manufacturer_web(model, sn)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_mini = executor.submit(query_manufacturer, "gpt-5.4-mini", model, sn, search_context, api_key)
        future_nano = executor.submit(query_manufacturer, "gpt-5.4-nano", model, sn, search_context, api_key)
        
        res_mini = future_mini.result()
        res_nano = future_nano.result()
        
    if not res_mini and not res_nano:
        return "Unknown Manufacturer"
        
    if not res_mini:
        return res_nano.get("manufacturer", "Unknown Manufacturer")
    return res_mini.get("manufacturer", "Unknown Manufacturer")
