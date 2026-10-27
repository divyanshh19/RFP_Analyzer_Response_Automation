import json
from google import genai
from google.genai import types
from typing import List
from app.core.config import settings
from app.schemas.requirement import RequirementCreate

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

PROMPT_TEMPLATE = """
You are an expert RFP (Request for Proposal) analyst.
Extract all explicit requirements from the following document text.

You MUST return a valid JSON object with a single key "requirements" that contains an array of objects. 
Each object MUST have this exact schema:
{
  "requirement_id": "REQ-001 (increment for each)",
  "description": "The full requirement text",
  "category": "Functional, Technical, Security, Compliance, Financial, Operational, Legal, Support, Infrastructure, or Other",
  "priority": "HIGH", "MEDIUM", or "LOW",
  "mandatory": true or false,
  "deadline": null,
  "deliverable": "string or null",
  "compliance": "string or null",
  "source_page": integer (if discernible) or null,
  "source_section": "string or null"
}

DOCUMENT TEXT:
{text}
"""

def extract_requirements_from_text(text: str) -> List[RequirementCreate]:
    prompt = PROMPT_TEMPLATE.replace("{text}", text)
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=4096
        )
    )
    
    response_text = response.text
    
    try:
        data = json.loads(response_text)
        reqs_data = data.get("requirements", [])
            
        valid_reqs = []
        for item in reqs_data:
            # Sanitize Priority Enum
            if "priority" in item and item["priority"]:
                item["priority"] = str(item["priority"]).upper()
                if item["priority"] not in ["HIGH", "MEDIUM", "LOW"]:
                    item["priority"] = "MEDIUM"
            else:
                item["priority"] = "MEDIUM"
                
            # Quick fix for compliance type mismatch
            if isinstance(item.get("compliance"), list):
                item["compliance"] = ", ".join(item["compliance"])
                
            try:
                valid_reqs.append(RequirementCreate(**item))
            except Exception as ve:
                print(f"Skipping malformed requirement: {item}. Error: {ve}")
                
        return valid_reqs
    except Exception as e:
        raise ValueError(f"Failed to parse LLM JSON response: {e}\nResponse: {response_text}")
