# EquityLens

**An interactive AI stock analysis assistant built with Python and React.** Ask a market question and let a tool-using agent retrieve Yahoo Finance data, then compose an interactive response in the chat interface.

EquityLens is a portfolio adaptation of the *AI Financial Analyst Agent* class assignment and the [NeuralNine walkthrough](https://youtu.be/AE_6F8cuXsA). It follows the tutorial's FastAPI, LangChain, yfinance, and C1Chat architecture, with additional input validation, normalized tool outputs, tests, and setup guidance. The tutorial's reference implementation is in [NeuralNine's public tutorial repository](https://github.com/NeuralNine/youtube-tutorials/tree/main/AI%20Stock%20Analysis%20Assistant).

## Capabilities

- Retrieve the latest available closing price for a ticker.
- Fetch historical prices for a date range to support comparisons and charts.
- Review a company's balance sheet.
- Retrieve recent company news.
- Keep conversation context by thread while streaming the agent response.
- Render assistant-generated charts, summaries, and follow-up actions through C1Chat.

The assistant is designed for public-market research and education. Its output can be incomplete or wrong and is not investment advice.

## Example questions

- "What is the latest available closing price for AAPL?"
- "Plot NVDA closing prices from 2026-01-01 to 2026-06-01."
- "Show me the latest annual balance sheet for MSFT."
- "Summarize the latest news for AMZN and give me the source links."

You can ask follow-up questions in the same chat, such as asking the assistant to compare periods or explain a balance-sheet line item.

## Architecture

```text
React + Vite + C1Chat
	| POST /api/chat (stream)
	v
FastAPI + LangChain agent + LangGraph checkpoint
	| tools
	v
Yahoo Finance via yfinance
	|
	v
Thesys C1 model endpoint
```

## Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer and npm
- A Thesys API key for generated-UI model responses
- Network access to Yahoo Finance

## Configure

If you do not already have a `.env` file, copy `.env.example` to `.env` in the repository root. Set `THESYS_API_KEY` to the key created under **Backend credentials** in the Thesys console. The key is read by the backend only; do not put it in frontend code or commit `.env`.

```text
THESYS_API_KEY=your-thesys-api-key
THESYS_MODEL=c1/openai/gpt-5/v-20250930
```

The backend also accepts `OPENAI_API_KEY` as a compatibility fallback for the tutorial's original setup. Both variables must contain a Thesys key because requests are sent to `https://api.thesys.dev/v1/embed/`.

## Run locally

Install backend dependencies from the repository root:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .\backend
```

In one terminal, start the API:

```powershell
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8888 --reload
```

In another terminal, install and start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Vite forwards `/api` requests to the FastAPI server on port `8888`.

## Tests

```powershell
python -m unittest discover -s backend/tests -v
```

## Data and limitations

The agent calls Yahoo Finance through `yfinance`. Quote freshness, news coverage, and financial statement availability depend on the upstream provider. Prices may be delayed. Conversation checkpoints are held in memory and are lost when the backend restarts. The model can misinterpret or misstate returned data, so verify important figures independently. This project does not provide personalized investment advice or recommendations.

## Technology

Python, FastAPI, LangChain, LangGraph, yfinance, React, TypeScript, Vite, and Thesys C1Chat.