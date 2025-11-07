# Migration Guide: OpenAI to Google Gemini

This guide helps you migrate from OpenAI to Google Gemini API.

## Why Gemini?

- **Free Tier**: Generous free tier with 15 requests per minute
- **Fast**: Gemini 2.0 Flash is optimized for speed
- **Cost-Effective**: Lower costs for production use
- **No Credit Card Required**: Get started immediately without payment info

## Migration Steps

### 1. Get Gemini API Key

1. Visit https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Update Environment Variables

Edit your `.env` file:

**Before (OpenAI):**
```env
OPENAI_API_KEY=sk-proj-...
UPLOAD_FOLDER=uploads
```

**After (Gemini):**
```env
GEMINI_API_KEY=AIza...
UPLOAD_FOLDER=uploads
```

### 3. Update Dependencies

The code has already been updated. Just reinstall dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

This will install `google-generativeai` instead of `openai`.

### 4. Verify Setup

Run the test script:

```powershell
python test_setup.py
```

You should see:
```
✓ google-generativeai
✓ GEMINI_API_KEY is set
```

### 5. Restart the Backend

```powershell
python run.py
```

## What Changed?

### Code Changes
- `llm_service.py`: Now uses `google.generativeai` SDK
- Model: Changed from `gpt-4o-mini` to `gemini-2.0-flash-exp`
- API calls: Adapted to Gemini's API structure

### Behavior Changes
- **Response Format**: Gemini uses `response_mime_type` instead of `response_format`
- **System Instructions**: Passed as a separate parameter
- **Temperature**: Works the same way (0.1 for structured, 0.7 for creative)

### No Changes Required
- Frontend code (already compatible)
- Database schema
- API endpoints
- File upload/extraction logic

## Comparison

| Feature | OpenAI GPT-4o-mini | Google Gemini 2.0 Flash |
|---------|-------------------|------------------------|
| **Free Tier** | $5 credit (expires) | 15 RPM forever |
| **Speed** | ~2-3 seconds | ~1-2 seconds |
| **Cost (1M tokens)** | $0.15 input / $0.60 output | $0.075 input / $0.30 output |
| **Context Window** | 128K tokens | 1M tokens |
| **JSON Mode** | ✓ | ✓ |
| **Credit Card** | Required after trial | Not required |

## Troubleshooting

### "API Key not found" error
- Make sure `.env` file exists in `backend/` directory
- Check that it says `GEMINI_API_KEY=` not `OPENAI_API_KEY=`
- Verify no extra spaces around the key

### "Import google.generativeai could not be resolved"
- Run `pip install google-generativeai`
- If using a virtual environment, make sure it's activated

### Rate limit errors
- Free tier: 15 requests per minute
- Wait a minute and try again
- Or upgrade to paid tier for higher limits

### Different responses than OpenAI
- Gemini may format responses slightly differently
- Both models are highly capable for this task
- If issues persist, adjust prompts in `llm_service.py`

## Rollback (If Needed)

If you need to go back to OpenAI:

1. **Revert code**: `git checkout HEAD~1 backend/llm_service.py`
2. **Update requirements**: Change `google-generativeai` to `openai`
3. **Change .env**: Use `OPENAI_API_KEY` instead
4. **Reinstall**: `pip install -r requirements.txt`

## Getting Help

- **Gemini API Docs**: https://ai.google.dev/docs
- **API Key Issues**: https://aistudio.google.com/app/apikey
- **Rate Limits**: https://ai.google.dev/pricing

---

**Migration Date**: November 7, 2025  
**Status**: ✅ Complete and Tested
