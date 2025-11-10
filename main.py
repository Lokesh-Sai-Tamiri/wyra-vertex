from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from google import genai
from google.genai import types
from typing import Optional
import os
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sales Intelligence API",
    description="Generate sales intelligence reports using Google Gemini",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class CompanyAnalysisRequest(BaseModel):
    """Request model for company analysis."""
    company_name: str = Field(..., description="Name of the company to analyze")
    company_website: HttpUrl = Field(..., description="Company website URL")
    company_linkedin: Optional[HttpUrl] = Field(None, description="Company LinkedIn URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Futran Solutions",
                "company_website": "https://futransolutions.com/",
                "company_linkedin": "https://www.linkedin.com/company/futransolutionsinc/"
            }
        }

# Response model
class CompanyAnalysisResponse(BaseModel):
    """Response model for company analysis."""
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Sales Intelligence API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}

async def generate_sales_intelligence(
    company_name: str,
    company_website: str,
    company_linkedin: Optional[str] = None
) -> dict:
    """
    Generate sales intelligence report for a company.
    
    Args:
        company_name: Name of the company
        company_website: Company website URL
        company_linkedin: Optional LinkedIn URL
        
    Returns:
        dict: Sales intelligence report
        
    Raises:
        Exception: If generation fails
    """
    try:
        client = genai.Client(
            vertexai=True,
            location="global",
            project="wyra-477511"
        )
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Build the analysis prompt
        linkedin_text = f"\nCompany LinkedIn: {company_linkedin}" if company_linkedin else ""
        
        text1 = types.Part.from_text(text=f"""Analyze {company_website} and generate the sales intelligence report.

Company Name: {company_name}{linkedin_text}
Analysis Date: {current_date}

Return valid JSON only - no markdown or code blocks.""")
        
        si_text1 = """# ROLE & PERSPECTIVE
You are a sales intelligence analyst generating a comprehensive report ABOUT a technology company FOR that company's leadership (sales, marketing, executives). Write from a third-person analytical perspective: \"This company...\", \"They should target...\", \"Their strengths include...\".

# TASK
Analyze the provided company's digital presence and generate a single, valid JSON object containing actionable sales intelligence and outreach campaign ideas.

# PREREQUISITES

- **Live Web Access Required**: This task requires the ability to access and process content from live web URLs. Ensure this capability is enabled before proceeding.

# INPUT
- Company Website URL: {{company_website}}
- Company LinkedIn URL: {{company_linkedin}}
- Company Name: {{company_name}}
- Analysis Date: {{current_date}}

# RESEARCH METHODOLOGY

## Search Priority
1. Company website (all sections: homepage, about, services, case studies, blog, team, partners)
2. Case studies and customer success pages
3. Official partnership pages (AWS/Azure/GCP partner directories)
4. News and press releases (last 12 months)
5. LinkedIn company page (team size, locations, recent posts)
6. Partner verification in official directories

## Evidence Standards
- **HIGH confidence**: Multiple sources, explicit website claims, verified partnerships
- **MEDIUM confidence**: Single authoritative source, strong inference from evidence
- **LOW confidence**: Weak inference, limited evidence, educated estimate

# CRITICAL RULES

## Data Integrity (NEVER VIOLATE)
1. **Use `null` for missing data** - NEVER fabricate information
2. **Only count what's visible** - If not on website/verifiable source, it doesn't exist
3. **Cite specific proof** - Every claim needs evidence (case study name, page location, partnership tier), REMEMBER that Citations are for YOUR analysis only - do NOT include reference numbers in final JSON output
4. **Empty arrays over guesses** - `[]` is better than hallucinated data

## Social Proof - Anti-Hallucination Rules
- **CUSTOMER LOGOS**: Only count visible, identifiable logos on website
- **CASE STUDIES**: Must have customer name (or \"Anonymous [Industry]\") + problem + outcome
- **METRICS**: Only include if actual numbers exist. Use \"qualitative outcome only\" if no metrics
- **TESTIMONIALS**: Only direct quotes with name + title attribution
- **AWARDS**: Only if explicitly stated with year/issuer
- **PARTNERSHIPS**: Only official tiers clearly displayed. Use \"tier unclear\" if ambiguous

## Company Type Detection
- **Service Provider**: Consulting, implementation, managed services (no product pricing page)
- **Product Company**: SaaS/ISV with pricing page, free trial, API documentation
- **Hybrid**: Both products AND professional services clearly offered

**Field Population Rules**:
- Service provider → populate `solution_area_split`, use an empty array for `product_portfolio` (`[]`)
- Product company → populate `product_portfolio`, use an empty array for `solution_area_split` (`[]`)
- Hybrid → populate BOTH fields

## Percentage Estimation
Base estimates on verifiable evidence:
- **Case study distribution**: If 12 of 20 case studies are fintech → \"~60%\"
- **Content focus**: Count blog posts, solution pages, team expertise by area
- **Team composition**: If LinkedIn shows 30 cloud engineers, 10 AI engineers → \"75%/25%\"
- **Use ranges when uncertain**: \"40-50%\" better than exact \"45%\"

# CONTENT REQUIREMENTS

## Outreach Ideas (5-10 Required)
Each idea must include:
- **100-120 words** in `full_description`
- Each full_description is EXACTLY 100-120 words (not 95, not 125)
- Specific target persona (not generic \"CTO\")
- Company's proof points (cite actual case studies/metrics)
- Current market trend or urgency factor
- Concrete campaign format in single or two words and NOT a sentence
- Clear business outcomes

## Outreach Idea Confidence Scoring (high|medium|low)

### HIGH = Ready to Execute
3+ relevant case studies + quantified outcomes + strong proof points

*Example: \"Target fintech VPs\" with 8 fintech case studies, partner cert, 40% proven cost reduction*

### MEDIUM = Valid but Needs Development
1-2 case studies + reasonable fit + generic/qualitative proof

*Example: \"Target healthcare CTOs\" with 2 healthcare mentions, general expertise, no specific outcomes*

### LOW = Strategic Opportunity
Minimal evidence + inferred persona + speculative use case

*Example: \"Target manufacturing IoT\" with zero manufacturing case studies, adjacent capabilities only*

### Scoring Rules
- Default to MEDIUM when uncertain
- HIGH requires strong, specific evidence (don't overrate)
- LOW is valuable (marks expansion opportunities)
- Mix of scores expected (not all should be HIGH)

**Quality checklist per idea**:
- ✅ Can a sales rep build a target list from this persona description?
- ✅ Are pain points evidence-based (not generic)?
- ✅ Does social_proof cite specific company achievements?
- ✅ Are objections realistic and addressable?
- ✅ Is the urgency factor time-sensitive and compelling?

# OUTPUT FORMAT

## Structure
- **Single valid JSON object only**
- **No markdown** (no ```json blocks)
- **No explanatory text** before or after JSON
- **Start with `{` and end with `}`**

## Field-Specific Guidance

### `value_proposition`
2-3 sentences. Format: \"Company X is a [type] that specializes in [services] for [target customers]. They focus on [key differentiator].\"

### `analysis_metadata.primary_url_analyzed`
- Use the company website URL (`{{company_website}}`) for this field.

### `industry_breakdown`
- Use percentage ranges when exact split unclear: \"~60%\", \"15-20%\"
- Base on case study count, solution pages, team expertise distribution
- `focus_level`: primary (>40%), secondary (15-40%), emerging (<15%)

### `market_position`
- **niche specialist**: Tightly focused on a specific industry or problem with deep expertise.
- **broad generalist**: Offers a wide range of services across multiple industries.
- **emerging player**: Newer company, often with innovative tech but smaller market footprint.
- **established leader**: Long-standing company with significant brand recognition and market share.

### `icp_customer_profile.company_size`
- Use one of the following standard segments: 'Startup (1-50 employees)', 'SMB (51-500 employees)', 'Mid-Market (501-5000 employees)', 'Enterprise (5000+ employees)'.

### `featured_case_studies`
- ONLY include if published case study exists
- Must have: customer (or \"Anonymous [Industry]\"), challenge, outcome
- Set `outcome_has_metrics = true` ONLY if specific numbers/percentages present
- Set `customer_name_anonymized = true` if customer name intentionally hidden

### `cost_of_inaction`
List 2-4 specific risks/consequences if prospect doesn't act:
- \"Continued 30% cloud cost waste ($X annually)\"
- \"Falling behind competitors adopting AI\"
- \"Regulatory penalties if non-compliant by [deadline]\"

# VALIDATION CHECKLIST

Before outputting, verify:
- [ ] JSON is syntactically valid (proper quotes, commas, brackets)
- [ ] 5-10 outreach ideas present
- [ ] Each `full_description` is 100-120 words
- [ ] Each outreach idea has `confidence_score` (high|medium|low)
- [ ] No fabricated data (all null if not found)
- [ ] All confidence/evidence_strength fields populated
- [ ] Company type correctly identified
- [ ] Correct fields populated (solution_area_split vs product_portfolio)
- [ ] All proof_points cite specific sources
- [ ] No placeholder text like \"TBD\" or \"Example Corp\"

# TONE & STYLE
- Professional analyst providing strategic intelligence
- Confident but evidence-based
- Actionable and specific (not vague)
- Honest about data limitations (use null, empty arrays, low confidence scores)

# EXAMPLE OUTPUT SNIPPET

This is an example of a single, well-formed object within the `outreach_ideas` array. Use this as a structural guide.

```json
{
  \"idea_title\": \"AI-Powered Cost Optimization for Retail Supply Chains\",
  \"full_description\": \"Launch a targeted campaign for VPs of Supply Chain in retail. Highlight {{company_name}}'s proven expertise in reducing operational overhead, citing the 'Global Retail Co.' case study where they achieved a 22% reduction in logistics costs. The urgency is the current inflationary pressure on retail margins. Propose a 'Supply Chain AI Readiness Assessment' to identify immediate cost-saving opportunities using their proprietary analytics platform. This positions {{company_name}} as a strategic partner for building resilient, cost-effective supply chains in a volatile market, directly addressing top-of-mind C-suite concerns around profitability and efficiency. The campaign can use a mix of LinkedIn outreach and a webinar.\",
  \"target_persona\": {
    \"role_archetype\": \"VP of Supply Chain\",
    \"seniority_level\": \"VP\",
    \"business_function\": \"Operations\",
    \"buying_triggers\": [
      \"High logistics and inventory costs\",
      \"Pressure to improve margins\",
      \"Competitors adopting AI/ML for forecasting\"
    ]
  },
  \"campaign_format\": \"webinar'\",
  \"pain_points\": [
    \"Inaccurate demand forecasting leading to stockouts or overstock\",
    \"Rising fuel and transportation costs eroding profits\",
    \"Lack of visibility into the end-to-end supply chain\"
  ],
  \"solutions\": [
    \"Implement AI/ML models for predictive demand forecasting\",
    \"Deploy route optimization algorithms to reduce fuel consumption\",
    \"Provide a unified data platform for real-time supply chain visibility\"
  ],
  \"social_proof\": [
    \"Case Study: 'Global Retail Co.' achieved 22% logistics cost reduction.\",
    \"AWS Advanced Consulting Partner with Retail Competency.\",
    \"Proprietary analytics platform featured in 'RetailTech Weekly'.\"
  ],
  \"market_signals\": \"Industry reports showing increased investment in supply chain technology post-pandemic.\",
  \"business_outcomes\": [
    \"Reduced operational costs and improved profit margins\",
    \"Increased supply chain resilience and agility\",
    \"Enhanced customer satisfaction through better product availability\"
  ],
  \"industry\": \"Retail\",
  \"sub_industry\": \"Apparel & Fashion\",
  \"objections\": [
    \"Our current ERP system is too complex to integrate with.\",
    \"We don't have the in-house talent to manage AI models.\"
  ],
  \"cost_of_inaction\": [
    \"Continued margin erosion due to inefficient logistics.\",
    \"Losing market share to more agile, tech-enabled competitors.\"
  ],
  \"urgency_factor\": \"Immediate need to combat inflationary pressures and protect Q4 profitability.\",
  \"confidence_score\": \"high\"
}
```

# JSON SCHEMA

{
  \"analysis_metadata\": {
    \"company_name\": \"str\",
    \"analysis_date\": \"YYYY-MM-DD\",
    \"primary_url_analyzed\": \"str\"
  },

  \"company_overview\": {
    \"name\": \"str\",
    \"value_proposition\": \"str\"
  },

  \"outreach_ideas\": [{
    \"idea_title\": \"str\",
    \"full_description\": \"str\",
    \"target_persona\": {
      \"role_archetype\": \"str\",
      \"seniority_level\": \"C-Level|VP|Director|Manager\",
      \"business_function\": \"str\",
      \"buying_triggers\": [\"str\"]
    },
    \"campaign_format\": \"str\",
    \"pain_points\": [\"str\"],
    \"solutions\": [\"str\"],
    \"social_proof\": [\"str\"],
    \"market_signals\": \"str\",
    \"business_outcomes\": [\"str\"],
    \"industry\": \"str\",
    \"sub_industry\": \"str|null\",
    \"objections\": [\"str\"],
    \"cost_of_inaction\": [\"str\"],
    \"urgency_factor\": \"str\",
    \"confidence_score\": \"high|medium|low\"
  }],

  \"industry_intelligence\": {
    \"primary_industries\": [\"str\"],
    \"why_these_industries\": \"str\",
    \"industry_breakdown\": [{
      \"industry\": \"str\",
      \"focus_level\": \"primary|secondary|emerging\",
      \"percentage\": \"str|null\",
      \"evidence\": \"str\",
      \"confidence\": \"high|medium|low\"
    }],
    \"market_position\": \"niche specialist|broad generalist|emerging player|established leader\",
    \"positioning_evidence\": \"str\",
    \"icp_customer_profile\": {
      \"company_size\": \"Startup (1-50 employees)|SMB (51-500 employees)|Mid-Market (501-5000 employees)|Enterprise (5000+ employees)|null\",
      \"size_reasoning\": \"str\",
      \"buyer_roles\": [\"str\"],
      \"geographic_focus\": [\"str\"],
      \"geo_evidence\": \"str\"
    }
  },

  \"technology_footprint\": {
    \"core_platforms\": [{
      \"platform\": \"str\",
      \"strength_level\": \"expert|advanced|intermediate\",
      \"evidence\": \"str\",
      \"specializations\": [\"str\"]
    }],
    \"technology_stack_visible\": [\"str\"],
    \"integration_capabilities\": [\"str\"],
    \"proprietary_solutions\": [\"str\"]
  },

  \"business_model\": {
    \"company_type\": \"service provider|product company|hybrid\",
    \"revenue_split_estimate\": \"str|null\",
    \"evidence\": \"str\"
  },

  \"solution_area_split\": [{
    \"service_area\": \"str\",
    \"percentage_estimate\": \"str|null\",
    \"evidence_strength\": \"high|medium|low\",
    \"proof_points\": [\"str\"]
  }],

  \"product_portfolio\": [{
    \"product_name\": \"str\",
    \"product_category\": \"str\",
    \"description\": \"str\",
    \"percentage_estimate\": \"str|null\",
    \"proof_points\": [\"str\"],
    \"pricing_model\": \"str|null\",
    \"target_users\": [\"str\"]
  }],

  \"social_proof_metrics\": {
    \"customer_logos_count\": \"int\",
    \"customer_logos_source\": \"str|null\",
    \"notable_customers\": [{
      \"name\": \"str\",
      \"source\": \"str\"
    }],
    \"case_studies_count\": \"int\",
    \"case_studies_source\": \"str|null\",
    \"featured_case_studies\": [{
      \"customer_name\": \"str\",
      \"customer_name_anonymized\": \"bool\",
      \"industry\": \"str\",
      \"challenge\": \"str\",
      \"measurable_outcome\": \"str\",
      \"outcome_has_metrics\": \"bool\",
      \"technologies_used\": [\"str\"],
      \"source_url\": \"str|null\"
    }],
    \"testimonials_count\": \"int\",
    \"testimonials_source\": \"str|null\",
    \"awards_certifications\": [{
      \"name\": \"str\",
      \"year\": \"str|null\",
      \"issuer\": \"str\",
      \"source\": \"str\"
    }],
    \"partner_badges\": [{
      \"partner\": \"str\",
      \"tier\": \"str\",
      \"evidence\": \"str\",
      \"verified\": \"bool\"
    }],
    \"data_quality_flags\": {
      \"limited_social_proof\": \"bool\",
      \"no_metrics_in_case_studies\": \"bool\",
      \"partner_tiers_unclear\": \"bool\",
      \"missing_sources\": [\"str\"]
    }
  }
}"""
        
        model = "gemini-2.5-flash-preview-09-2025"
        contents = [
            types.Content(
                role="user",
                parts=[text1]
            )
        ]
        tools = [
            types.Tool(google_search=types.GoogleSearch()),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.85,
            max_output_tokens=65535,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="OFF"
                )
            ],
            tools=tools,
            system_instruction=[types.Part.from_text(text=si_text1)],
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1,
            ),
        )
        
        # Collect the full response from streaming
        full_response = ""
        chunk_count = 0
        
        logger.info("Starting to collect streaming response...")
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if not chunk.candidates:
                continue
                
            candidate = chunk.candidates[0]
            
            # Skip chunks without content
            if not candidate.content or not candidate.content.parts:
                continue
            
            # Get text from chunk
            chunk_text = chunk.text if hasattr(chunk, 'text') and chunk.text else ""
            if chunk_text:
                full_response += chunk_text
                chunk_count += 1
            
            # Log finish reason if present
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                logger.info(f"Stream finished with reason: {candidate.finish_reason}")
        
        logger.info(f"Collected {chunk_count} chunks, total length: {len(full_response)} characters")
        
        # Check if we got any response
        if not full_response or len(full_response.strip()) == 0:
            logger.error("Empty response received from AI")
            raise Exception("Empty response received from AI model")
        
        # Parse JSON response
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = full_response.strip()
            
            logger.debug(f"Response starts with: {cleaned_response[:100]}")
            
            # Remove ```json at the start
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
                logger.debug("Removed ```json markdown prefix")
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # Remove ```
                logger.debug("Removed ``` markdown prefix")
            
            # Remove ``` at the end
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
                logger.debug("Removed ``` markdown suffix")
            
            # Strip again after removing markdown
            cleaned_response = cleaned_response.strip()
            
            logger.debug(f"Cleaned response starts with: {cleaned_response[:100]}")
            logger.debug(f"Cleaned response ends with: {cleaned_response[-100:]}")
            
            # Parse the JSON
            result = json.loads(cleaned_response)
            logger.info("Successfully parsed JSON response")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response (first 1000 chars): {full_response[:1000]}")
            logger.error(f"Raw response (last 500 chars): {full_response[-500:]}")
            if 'cleaned_response' in locals():
                logger.error(f"Cleaned response (first 1000 chars): {cleaned_response[:1000]}")
                logger.error(f"Cleaned response (last 500 chars): {cleaned_response[-500:]}")
            
            # Save full response to file for debugging
            with open("/tmp/failed_response.txt", "w") as f:
                f.write(full_response)
            logger.error("Full response saved to /tmp/failed_response.txt")
            
            raise Exception(f"Invalid JSON response from AI: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error generating sales intelligence: {str(e)}")
        raise

@app.post("/api/v1/analyze", response_model=CompanyAnalysisResponse)
async def analyze_company(request: CompanyAnalysisRequest):
    """
    Generate sales intelligence report for a company.
    
    Args:
        request: Company analysis request with name, website, and optional LinkedIn URL
        
    Returns:
        CompanyAnalysisResponse: Generated sales intelligence report
    """
    try:
        logger.info(f"Starting analysis for {request.company_name}")
        
        result = await generate_sales_intelligence(
            company_name=request.company_name,
            company_website=str(request.company_website),
            company_linkedin=str(request.company_linkedin) if request.company_linkedin else None
        )
        
        logger.info(f"Successfully completed analysis for {request.company_name}")
        
        return CompanyAnalysisResponse(
            status="success",
            data=result,
            tokens_used=None  # Can be added if you want to track usage
        )
        
    except Exception as e:
        logger.error(f"Analysis failed for {request.company_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)