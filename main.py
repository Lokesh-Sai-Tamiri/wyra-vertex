"""
Cloud Run API Service for Sales Intelligence Report Generation
Uses Vertex AI with service account authentication
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi import Security, Depends, status
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
import logging
import json
from datetime import datetime

from services.ai_service import SalesIntelligenceGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# API Key configuration
API_KEY = "x5ZK8PmzIFIZa79bMOaLHNuhgDf7-1HdJ4sUwSs9laA"  # Load from environment variable
if not API_KEY:
    logger.warning("⚠️  API_KEY not set! All requests will be rejected.")

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from X-API-KEY header.
    
    Args:
        api_key: API key from request header
        
    Returns:
        str: Validated API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server"
        )
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-KEY header"
        )
    
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt from request")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return api_key

# Initialize FastAPI app
app = FastAPI(
    title="Sales Intelligence API",
    description="Generate AI-powered sales intelligence reports using Vertex AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class AnalysisRequest(BaseModel):
    """Request model for sales intelligence analysis"""
    company_website: HttpUrl = Field(..., description="Company website URL to analyze")
    #company_website: str = Field(..., description="Name of the company")
    company_linkedin: Optional[HttpUrl] = Field(None, description="Company LinkedIn URL")
    analysis_date: Optional[str] = Field(None, description="Analysis date (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "company_website": "https://futransolutions.com/",
                "company_linkedin": "https://www.linkedin.com/company/futransolutionsinc/",
                "analysis_date": "2025-11-10"
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for successful analysis"""
    status: str = Field(default="success")
    data: dict = Field(..., description="Generated sales intelligence report")
    metadata: dict = Field(..., description="Analysis metadata")


# Initialize AI service
ai_generator = SalesIntelligenceGenerator()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Sales Intelligence API",
        "status": "running",
        "version": "1.0.0",
        "vertex_ai": "enabled"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "operational"
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_company(request: AnalysisRequest,
                          api_key: str = Depends(verify_api_key)):
    """
    Generate sales intelligence report for a company

    This endpoint analyzes a company's digital presence and generates
    a comprehensive sales intelligence report with outreach campaign ideas.

    Args:
        request: Analysis request containing company details

    Returns:
        AnalysisResponse with the generated report

    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"Starting analysis for company: {request.company_website}")

        # Set default analysis date if not provided
        analysis_date = request.analysis_date or datetime.now().strftime("%Y-%m-%d")

        # Generate the user prompt
        user_prompt = f"""Analyze {request.company_website} and generate the sales intelligence report.

Company LinkedIn: {request.company_linkedin or "Not provided"}
Analysis Date: {analysis_date}

Return valid JSON only - no markdown or code blocks."""

        logger.info(f"Generated prompt for Vertex AI")

        # Call Vertex AI to generate the report
        result = await ai_generator.generate_report(user_prompt)

        # Log response preview for debugging
        preview = result[:500] if len(result) > 500 else result
        logger.info(f"AI response preview (first 500 chars): {preview}")

        # Parse the JSON response
        report_data = None

        # First, try parsing as-is
        try:
            report_data = json.loads(result)
            logger.info("Successfully parsed JSON response directly")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response directly: {e}")
            logger.debug(f"Full response (first 1000 chars): {result[:1000]}")

            # Try to extract from markdown code blocks
            if "```json" in result:
                try:
                    extracted = result.split("```json")[1].split("```")[0].strip()
                    report_data = json.loads(extracted)
                    logger.info("Successfully extracted JSON from ```json code block")
                except (IndexError, json.JSONDecodeError) as ex:
                    logger.error(f"Failed to extract from ```json block: {ex}")

            if report_data is None and "```" in result:
                try:
                    extracted = result.split("```")[1].split("```")[0].strip()
                    report_data = json.loads(extracted)
                    logger.info("Successfully extracted JSON from ``` code block")
                except (IndexError, json.JSONDecodeError) as ex:
                    logger.error(f"Failed to extract from ``` block: {ex}")

            # If all parsing attempts failed, raise error
            if report_data is None:
                logger.error(f"Could not extract valid JSON. Response length: {len(result)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"AI response was not valid JSON. Response preview: {result[:200]}..."
                )

        logger.info(f"Successfully generated report for {request.company_website}")

        return AnalysisResponse(
            status="success",
            data=report_data,
            metadata={
                "company_website": request.company_website,
                "analysis_date": analysis_date,
                "generated_at": datetime.utcnow().isoformat(),
                "model": "gemini-2.5-flash-preview-09-2025"
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/api/v1/analyze/custom")
async def analyze_custom_prompt(request: Request):
    """
    Generate report using a custom prompt

    This endpoint accepts a raw text prompt and passes it directly to Vertex AI.
    Useful for testing or custom analysis scenarios.

    Args:
        request: Raw request with 'prompt' field in JSON body

    Returns:
        Generated AI response
    """
    try:
        body = await request.json()
        prompt = body.get("prompt")

        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Missing 'prompt' field in request body"
            )

        logger.info("Processing custom prompt")

        # Generate response
        result = await ai_generator.generate_report(prompt)

        # Try to parse as JSON
        try:
            parsed_result = json.loads(result)
            return JSONResponse(content={
                "status": "success",
                "data": parsed_result,
                "raw_output": result
            })
        except json.JSONDecodeError:
            # Return as raw text if not JSON
            return JSONResponse(content={
                "status": "success",
                "data": result,
                "raw_output": result
            })

    except Exception as e:
        logger.error(f"Error processing custom prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process prompt: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
