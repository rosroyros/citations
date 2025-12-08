# Plan: 50/50 Gemini vs OpenAI A/B Test

## Objective
Implement a 50/50 split test between OpenAI (current) and Gemini (new) for citation validation. 
- **Stickiness:** Per user session via Local Storage (`model_a` vs `model_b`).
- **Data Flow:** Provider selection stored in-memory (`jobs` dict) and shipped via structured `app.log` events.
- **Dashboard:** Update UI to show "Provider" in table and modal.

## 1. Prerequisites & Dependencies
- [ ] **Dependencies:** Add `google-genai` to `requirements.txt`.
- [ ] **Configuration:** Ensure `GEMINI_API_KEY` is in `.env` and `app.py` checks for it.

## 2. Frontend Implementation (Client Logic)
**Location:** `frontend/frontend/src/`

- [ ] **Stickiness Logic:**
  - Check `localStorage` for `model_preference`.
  - If missing: `Math.random() < 0.5 ? 'model_b' : 'model_a'`. Store result.
  - `model_a` = OpenAI (`gpt-5-mini` - Default)
  - `model_b` = Gemini (`gemini-2.5-flash` - Challenger)
- [ ] **API Call:** Send header `X-Model-Preference: <value>` with validation requests.
- [ ] **Dashboard UI:**
  - **Data Table:** Add "Provider" column. Map `model_a` -> "OpenAI", `model_b` -> "Gemini".
  - **Job Detail Modal:** Add "Model Provider" field.

## 3. Backend: Gemini Provider (Adapter)
**Location:** `backend/providers/gemini_provider.py`

- [ ] **Create Class:** `GeminiProvider` implementing `CitationValidator`.
- [ ] **Implementation:**
  - Use `google.generativeai` SDK with `gemini-2.5-flash`.
  - **Prompt Strategy:** Send prompt as **User Content** (not system instruction).
  - **Adapter Logic:** The provider MUST transform Gemini's response into the exact `CitationResult` dictionary structure used by `OpenAIProvider`.

## 4. Backend: API & Routing
**Location:** `backend/app.py`

- [ ] **Initialization:** Instantiate `GeminiProvider` alongside `OpenAIProvider`.
- [ ] **Routing & Fallback:**
  - In `validate_citations`: extract `X-Model-Preference`.
  - **Logic:**
    - `model_b` -> Try `GeminiProvider`.
      - **Fallback:** If Gemini fails, log error, fallback to `OpenAIProvider`, and record provider as `model_a` (fallback).
    - `model_a` OR missing header OR invalid value -> Use `OpenAIProvider`.
- [ ] **Job Storage (In-Memory):**
  - Store `provider` (internal ID) in the `jobs[job_id]` dictionary.
  - *Note:* This ensures the `/api/dashboard` endpoint immediately serves this data.
- ] **Logging (Data Shipping):**
  - **Target:** `citations.log` (The specific log file ingested by the dashboard parser).
  - **Action:** Update `log_citations_to_dashboard` to write a metadata line immediately after the job ID marker.
  - **Format:** `<<METADATA:provider=gemini>>` (or `openai`).
  - *Note:* This allows the existing `CitationLogParser` to extract the provider during its standard parsing loop without requiring a new parser for `app.log`.


## 5. Verification
- [ ] **Test:** Verify missing header defaults to `model_a`.
- [ ] **Test:** Verify `model_b` triggers Gemini.
- [ ] **Test:** Verify Gemini failure falls back to OpenAI (`model_a`).
- [ ] **Test:** Verify Dashboard UI shows "OpenAI" or "Gemini" correctly.

## 6. Verification
- [ ] **Test:** Verify `X-Provider-Preference` header switches models.
- [ ] **Test:** Verify Local Storage persistence survives page reload.
- [ ] **Test:** Verify graceful fallback (force Gemini failure and ensure OpenAI picks it up).
- [ ] **Test:** Verify logs contain the provider info.
- [ ] **Test:** Verify dashboard shows the provider column/info.
