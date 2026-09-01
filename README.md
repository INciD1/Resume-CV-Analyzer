# Smart Resume Analyzer 📄🤖

## Overview
This is a **conceptual academic project** developed for the course *Introduction to Natural Language Processing*.  
The system automates resume screening by extracting key information and evaluating candidate suitability against job descriptions.  

⚠️ Note: This project is a **prototype for educational purposes** and not a production-ready system. It can be used as a base for further development.  

## Features
- Extracts **name, email, and skills** from resumes (PDF & images).  
- Supports **100+ predefined skills recognition** (legacy pipeline).  
- Calculates candidate-job fit using **TF-IDF** and **Cosine Similarity** (legacy pipeline).  
- **NEW — LLM-assisted pipeline** (`llm_pipeline.py`): when `ANTHROPIC_API_KEY` is set, resumes
  are parsed into a structured profile (education, experience, skills — Thai or English,
  no fixed skill list needed) and matched against the job description directly by an LLM,
  which returns a score **plus a short explanation** (matched/missing skills, experience fit,
  education fit, and a natural-language reasoning sentence). No key configured → the app
  falls back to the original TF-IDF pipeline automatically, so it still runs standalone.
- Generates **JSON output** for processed results.  
- Visualizes results with **charts, heatmaps, and score rankings**.  

## Tech Stack
- **Web Framework**: Flask (Python), HTML, CSS, JavaScript  
- **Data Processing**: pdfplumber, OCR.space API, pandas, numpy, NLTK  
- **Analysis**: scikit-learn (TF-IDF, Cosine Similarity) for the legacy pipeline;
  Anthropic Claude API (`anthropic` SDK) for the LLM-assisted pipeline  
- **Visualization**: matplotlib, seaborn, Chart.js  

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your ANTHROPIC_API_KEY (optional)
python app.py
```
Without an `ANTHROPIC_API_KEY`, the app runs exactly as it did before (TF-IDF pipeline).
With one set, uploads are analyzed by the LLM pipeline instead — look for the
"ประเมินด้วย AI (LLM-assisted)" badge on the results page to confirm which mode ran.

## Future Improvements
- [x] ~~Improve skill recognition using ML models.~~ → done via `llm_pipeline.extract_profile`
- [x] ~~Add analysis of **work experience & education**.~~ → done via `llm_pipeline.extract_profile`
- [x] ~~Support **multi-language resumes**~~ (Thai/English) → handled by the LLM pipeline; the
      legacy pipeline still needs `pythainlp` integration for Thai tokenization if you want it
      to work without an API key too.
- Provide an **API for integration** with other HR systems (e.g. a FastAPI layer over
  `ResumeAnalyzer`/`llm_pipeline`).
- Suggest **best-fit job positions** automatically.
- Add a **fairness/bias audit** pass (e.g. blind screening — strip name/school before scoring,
  only reattach for the final HR-facing report).
- Swap OCR.space for a locally-run OCR (PaddleOCR/Tesseract) to remove the external API
  dependency and rate limits.
- Move results storage from flat JSON files to a proper database (SQLite/Postgres) for
  querying candidate history across sessions.

## Author
- **Auchukorn Veschapun** (6630611033)  

---
