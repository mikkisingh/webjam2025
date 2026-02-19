# Product Requirements Document (PRD)
## MediCheck — AI-Powered Medical Bill Analysis Platform

**Version:** 1.0
**Date:** February 2026
**Status:** Draft

---

## 1. Executive Summary

MediCheck is a consumer-facing web application that empowers patients to understand, verify, and dispute their medical bills using AI. Medical billing errors affect an estimated **80% of medical bills** in the US, with patients collectively overpaying billions of dollars annually. MediCheck democratizes access to the kind of bill review that previously required hiring a professional medical billing advocate.

**Core value proposition:** Upload your medical bill in 30 seconds. Get a plain-English analysis in under 2 minutes. Know exactly what to dispute and how.

---

## 2. Problem Statement

### The Patient's Pain
- Medical bills are deliberately complex — dense codes, abbreviations, and line items that require expertise to interpret
- The average American doesn't know what CPT codes are, let alone whether a charge is inflated
- Hiring a medical billing advocate costs $50–$200/hour
- Patients often pay incorrect bills simply because they don't know they can dispute them
- Insurance Explanation of Benefits (EOBs) are equally confusing and rarely cross-referenced with the actual bill

### The Scale of the Problem
- ~80% of medical bills contain errors (Medical Billing Advocates of America)
- Average error amount: $1,300 per hospital stay
- Americans pay an estimated $935 billion in excess medical costs annually
- Only ~1 in 5 patients who dispute bills get a reduction — simply because most don't try

### Current Alternatives Are Inadequate
| Solution | Problem |
|----------|---------|
| DIY research | Time-consuming, requires medical billing knowledge |
| Billing advocate | Expensive ($50–$200/hr), not scalable |
| Hospital billing department | Conflict of interest |
| Insurance company | Focused on their costs, not patient responsibility |
| Generic AI chatbots | No specialized billing knowledge, no document parsing |

---

## 3. Target Users

### Primary: The Anxious Patient (Core User)
- **Profile:** Adults aged 25–65 who recently received a large medical bill ($500+)
- **Motivation:** Fear of overpaying, distrust of the billing system, financial stress
- **Behavior:** Will spend 30–60 min researching if they suspect an error
- **Technical comfort:** Moderate — comfortable uploading a document, reading structured results
- **Success metric:** Finds at least one issue they can act on

### Secondary: The Caregiver
- **Profile:** Adult children managing bills for elderly parents, spouses managing family healthcare
- **Motivation:** Protecting a loved one from financial exploitation
- **Behavior:** Proactive, organized, uploads multiple bills over time

### Tertiary: The Healthcare Professional
- **Profile:** Nurses, social workers, patient advocates at non-profits
- **Motivation:** Help patients they work with navigate billing
- **Behavior:** Power user, may process many bills, wants bulk features

### Out of Scope (v1)
- Insurance companies
- Hospital billing departments
- Legal teams building cases

---

## 4. Goals & Success Metrics

### Business Goals
| Goal | Metric | Target (6 months) |
|------|--------|-------------------|
| Grow user base | Monthly Active Users (MAU) | 10,000 MAU |
| Demonstrate value | Bills analyzed | 25,000 bills |
| Drive retention | 30-day return rate | 20% |
| Build trust | NPS score | 40+ |
| Sustainability | Conversion to paid tier | 5% of MAU |

### User Success Metrics
| Goal | Metric |
|------|--------|
| Find billing errors | % of analyzed bills with at least 1 issue flagged |
| Enable dispute | % of users who copy the dispute email |
| Save money | Self-reported savings (opt-in survey) |
| Reduce confusion | Post-analysis comprehension score (5-point survey) |

### Product Health Metrics
- Upload-to-analysis completion rate (target: >85%)
- Average analysis time (target: <90 seconds)
- False positive rate on issue detection (target: <15%)
- Support ticket rate (target: <2% of analyses)

---

## 5. Core Features (v1 — Public Launch)

### F1: Bill Upload & Text Extraction
**Current state:** Working
**Gaps to fix:**
- Add progress indicator during extraction
- Better error messages for password-protected PDFs
- Support multi-page bills (currently truncates at 2000 chars in AI prompt)
- Auto-delete uploaded files after analysis (privacy)

**User story:** As a patient, I want to upload my medical bill as a PDF or photo so that I don't have to manually type any information.

**Acceptance criteria:**
- Accepts PDF, JPG, PNG up to 16MB
- Drag-and-drop and click-to-browse
- Shows real-time upload progress bar
- Displays confirmation with file name and size
- Extracts text from multi-page PDFs (all pages, not just first)
- Auto-deletes the uploaded file from server within 1 hour of analysis

---

### F2: AI Bill Analysis
**Current state:** Working (3-step Gemini pipeline)
**Gaps to fix:**
- Full bill text passed to AI (currently truncated at 2000 chars)
- Add confidence scores to each detected issue
- Cross-reference against real pricing databases (future)
- Handle bills with no text (fully scanned/handwritten)

**User story:** As a patient, I want my bill automatically analyzed so I can understand what I'm being charged for and whether it looks correct.

**Acceptance criteria:**
- Extracts: patient name, provider, date of service, all line items with codes and costs, total, insurance info, patient responsibility
- Detects: overcharges (vs. typical rates), duplicates, missing insurance adjustments, unbundled procedures
- Assigns severity: low / medium / high per issue
- Produces a plain-English summary (non-technical language)
- Completes in under 90 seconds for a typical bill
- Graceful fallback if AI returns malformed JSON

---

### F3: Results Display
**Current state:** Working
**Gaps to fix:**
- Add color-coded severity badges (red/yellow/green)
- Add "What does this mean?" expandable explanations per issue type
- Show "potential savings" prominently
- Allow printing / PDF export of results
- Mobile-responsive layout

**User story:** As a patient, I want to see a clear, color-coded breakdown of my bill so I can quickly understand what's wrong and how much I might save.

**Acceptance criteria:**
- Summary section in plain English, no medical jargon
- Bill details: patient, provider, date, all charges in a sortable table
- Issues section: color-coded by severity, with plain-English explanations
- Potential savings total displayed prominently
- Recommendations list as actionable steps
- Print-friendly view

---

### F4: Dispute Email Generator
**Current state:** Working
**Gaps to fix:**
- Let users edit the email before copying
- Add "Send via Gmail" / "Open in mail client" button
- Provide multiple templates (formal dispute, simple inquiry, insurance complaint)

**User story:** As a patient, I want a ready-to-send email that I can use to dispute charges so I don't have to figure out what to write.

**Acceptance criteria:**
- Auto-generated email references specific disputed items and codes
- User can edit the email in-browser before copying
- One-click copy to clipboard
- Option to open in default mail client (mailto: link)
- Email addresses correct department (billing vs. insurance)

---

### F5: Bill History
**Current state:** Basic (GET /bills exists, no UI)
**Required for v1:**
- History page showing past analyses
- Click to re-view any past analysis
- Delete a bill and its data

**User story:** As a returning user, I want to see all my past bill analyses so I can track my disputes over time.

**Acceptance criteria:**
- List view: filename, upload date, status, total amount
- Click to view full analysis results
- Delete individual records (including uploaded file and all data)
- Empty state with CTA when no bills exist

---

### F6: User Accounts & Authentication
**Current state:** Not implemented — critical gap for public launch
**Required for v1 public:**
- Email + password signup/login
- "Magic link" (passwordless) option
- Google OAuth
- Session management

**Why this matters:** Without auth, any user can access any bill by ID — a serious privacy issue.

**User story:** As a user, I want my bills to be private and accessible only to me.

**Acceptance criteria:**
- Bills are scoped to authenticated user — users cannot access other users' bills
- Secure session tokens (JWT or session cookies, httpOnly)
- Password reset flow
- Account deletion (GDPR/CCPA compliance — deletes all user data)
- Optional: Google / Apple sign-in

---

### F7: Privacy & Data Handling
**Current state:** Not implemented — critical for public trust
**Required for v1 public:**

- Privacy policy (clear, plain English)
- Data retention policy: bills and uploads auto-deleted after N days
- HTTPS enforced
- No third-party analytics on bill content
- Explicit opt-in for any data used to improve the product

**Acceptance criteria:**
- HTTPS everywhere
- Uploaded files deleted from server immediately after text extraction
- Raw text deleted after user-specified retention period (default: 90 days)
- Privacy policy linked from every page
- Cookie consent banner (GDPR)
- One-click "Delete all my data" in account settings

---

## 6. Features NOT in v1 (Future Roadmap)

### v2 — Intelligence & Accuracy
- **Real pricing database integration** — Cross-reference charges against Medicare rates, FAIR Health, or Healthcare Bluebook to give data-backed "typical cost" comparisons instead of AI estimates
- **EOB cross-reference** — Upload both your bill and your Explanation of Benefits; detect mismatches between what insurance paid and what the provider billed
- **Confidence scores** — Show "high confidence" vs "possible issue" per detected problem
- **Procedure code lookup** — Let users click any CPT/ICD code to see a plain-English description

### v3 — Engagement & Retention
- **Dispute tracker** — Track the status of disputes (submitted, pending, resolved, amount recovered)
- **Outcome reporting** — "How much have I saved using MediCheck?"
- **Notifications** — Email alerts when a bill dispute deadline is approaching
- **Document vault** — Store EOBs, bills, and correspondence in one place

### v4 — Scale & Ecosystem
- **API for non-profits** — Let patient advocacy organizations process bills for their clients
- **Bulk upload** (caregiver use case)
- **Provider price transparency** — Search for a procedure before receiving care
- **Multilingual support** — Spanish first (large underserved population)
- **Mobile app** — Camera capture → instant analysis

### Monetization Options (to be validated)
| Model | Description | Pros | Cons |
|-------|-------------|------|------|
| Freemium | 3 free analyses/month, unlimited on paid tier ($9.99/mo) | Low friction, viral growth | Churn risk |
| Per-analysis | $2.99 per analysis | Aligns cost with value | Friction at moment of need |
| Outcome-based | 10% of recovered savings (user-reported) | Aligned incentives | Hard to verify, trust issues |
| B2B / API | Sell API access to non-profits, patient advocates | Predictable revenue | Longer sales cycle |
| Freemium + B2B | Free for individuals, paid API for orgs | Best of both | Complex pricing |

---

## 7. Non-Functional Requirements

### Security
- HTTPS enforced (TLS 1.2+)
- API rate limiting (max 10 uploads/hour per IP, 50/day per user)
- Input validation and file type verification (beyond extension check — verify MIME type)
- No PII logged in server logs
- Gemini API key stored as environment variable, never exposed to client
- OWASP Top 10 compliance audit before public launch

### Privacy
- Comply with HIPAA (if storing health data) — or explicitly design to NOT be a covered entity
- CCPA (California) and GDPR (EU) compliance
- Data minimization: only store what's needed for the feature
- Right to deletion: 30-day SLA for full data removal

### Performance
- Bill upload: <5 seconds for files up to 10MB
- Text extraction: <15 seconds
- AI analysis: <90 seconds end-to-end
- Frontend initial load: <2 seconds (LCP)
- 99.5% uptime target

### Accessibility
- WCAG 2.1 AA compliance
- Screen reader support for all results
- Keyboard navigation throughout
- Sufficient color contrast (not relying on color alone for severity)

### Scalability
- Designed for async processing (queue-based analysis for high load)
- Horizontal scaling of Flask workers
- File storage: move from local disk to S3 or equivalent
- Database: migrate from SQLite to PostgreSQL for production

---

## 8. Technical Gaps to Address Before Public Launch

| Gap | Priority | Effort |
|-----|----------|--------|
| User authentication | Critical | High |
| File privacy (delete after extraction) | Critical | Low |
| Bill scoped to user (not globally accessible by ID) | Critical | Medium |
| HTTPS / production deployment | Critical | Medium |
| Full bill text passed to AI (remove 2000-char truncation) | High | Low |
| Rate limiting | High | Low |
| Async job queue for analysis (avoid HTTP timeout) | High | Medium |
| File storage → cloud (S3) | High | Medium |
| SQLite → PostgreSQL | High | Medium |
| Mobile-responsive UI | High | Medium |
| Error handling for malformed AI responses | High | Low |
| Input validation (MIME type, not just extension) | High | Low |
| Bill history UI | Medium | Medium |
| Export results to PDF | Medium | Medium |
| Editable dispute email | Medium | Low |

---

## 9. Go-to-Market Considerations

### Distribution Channels
1. **Reddit communities** — r/personalfinance, r/HealthInsurance, r/medicine — organic trust-building
2. **Patient advocacy partnerships** — Non-profits already serving medical debt patients
3. **Content marketing** — "How to read your medical bill" blog/video series
4. **Social proof** — Share anonymized success stories ("User saved $1,200 on a hospital bill")
5. **Journalist outreach** — Healthcare billing is a perennial news story

### Trust-Building Requirements
- Clear, visible privacy policy
- "We never sell your data" prominently displayed
- No ads on the analysis page (ever)
- Show what data is sent to Gemini AI (transparency)
- Option to process locally / self-host (for privacy-conscious users)
- Security audit / penetration test results published

### Legal Considerations
- **Not medical advice disclaimer** — MediCheck provides informational analysis only, not legal or medical advice
- **HIPAA posture** — Either become a HIPAA Business Associate or design the product to avoid storing PHI (delete files immediately)
- **Terms of Service** — Acceptable use, limitation of liability
- **Jurisdictional compliance** — State-level healthcare billing regulations vary

---

## 10. Open Questions for Team Discussion

1. **HIPAA or not?** Do we become a covered entity / BAA, or do we architect around never persistently storing PHI? (Biggest legal decision)
2. **AI accuracy vs. liability** — How do we communicate the limitations of AI-detected issues without undermining user confidence?
3. **Pricing database** — Do we build our own, license from FAIR Health/Healthcare Bluebook, or use Medicare as a proxy?
4. **Self-hosting option** — Should we offer an open-source self-hosted version to build community trust?
5. **Monetization timing** — Launch free first to build trust and data, or charge from day 1?
6. **Scope of "analysis"** — Do we flag issues only, or do we tell users definitively "this is wrong"? (Legal risk)

---

*Document Owner: Product Team*
*Last Updated: February 2026*
*Next Review: March 2026*
