import io
from fastapi import APIRouter, UploadFile, File, HTTPException, status

try:
    import joblib
    import pandas as pd
except ImportError:
    joblib = None
    pd = None

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

MODEL_PATH = "models/rf_severity_pipeline.joblib"
rf_pipeline = None

if joblib is not None:
    try:
        rf_pipeline = joblib.load(MODEL_PATH)
    except Exception:
        rf_pipeline = None

# These must match exactly what the model was trained on
RAW_NUMERIC_FEATURES = ["cvss_score"]
RAW_CATEGORICAL_FEATURES = [
    "category",
    "status",  
    "new_or_repeat",
    "revalidation_status",
    "cwe_ids",
]
EXPECTED_COLUMNS = RAW_NUMERIC_FEATURES + RAW_CATEGORICAL_FEATURES

@router.post("/predict-severity")
async def predict_severity(file: UploadFile = File(...)):
    """
    Accepts a CSV file of vulnerabilities, runs the Random Forest model,
    and returns the predicted severity for each row.
    """
    if pd is None or joblib is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Required ML dependencies (pandas, joblib, scikit-learn) are missing on backend."
        )

    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only CSV files are supported."
        )
        
    if rf_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Model artifact not found at '{MODEL_PATH}'. Please ensure the model is trained and saved."
        )
        
    try:
        # 1. Dynamic File Handling (In-memory)
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Error parsing CSV file: {str(e)}"
        )

    # 2. Error Handling (Missing Columns)
    # This specifically catches the cvss_score vs cvssscore mismatch or other schema issues
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=(
                f"Missing expected columns in the uploaded CSV: {', '.join(missing_columns)}. "
                f"Required schema: {', '.join(EXPECTED_COLUMNS)}"
            )
        )
        
    try:
        # 3. Inference Only
        X_inference = df[EXPECTED_COLUMNS]
        predictions = rf_pipeline.predict(X_inference)
        
        # 4. Web-Safe Outputs (Structured JSON)
        df['predicted_severity'] = predictions
        
        # Replace NaN values with None so FastAPI can serialize it to standard JSON nulls
        clean_df = df.where(pd.notnull(df), None)
        results = clean_df.to_dict(orient="records")
        
        return {
            "status": "success",
            "message": "Severity predictions generated successfully",
            "total_records": len(results),
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error during model inference: {str(e)}"
        )
