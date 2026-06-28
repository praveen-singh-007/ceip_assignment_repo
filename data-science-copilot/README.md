# Autonomous Data Science Co-Pilot

Final project submission for the CEIP assignment repository.

This project is an AI-powered junior data analyst. It lets a user upload a CSV,
Excel, or JSON dataset, ask questions in plain English, and receive generated
Python/Pandas analysis, charts, result tables, and a downloadable report. The
agent can self-correct failed code by retrieving relevant local documentation
snippets for Python, Pandas, NumPy, Matplotlib, and Seaborn.

## Official Submission UI: Streamlit

The Streamlit application:

```text
backend/streamlit_app.py
```

Run it with:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

For Streamlit Community Cloud, use this main file path:

```text
backend/streamlit_app.py
```

The Streamlit app is the primary UI for evaluation. It uses the same backend
agent modules as the rest of the project.

## Optional College Demo UI: Next.js

The project also includes a Next.js interface in `frontend/`. This was built for
college presentation/demo purposes. It is not required for the Streamlit
submission, but it can be shown separately as a richer web UI.

To run the Next.js UI:

```powershell
# Terminal 1
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

## Features

- Upload CSV, Excel, or JSON datasets.
- Use included sample datasets for quick testing.
- Ask ad-hoc business/data questions in natural language.
- Generate Python/Pandas analysis code with an LLM.
- Execute generated code in a restricted subprocess sandbox.
- Self-heal failed code using RAG over local documentation excerpts.
- Produce charts, insights, result tables, and Markdown reports.
- Inspect data quality: rows, columns, duplicates, missing values, data types,
  unique counts, and sample values.

## Project Structure

```text
backend/
  streamlit_app.py                 Official Streamlit UI for submission
  requirements.txt                 Python dependencies
  app/                             FastAPI service for optional Next.js UI
  agent/                           Core analysis/self-healing agent
    config.py
    data_loader.py
    prompts.py
    llm.py
    code_extractor.py
    code_safety.py
    sandbox_runner.py
    sandbox.py
    self_heal_agent.py
    report.py
    rag/                           Local RAG corpus, chunking, index, retriever
  data/                            Sample datasets
  tests/                           Smoke/manual tests
  outputs/                         Generated charts and reports at runtime

frontend/
  src/app/                         Next.js app router pages
  src/components/                  UI components
  src/lib/                         API client and shared types
  package.json
```

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

```powershell
cd backend
copy .env.example .env
```

Then add your Groq API key:

```text
GROQ_API_KEY=your_groq_api_key_here
```

Optional settings are documented in `backend/.env.example`.

## Testing

Backend smoke test:

```powershell
cd backend
python tests\test_smoke.py
```

Optional live tests that call Groq:

```powershell
cd backend
python tests\manual_e2e.py
python tests\manual_self_heal_force.py
```

Optional frontend checks:

```powershell
cd frontend
npm run build
npm run lint
```

## Notes

The generated-code runner uses subprocess isolation, AST checks, restricted
imports/builtins, and timeouts. This is suitable for a trusted local/internal
project demo, but it is not a replacement for a production-grade container,
VM, or microVM sandbox for untrusted public users.
