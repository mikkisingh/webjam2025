# MediCheck — API Reference

Base URL: `http://localhost:5001`

> The Flask backend is a **stateless compute layer**. It processes files and returns results but never stores bill data. All user data persistence (analysis history, dispute tracking) is handled by the frontend directly via the Supabase SDK.

---

## Endpoints

### `GET /`
Health check.

**Response:**
```json
{ "message": "MediCheck API - Medical Bill Analysis" }
```

---

### `POST /process`
The core endpoint. Accepts a medical bill file, extracts text, runs full AI analysis, deletes the file, and returns results — all in a single call.

**HIPAA Option A:** The uploaded file is deleted from disk immediately after text extraction. Raw extracted text is never written to any database. Nothing about the bill is persisted on this server.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF, JPG, or PNG (max 16MB) |

**Success Response — `200 OK`:**
```json
{
  "structured_data": {
    "patient_name": "Jane Doe",
    "date_of_service": "2025-01-15",
    "provider_name": "City Medical Center",
    "provider_address": "123 Main St, Springfield",
    "charges": [
      { "item": "Office Visit",  "cost": 250.00, "code": "99213" },
      { "item": "Blood Panel",   "cost": 180.00, "code": "80053" }
    ],
    "total": 430.00,
    "insurance_info": "BlueCross PPO",
    "patient_responsibility": 95.00
  },
  "analysis_results": {
    "issues": [
      {
        "type": "overcharge",
        "description": "Office visit billed at rate 40% above regional average",
        "item": "Office Visit",
        "severity": "high"
      }
    ],
    "overall_severity": "high",
    "potential_savings": 100.00,
    "recommendations": [
      "Request an itemized bill",
      "Cross-reference with your EOB from the insurer"
    ]
  },
  "summary": "Your bill totals $430 with a patient responsibility of $95...",
  "complaint_email": "Dear Billing Department, I am writing to dispute..."
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| `400` | No file provided, empty filename, or unsupported file type |
| `422` | File was valid but no text could be extracted |
| `500` | Text extraction or Gemini API call failed |

**Processing pipeline (internal):**
```
Receive file
  → Validate type + size
  → Save to uploads/ (temp)
  → Extract text (pdfplumber or Tesseract)
  → DELETE file immediately
  → LLMAnalyzer.analyze_bill(raw_text)
      → extract_structured_data()   [Gemini call 1]
      → analyze_costs()             [Gemini call 2]
      → generate_summary()          [Gemini call 3]
  → Return results (nothing stored)
```

---

### `GET /items`
Legacy endpoint — list all items.

**Response — `200 OK`:**
```json
[{ "id": 1, "name": "Example", "description": "..." }]
```

---

### `POST /items`
Legacy endpoint — create an item.

**Request body:**
```json
{ "name": "Item Name", "description": "Optional description" }
```

**Response — `200 OK`:**
```json
{ "id": 1, "name": "Item Name", "description": "Optional description" }
```

---

## Supabase Data Layer (Frontend → Supabase direct)

The following operations are performed by the frontend using the Supabase JS SDK, not through Flask.

### Save analysis result
After `/process` returns, if the user is authenticated, the frontend inserts into the `analyses` table:

```js
await supabase.from('analyses').insert({
  user_id: user.id,
  overall_severity,
  potential_savings,
  issues_count,
  structured_data,   // jsonb
  analysis_results,  // jsonb
  summary,
  complaint_email,
})
```

### List user's analyses
```js
await supabase
  .from('analyses')
  .select('*')
  .order('created_at', { ascending: false })
```

Row Level Security ensures this only returns rows where `user_id = auth.uid()`.

### Update dispute status
```js
await supabase
  .from('analyses')
  .update({ dispute_status: 'submitted' })
  .eq('id', analysisId)
```

### Delete an analysis
```js
await supabase.from('analyses').delete().eq('id', analysisId)
```

---

## Analysis Data Structures

### `structured_data` object

| Field | Type | Description |
|-------|------|-------------|
| `patient_name` | string | Patient name or `"Not found"` |
| `date_of_service` | string | ISO date or `"Not found"` |
| `provider_name` | string | Provider/clinic name |
| `provider_address` | string | Provider address |
| `charges` | array | Line items — see below |
| `total` | number | Total bill amount |
| `insurance_info` | string | Insurance provider name |
| `patient_responsibility` | number | Amount patient owes |

**Charge item:**
```json
{ "item": "Service name", "cost": 250.00, "code": "CPT code" }
```

### `analysis_results` object

| Field | Type | Description |
|-------|------|-------------|
| `issues` | array | Detected billing issues — see below |
| `overall_severity` | string | `low` / `medium` / `high` |
| `potential_savings` | number | Estimated recoverable amount |
| `recommendations` | array | Actionable advice strings |

**Issue item:**
```json
{
  "type": "overcharge",
  "description": "Plain-English description of the issue",
  "item": "Affected charge name",
  "severity": "high"
}
```

---

## Issue Types

| Type | Description |
|------|-------------|
| `overcharge` | Service priced significantly above typical rates |
| `duplicate` | Same service billed more than once |
| `missing_adjustment` | Expected insurance adjustment not applied |
| `unbundling` | Procedures billed separately that should be bundled |

## Severity Levels

| Level | Meaning |
|-------|---------|
| `low` | Minor concern, informational |
| `medium` | Potential billing error worth reviewing |
| `high` | Likely overcharge or duplicate — recommend disputing |

## Dispute Status Values (Supabase)

| Value | Meaning |
|-------|---------|
| `none` | No dispute initiated |
| `submitted` | Dispute letter/email sent |
| `in_progress` | Provider acknowledged, under review |
| `resolved` | Dispute resolved (amount corrected) |
| `rejected` | Dispute rejected by provider |
