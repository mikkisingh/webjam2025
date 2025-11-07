"""
LLM service for analyzing medical bills using Google Gemini API.
Handles data extraction, cost analysis, and summary generation.
"""
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMAnalyzer:
    """Analyze medical bills using Google Gemini LLM."""
    
    def __init__(self):
        """Initialize Gemini client."""
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model with JSON response configuration
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={
                "response_mime_type": "application/json"
            }
        )
    
    def extract_structured_data(self, raw_text):
        """
        Extract structured data from raw bill text.
        
        Args:
            raw_text: Raw text extracted from the bill
            
        Returns:
            Dictionary with structured data
        """
        prompt = f"""Extract from medical bill:

{raw_text[:2000]}

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
}}"""
        
        try:
            # Create chat with system instruction
            chat_model = genai.GenerativeModel(
                'gemini-2.0-flash',
                generation_config={"response_mime_type": "application/json"},
                system_instruction="You are a medical billing data extraction expert. Always respond with valid JSON only."
            )
            
            response = chat_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                )
            )
            
            result = response.text
            return json.loads(result)
        except Exception as e:
            raise Exception(f"Error extracting structured data: {str(e)}")
    
    def analyze_costs(self, structured_data):
        """
        Analyze costs for anomalies and overcharges.
        
        Args:
            structured_data: Dictionary with structured bill data
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""Analyze for: overcharges, duplicates, missing insurance adjustments, unbundling.

{json.dumps(structured_data)}

Return JSON:
{{
  "issues": [{{"type": "type", "description": "desc", "item": "item", "severity": "low/medium/high"}}],
  "overall_severity": "low/medium/high",
  "potential_savings": number,
  "recommendations": ["rec1", "rec2"]
}}"""
        
        try:
            # Create chat with system instruction
            chat_model = genai.GenerativeModel(
                'gemini-2.0-flash',
                generation_config={"response_mime_type": "application/json"},
                system_instruction="You are a medical billing audit expert. Always respond with valid JSON only."
            )
            
            response = chat_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                )
            )
            
            result = response.text
            return json.loads(result)
        except Exception as e:
            raise Exception(f"Error analyzing costs: {str(e)}")
    
    def generate_summary(self, structured_data, analysis_results):
        """
        Generate a human-readable summary and complaint template.
        
        Args:
            structured_data: Dictionary with structured bill data
            analysis_results: Dictionary with analysis results
            
        Returns:
            Dictionary with summary and complaint template
        """
        prompt = f"""Summarize bill and create dispute email if issues found.

Bill: {json.dumps(structured_data)}
Issues: {json.dumps(analysis_results)}

Return JSON:
{{
  "summary": "2-3 paragraph friendly summary",
  "complaint_email": "professional email or empty string"
}}"""
        
        try:
            # Create chat with system instruction
            chat_model = genai.GenerativeModel(
                'gemini-2.0-flash',
                generation_config={"response_mime_type": "application/json"},
                system_instruction="You are a helpful patient advocate. Always respond with valid JSON only."
            )
            
            response = chat_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )
            
            result = response.text
            return json.loads(result)
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")
    
    def analyze_bill(self, raw_text):
        """
        Complete analysis pipeline for a medical bill.
        
        Args:
            raw_text: Raw text extracted from the bill
            
        Returns:
            Dictionary with all analysis results
        """
        # Step 1: Extract structured data
        structured_data = self.extract_structured_data(raw_text)
        
        # Step 2: Analyze costs
        analysis_results = self.analyze_costs(structured_data)
        
        # Step 3: Generate summary
        summary_data = self.generate_summary(structured_data, analysis_results)
        
        return {
            "structured_data": structured_data,
            "analysis_results": analysis_results,
            "summary": summary_data["summary"],
            "complaint_email": summary_data["complaint_email"]
        }
