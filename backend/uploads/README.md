# Sample Medical Bills for Testing

This directory contains sample medical bill files for testing the MediCheck application.

## Quick Test

If you don't have a real medical bill to test with, you can create a simple text file and save it as a PDF:

### Sample Bill Content

```
GENERAL HEALTH CLINIC
123 Medical Center Drive
Anytown, ST 12345
Phone: (555) 123-4567

PATIENT STATEMENT
Date: January 15, 2025

Patient Name: John Doe
Patient ID: P-12345
Date of Birth: 01/15/1980
Insurance: Blue Cross Blue Shield - Policy #BC123456

Date of Service: January 3, 2025
Provider: Dr. Sarah Johnson, MD

CHARGES:
-------------------------------------------------
Service Description          Code      Amount
-------------------------------------------------
Office Visit - Level 3       99213     $150.00
X-Ray Chest, 2 Views        71020     $280.00
X-Ray Chest, 2 Views        71020     $280.00  (DUPLICATE)
Laboratory Tests             80053     $125.00
Consultation Fee            99245     $650.00
Administrative Fee           N/A       $45.00
-------------------------------------------------
Subtotal:                              $1,530.00
Insurance Adjustment:                   -$200.00
-------------------------------------------------
TOTAL DUE:                             $1,330.00

Your Responsibility:                   $1,330.00

Payment Due: February 15, 2025

Please remit payment to:
General Health Clinic
P.O. Box 9876
Anytown, ST 12345

Questions? Call (555) 123-4567
```

## How to Create a Test PDF

### Method 1: Online Converter
1. Copy the sample bill content above
2. Paste into a text editor
3. Use an online tool like https://www.text2pdf.com or https://convertio.co/txt-pdf/
4. Download the PDF

### Method 2: Microsoft Word
1. Copy the sample bill content
2. Paste into Microsoft Word
3. Save As → PDF

### Method 3: Print to PDF
1. Copy the sample bill content
2. Paste into any text editor
3. Print → Select "Microsoft Print to PDF" or "Save as PDF"

## Testing Notes

This sample bill contains intentional issues for testing:
- **Duplicate Charge**: X-Ray appears twice at $280 each
- **Overpriced Consultation**: $650 is above typical range
- **Missing Insurance Details**: Limited insurance adjustment information

The AI should detect these issues and flag them in the analysis.

## Using Real Bills

For best results, test with actual medical bills (PDF or images). The system can handle:
- **PDF files**: Multi-page medical statements
- **Images**: Photos or scans of paper bills (JPG, PNG)
- **Quality**: Higher quality images produce better text extraction

## Privacy Note

If testing with real bills, remember:
- Data is stored locally in your database
- Files are saved in the uploads folder
- Consider redacting personal information if sharing results
