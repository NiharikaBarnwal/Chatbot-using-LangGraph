# Chatbot using LangGraph

An interactive **multi-conversation chatbot** built with **Streamlit**, **LangGraph**, and **SQLite**. It supports conversation persistence, multiple chat threads, **tool usage** (web search, calculator, stock prices, **PDF RAG**), optional **LangSmith** tracing, and automatic conversation naming.

---

## Features

* **Multi-threaded chats** – Each conversation uses a unique `thread_id` (LangGraph checkpointing).
* **Persistent storage** – SQLite + LangGraph `SqliteSaver` for message history; a small `chat_names` table stores sidebar titles.
* **PDF RAG** – Upload a PDF per chat; chunks are embedded with **Google Generative AI** and retrieved via FAISS (in-memory for the running process).
* **Automatic chat titles** – The first user message is summarized (≤4 words) and saved as the chat name.
* **Conversation history** – Switch chats from the sidebar; tool-use status appears during streaming when applicable.
* **Streaming responses** – Assistant tokens stream in the main chat area (Gemini via `langchain-google-genai`).
* **Tools**

  * Web search (DuckDuckGo)
  * Calculator (basic arithmetic)
  * Stock price lookup (Alpha Vantage)
  * **RAG** over the PDF indexed for the current thread

---

## Streaming Note

Gemini (`gemini-2.5-flash`) supports streaming but may behave differently compared to OpenAI models.
If you switch to **OpenAI models** (e.g., `gpt-4o-mini`), response streaming works **smoothly and reliably**.

---

## Tech stack

| Layer | Technology |
| --- | --- |
| UI | [Streamlit](https://streamlit.io/) |
| Orchestration | [LangGraph](https://www.langchain.com/langgraph) |
| LLM & embeddings | [Google Gemini](https://ai.google.dev/) via [langchain-google-genai](https://pypi.org/project/langchain-google-genai/) |
| Vectors (RAG) | [FAISS](https://github.com/facebookresearch/faiss) (LangChain community) |
| Persistence | [SQLite](https://www.sqlite.org/) (`chatbot.db`) |
| Search tool | [duckduckgo-search](https://pypi.org/project/ddgs/) (`ddgs` on PyPI) |
| Stock tool | [Alpha Vantage](https://www.alphavantage.co/) (optional) |
| Tracing (optional) | [LangSmith](https://smith.langchain.com/) |

---

## Project structure

```
.
├── frontend.py          # Streamlit app (run this)
├── backend.py           # LangGraph graph, tools, Gemini, PDF ingestion
├── chatbot.db           # SQLite DB (created on first run)
├── requirements.txt
├── .env                 # API keys (create locally; do not commit)
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone and enter the project

```bash
git clone https://github.com/NiharikaBarnwal/Chatbot-using-LangGraph.git
cd Chatbot-using-LangGraph
```

### 2. Virtual environment

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables

Create a `.env` file in the project root.

**Required (Gemini Developer API)**

```ini
GOOGLE_API_KEY=your_google_api_key_here
```

`GEMINI_API_KEY` is also supported by the Google integration as a fallback.

**Optional – model overrides**

```ini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2-preview
```

If an embedding model is unavailable for your account, try another ID listed in [Google AI Studio](https://aistudio.google.com/) for embeddings.

**Optional – Alpha Vantage (stock tool)**

```ini
ALPHAVANTAGE_API_KEY=your_alpha_vantage_key_here
```

**Optional – LangSmith**

```ini
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=LangGraph-Chatbot
```

Use current LangSmith env names from the [LangSmith docs](https://docs.smith.langchain.com/) if these differ in your SDK version.

---

## Run the app

The graph and database initialize when the backend module loads. You only need to start Streamlit:

```bash
streamlit run frontend.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Database notes

* **`chat_names`** – Maps `thread_id` (text) to the short title shown in the sidebar.
* **LangGraph checkpoint tables** – Managed by `SqliteSaver`; store graph state and messages per thread.

PDF vectors are **not** stored in SQLite; they live in process memory. After a full app restart, re-upload PDFs if you need RAG for old threads (conversation text still loads from checkpoints).

---

## Example workflow

1. Click **New Chat** if you want a fresh thread.
2. Optionally **upload a PDF** for that thread, then ask questions about it (the model uses the RAG tool with your thread id).
3. Ask general questions; the assistant may call search, calculator, or stock tools when useful.
4. Switch **My conversations** in the sidebar to load prior threads.

---

## Future improvements

* Rename or delete conversations from the UI
* Persist vector stores across restarts (e.g. disk-backed FAISS or a hosted vector DB)
* Dark mode and richer markdown in the chat pane
* Additional tools (weather, news, etc.)
