"""
AI Pipeline Service
-------------------
Standalone FastAPI microservice that receives a report file,
runs the real AI analysis pipeline (report_to_json), and returns structured JSON results.
"""

import os
import sys
import uuid
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add the standardTemp directory to the Python path so we can import report_to_json
standard_temp_path = str(Path(__file__).parent.parent / "standardTemp")
if standard_temp_path not in sys.path:
    sys.path.append(standard_temp_path)

from report_to_json.api import process_report, PipelineError

app = FastAPI(
    title="AI Pipeline Service",
    description="AI analysis pipeline for cyber-audit reports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/run")
async def run_pipeline(
    report_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Run the AI analysis pipeline on the uploaded report file.
    Returns structured JSON with analysis results.
    """
    file_bytes = await file.read()
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix or ".pdf"

    # Save to a temporary file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # Call the actual standardization pipeline
        result = process_report(tmp_path)
        
        data = result.data
        
        # Inject the provided report_id into the standardized output
        if "report_meta" in data:
            data["report_meta"]["report_id"] = report_id
        elif "document_control" in data:
            data["document_control"]["document_id"] = report_id
            
        return data
        
    except PipelineError as e:
        raise HTTPException(status_code=400, detail=f"Pipeline error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-pipeline"}
