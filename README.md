# Chatbot using Langraph

An interactive **multi-conversation chatbot** built with **Streamlit**, **LangGraph**, and **SQLite**.
It supports conversation persistence, multiple chat threads, **tool usage** (search, calculator, stock prices), **LangSmith tracking**, and automatic conversation naming.

---

## 🚀 Features

* **Multi-threaded chats** – Each conversation is stored under a unique `thread_id`.
* **Persistent storage** – Uses SQLite + LangGraph `SqliteSaver` to save conversations.
* **Automatic chat titles** – First user message is summarized (≤4 words) and saved as the chat name.
* **Conversation history** – Easily switch between chats via the sidebar.
* **Streaming responses** – AI responses stream live into the UI.
* **Tool support** –

  * 🌐 Web search (DuckDuckGo)
  * ➗ Calculator (basic arithmetic)
  * 📈 Stock price lookup (Alpha Vantage API)
* **LangSmith integration** – Track, debug, and monitor queries made by the chatbot.

---

## ⚠️ Streaming Note

Gemini (`gemini-2.5-flash`) supports streaming but may behave differently compared to OpenAI models.
👉 If you switch to **OpenAI models** (e.g., `gpt-4o-mini`), response streaming works **smoothly and reliably**.

---

## 🛠️ Tech Stack

* [Streamlit](https://streamlit.io/) – Frontend UI
* [LangGraph](https://www.langchain.com/langgraph) – Conversation graph management
* [LangChain](https://www.langchain.com/) – Message handling
* [SQLite](https://www.sqlite.org/) – Persistent conversation storage
* [Google Generative AI](https://ai.google.dev/) – LLM backend (Gemini-2.5-flash)
* [DuckDuckGo Search API](https://pypi.org/project/duckduckgo-search/) – Web search tool
* [Alpha Vantage](https://www.alphavantage.co/) – Stock price tool
* [LangSmith](https://smith.langchain.com/) – Query monitoring, debugging, and tracing

---

## 📂 Project Structure

```
.
├── frontend.py                 # Streamlit app
├── backend.py                  # LangGraph + SQLite backend + tools
├── chatbot.db                  # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
├── .env                        # API keys & environment variables
├── .gitignore                  # Ignore unnecessary files in Git
└── README.md                   # Project documentation
```

---

## ⚙️ Setup & Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/NiharikaBarnwal/Chatbot-using-LangGraph.git
   cd Chatbot-using-LangGraph
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate    # Mac/Linux
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:

   ```ini
   GOOGLE_API_KEY=your_google_api_key_here
   ALPHAVANTAGE_API_KEY=your_alpha_vantage_api_key_here
   LANGSMITH_ENDPOINT='https://api.smith.langchain.com'
   LANGSMITH_API_KEY=your_langsmith_api_key_here
   LANGSMITH_TRACING_V2=true
   LANGSMITH_PROJECT=LangGraph-Chatbot
   ```

---

## ▶️ Run the App

Start the backend (database + graph will initialize automatically):

```bash
python backend.py
```

Then launch the Streamlit frontend:

```bash
streamlit run frontend.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser. 🎉

---

## 💾 Database Schema

The app creates two tables in `chatbot.db`:

* **`chat_threads`**: Stores thread IDs and chat names
* **LangGraph checkpoint tables**: Store conversation states (messages, tool usage, etc.)

---

## 🧩 Example Workflow

1. Start a **new chat** from the sidebar.
2. Type your query → Chat title is auto-generated.
3. AI responds in real-time.
4. If needed, the bot may use tools (search, calculator, stock lookup).
5. Switch between past conversations in the sidebar.
6. All queries are logged and traceable in **LangSmith dashboard**.

---

## 🔮 Future Improvements

* ✅ Rename conversations manually
* ✅ Delete old chats
* ✅ Dark mode toggle
* ✅ Support for system prompts
* ✅ Enhanced UI with markdown rendering
* ✅ Tool usage logging & visualization
* ✅ More tool integrations (weather, news, etc.)