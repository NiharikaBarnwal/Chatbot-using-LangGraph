# LangGraph Chatbot

An interactive **multi-conversation chatbot** built with **Streamlit**, **LangGraph**, and **SQLite**.
It supports conversation persistence, multiple chat threads, and automatic conversation naming.

---

## 🚀 Features

* **Multi-threaded chats** – Each conversation is stored under a unique `thread_id`.
* **Persistent storage** – Uses SQLite + LangGraph `SqliteSaver` to save conversations.
* **Automatic chat titles** – First user message is summarized (≤4 words) and saved as the chat name.
* **Conversation history** – Easily switch between chats via the sidebar.
* **Streaming responses** – AI responses stream live into the UI.

---

## 🛠️ Tech Stack

* [Streamlit](https://streamlit.io/) – Frontend UI
* [LangGraph](https://www.langchain.com/langgraph) – Conversation graph management
* [LangChain](https://www.langchain.com/) – Message handling
* [SQLite](https://www.sqlite.org/) – Persistent conversation storage
* [Google Generative AI](https://ai.google.dev/) – LLM backend (Gemini-2.5-flash)

---

## 📂 Project Structure

```
.
├── frontend.py                 # Streamlit app
├── backend.py                  # LangGraph + SQLite backend
├── chatbot.db                  # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
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
* **LangGraph checkpoint tables**: Store conversation states

---

## 🧩 Example Workflow

1. Start a **new chat** from the sidebar.
2. Type your query → Chat title is auto-generated.
3. Chat responses stream live.
4. Switch between past conversations in the sidebar.

---

## 🔮 Future Improvements

* ✅ Rename conversations manually
* ✅ Delete old chats
* ✅ Dark mode toggle
* ✅ Support for system prompts
* ✅ Enhanced UI with markdown rendering
