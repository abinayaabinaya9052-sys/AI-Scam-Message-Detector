# AI Scam Message Detector Chatbot — Build Guide (matches your architecture diagram)

## How the pieces map to your diagram

| # | Box | File |
|---|-----|------|
| 1 | User pastes SMS/WhatsApp message | `templates/index.html` (textarea) |
| 2 | Chatbot Interface | `templates/index.html`, `static/script.js`, `static/style.css` |
| 3 | Backend Server (Flask) | `app.py` → `/` and `/api/analyze` routes |
| 4 | Text Processing (NLP) | `clean_text()`, `tokenize()`, `extract_features()` in `app.py` |
| 5 | Gemini API | `analyze_with_gemini()` in `app.py` |
| 6 | Response Generator | JSON built inside `analyze_with_gemini()` / prompt in `build_prompt()` |
| 7 | Chatbot Response | returned by `/api/analyze`, rendered by `script.js` |
| 8 | Dataset (few-shot examples) | `FEW_SHOT_EXAMPLES` in `app.py` |
| 9 | Gemini Prompt | `build_prompt()` in `app.py` |
| 10 | Database (Supabase) | `save_to_supabase()` in `app.py`, schema in `supabase_schema.sql` |

## Setup steps

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a Gemini API key**
   - Go to https://aistudio.google.com/apikey and create a key.

3. **Set up Supabase**
   - Create a project at https://supabase.com
   - Open the SQL editor and run `supabase_schema.sql`
   - Copy your Project URL and anon/service key from Settings → API

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # then edit .env and paste your keys
   ```

5. **Run the app**
   ```bash
   python app.py
   ```
   Open http://127.0.0.1:5000

## Request flow (top to bottom, exactly like your diagram)

1. User types/pastes a message in the browser (`index.html`).
2. `script.js` POSTs `{ "message": "..." }` to `/api/analyze`.
3. Flask (`app.py`) receives it.
4. `clean_text()` strips links/emoji/extra spaces → `tokenize()` splits into words → `extract_features()` pulls quick signals (mentions money, asks for OTP, urgency words, etc.).
5. `build_prompt()` combines the cleaned message + few-shot examples (box 8) + extracted features into the prompt sent to Gemini (box 9).
6. `analyze_with_gemini()` calls the Gemini API and parses the structured JSON response (risk level, reasons, tips, suggestion).
7. `save_to_supabase()` logs the original message, cleaned message, and Gemini's verdict into the `scam_checks` table.
8. Flask returns JSON to the frontend.
9. `script.js` renders the chatbot's reply bubble, color-coded by risk level (green = safe, amber = suspicious, red = high risk).

## Notes / next steps
- Swap `gemini-1.5-flash` for a newer model name if you have access to one — check available models in Google AI Studio, since model names change over time.
- Add rate limiting (e.g. Flask-Limiter) before deploying publicly, since Gemini calls cost money per request.
- For WhatsApp integration specifically, you'd add a webhook route (e.g. via Twilio or WhatsApp Business API) that calls the same `analyze_with_gemini()` logic instead of the browser UI.
