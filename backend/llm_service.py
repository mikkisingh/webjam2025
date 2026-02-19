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
            system="You are a medical billing audit expert. Always respond with valid JSON only.",
            prompt=f"""Analyze for: overcharges, duplicates, missing insurance adjustments, unbundling.

{json.dumps(structured_data)}

Return JSON:
{{
  "issues": [{{"type": "type", "description": "desc", "item": "item", "severity": "low/medium/high"}}],
  "overall_severity": "low/medium/high",
  "potential_savings": number,
  "recommendations": ["rec1", "rec2"]
}}""",
            temperature=0.3,
        )

    def generate_summary(self, structured_data, analysis_results):
        return self._call(
            system="You are a helpful patient advocate. Always respond with valid JSON only.",
            prompt=f"""Summarize bill and create dispute email if issues found.

Bill: {json.dumps(structured_data)}
Issues: {json.dumps(analysis_results)}

Return JSON:
{{
  "summary": "2-3 paragraph friendly summary",
  "complaint_email": "professional email or empty string"
}}""",
            temperature=0.7,
        )

    def analyze_bill(self, raw_text):
        structured_data = self.extract_structured_data(raw_text)
        analysis_results = self.analyze_costs(structured_data)
        summary_data = self.generate_summary(structured_data, analysis_results)

        return {
            "structured_data": structured_data,
            "analysis_results": analysis_results,
            "summary": summary_data["summary"],
            "complaint_email": summary_data["complaint_email"],
        }
