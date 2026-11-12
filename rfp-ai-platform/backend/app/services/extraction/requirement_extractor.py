import json
from typing import List
from app.core.llm import get_groq_client, generate_text
from app.schemas.requirement import RequirementCreate

# Backwards compatibility reference
client = get_groq_client()

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
    response_text = generate_text(
        prompt,
        temperature=0.2,
        max_tokens=4096,
        json_mode=True,
        client=get_groq_client(),
    )
    
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
                
            # Ensure compliance field is List[str] as expected by RequirementCreate
            comp_val = item.get("compliance")
            if isinstance(comp_val, str):
                item["compliance"] = [c.strip() for c in comp_val.split(",") if c.strip()]
            elif isinstance(comp_val, list):
                item["compliance"] = [str(c) for c in comp_val]
            else:
                item["compliance"] = []
                
            try:
                valid_reqs.append(RequirementCreate(**item))
            except Exception as ve:
                print(f"Skipping malformed requirement: {item}. Error: {ve}")
                
        return valid_reqs
    except Exception as e:
        raise ValueError(f"Failed to parse LLM JSON response: {e}\nResponse: {response_text}")
