# AI Engineering Drawing & Manufacturing Risk Checker

## Run
```text
cd AI_Drawing_Risk_Checker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Demo
Select **Demo Mode** → **LOAD DEMO DRAWING** → **ANALYZE DRAWING**.

Demo Mode is intentionally deterministic so the hackathon video does not depend on an API/network connection.

## AI Mode
Set:
```text
set OPENAI_API_KEY=YOUR_KEY
set OPENAI_MODEL=gpt-5.6-luna
```
Then run Streamlit. AI Mode uses a multimodal model to analyze the uploaded image and return structured JSON.

## MVP limitations
- PDF: first page only.
- GD&T: not a validated production capability.
- Risk thresholds are screening guidance, not universal manufacturing limits.
- Final engineering approval remains with a qualified engineer.
