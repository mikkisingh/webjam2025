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
        if (api_key): 
            print("h")
        else: 
            print("s")

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
        prompt = f"""
You are a medical billing expert. Extract structured information from this medical bill.

Medical Bill Text:
{raw_text}

Extract and return a JSON object with the following structure:
{{
  "patient_name": "patient full name or 'Not found'",
  "date_of_service": "YYYY-MM-DD format or 'Not found'",
  "provider_name": "provider/clinic name or 'Not found'",
  "provider_address": "provider address or 'Not found'",
  "charges": [
    {{"item": "service/procedure name", "cost": numeric_value, "code": "procedure code if available"}}
  ],
  "total": numeric_total_amount,
  "insurance_info": "insurance company and policy info or 'Not found'",
  "patient_responsibility": numeric_amount_patient_owes
}}

Be precise with numbers. If information is missing, use "Not found" or 0 for numbers.
Return ONLY the JSON object, no additional text.
"""
        
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
        prompt = f"""
You are a medical billing auditor. Analyze this medical bill for potential issues.

Bill Data:
{json.dumps(structured_data, indent=2)}

Identify:
1. Charges that seem unusually high (compare to typical US healthcare costs)
2. Duplicate charges for the same service
3. Missing insurance adjustments or discounts
4. Unbundled services that should be bundled
5. Any other billing irregularities

Return a JSON object with:
{{
  "issues": [
    {{"type": "issue_type", "description": "detailed description", "item": "affected charge item", "severity": "low/medium/high"}}
  ],
  "overall_severity": "low/medium/high",
  "potential_savings": numeric_estimate_of_overcharges,
  "recommendations": ["actionable recommendation 1", "actionable recommendation 2"]
}}

If no issues found, return empty issues array.
Return ONLY the JSON object, no additional text.
"""
        
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
        prompt = f"""
You are a patient advocate helping someone understand their medical bill.

Bill Data:
{json.dumps(structured_data, indent=2)}

Analysis Results:
{json.dumps(analysis_results, indent=2)}

Generate:
1. A clear, friendly summary explaining the bill (2-3 paragraphs)
2. If issues were found, a professional email template the patient can send to the billing department

Return a JSON object:
{{
  "summary": "friendly summary text",
  "complaint_email": "professional email template (or empty string if no issues)"
}}

The summary should be conversational and easy to understand.
The email should be professional and specific about the issues found.
Return ONLY the JSON object, no additional text.
"""
        
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
