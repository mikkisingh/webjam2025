"""
LLM service for analyzing medical bills using OpenAI API.
Handles data extraction, cost analysis, and summary generation.
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMAnalyzer:
    """Analyze medical bills using OpenAI GPT."""

    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def _call(self, system: str, prompt: str, temperature: float = 0.3) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)

    def classify_document(self, raw_text):
        """Determine if the document is a healthcare-related bill."""
        return self._call(
            system="You are a document classification expert. Always respond with valid JSON only.",
            prompt=f"""Analyze this document text and determine if it is a healthcare-related bill, invoice, or statement.

{raw_text[:3000]}

ALL of these should return is_healthcare_bill = true:
- Medical bills, hospital bills, clinic bills
- Dental bills, orthodontic bills
- Pharmacy bills, prescription receipts
- Insurance EOBs (Explanation of Benefits)
- Lab/diagnostic bills
- Mental health / therapy bills
- Vision/optometry bills
- Any bill from a healthcare provider

Only return is_healthcare_bill = false for documents that are clearly NOT healthcare-related (e.g., utility bills, restaurant receipts, retail invoices, tax documents, etc.)

Return JSON:
{{
  "is_healthcare_bill": true/false,
  "document_type": "medical bill" | "dental bill" | "pharmacy bill" | "insurance EOB" | "lab bill" | "vision bill" | "general invoice" | "receipt" | "other",
  "confidence": 0.0-1.0,
  "reason": "brief explanation of why this is or is not a healthcare bill"
}}""",
            temperature=0.1,
        )

    def extract_structured_data(self, raw_text):
        return self._call(
            system="You are a medical billing data extraction expert. Always respond with valid JSON only.",
            prompt=f"""Extract from medical bill:

{raw_text[:4000]}

Return JSON:
{{
  "patient_name": "name or 'Not found'",
  "date_of_service": "YYYY-MM-DD or 'Not found'",
  "provider_name": "clinic name or 'Not found'",
  "provider_address": "address or 'Not found'",
  "charges": [{{"item": "service", "cost": number, "code": "code"}}],
  "total": number,
  "insurance_info": "insurance or 'Not found'",
  "patient_responsibility": number
}}""",
            temperature=0.1,
        )

    def analyze_costs(self, structured_data):
        return self._call(
            system="You are a medical billing audit expert with deep knowledge of Medicare rates, CDT dental codes, CPT codes, and typical US healthcare pricing. Always respond with valid JSON only.",
            prompt=f"""Perform a thorough audit of this medical/dental bill. For EVERY charge, provide a detailed assessment.

Bill data:
{json.dumps(structured_data)}

For each charge, evaluate:
1. Is the price reasonable compared to typical US rates for this service?
2. Is the billing code appropriate for the described service?
3. Are there any signs of upcoding, unbundling, or duplicate charges?
4. If insurance was applied, are the adjustments reasonable?
5. For dental: compare against typical dental fee ranges (e.g., cleaning $100-$300, filling $150-$400, crown $800-$1500, root canal $700-$1200, extraction $150-$600)
6. For medical: compare against Medicare rates and typical private-pay rates

Even if charges appear reasonable, explain WHY they are reasonable (e.g., "The $250 charge for a dental cleaning is within the typical $100-$300 range for a comprehensive cleaning").

Return JSON:
{{
  "charge_assessments": [
    {{
      "item": "the service name",
      "charged_amount": number,
      "typical_range_low": number,
      "typical_range_high": number,
      "assessment": "detailed explanation of whether this charge is fair and why",
      "status": "fair" | "high" | "overcharged" | "low" | "unclear"
    }}
  ],
  "issues": [{{"type": "type", "description": "desc", "item": "item", "severity": "low/medium/high"}}],
  "overall_severity": "low/medium/high",
  "potential_savings": number,
  "recommendations": ["actionable recommendation 1", "actionable recommendation 2"]
}}

IMPORTANT: charge_assessments must have one entry per charge. If there are no issues, still provide helpful recommendations (e.g., "Request an itemized bill", "Verify insurance was applied correctly", "Compare with other providers in your area").""",
            temperature=0.3,
        )

    def generate_summary(self, structured_data, analysis_results):
        return self._call(
            system="You are a helpful patient advocate who explains medical bills in plain language. Always respond with valid JSON only.",
            prompt=f"""Summarize this bill analysis for a patient. Reference specific charges and their assessments.

Bill: {json.dumps(structured_data)}
Analysis: {json.dumps(analysis_results)}

Write a summary that:
1. Explains what services were billed and the total
2. For EACH charge, mention whether it's fairly priced and the typical range
3. Highlights any issues or concerns found
4. Gives specific next steps the patient should take
5. If issues were found, draft a professional dispute email

Return JSON:
{{
  "summary": "3-4 paragraph detailed friendly summary with per-charge insights",
  "complaint_email": "professional email or empty string if no issues"
}}""",
            temperature=0.7,
        )

    def analyze_bill(self, raw_text):
        # Step 0: Classify the document
        classification = self.classify_document(raw_text)
        if not classification.get("is_healthcare_bill", False):
            return {
                "rejected": True,
                "document_type": classification.get("document_type", "unknown"),
                "reason": classification.get("reason", "This does not appear to be a medical bill."),
            }

        structured_data = self.extract_structured_data(raw_text)
        analysis_results = self.analyze_costs(structured_data)
        summary_data = self.generate_summary(structured_data, analysis_results)

        return {
            "structured_data": structured_data,
            "analysis_results": analysis_results,
            "summary": summary_data["summary"],
            "complaint_email": summary_data["complaint_email"],
        }
