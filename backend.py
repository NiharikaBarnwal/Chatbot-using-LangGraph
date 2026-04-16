from __future__ import annotations

import os
import sqlite3
import tempfile
from typing import Annotated, Any, Dict, Optional, TypedDict

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import requests

load_dotenv()

# Gemini Developer API: set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env
_GEMINI_CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview")

# **************** LLM + embeddings *******************
llm = ChatGoogleGenerativeAI(model=_GEMINI_CHAT_MODEL)
embeddings = GoogleGenerativeAIEmbeddings(model=_GEMINI_EMBEDDING_MODEL)

# **************** PDF retriever store (per thread)
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}


def _get_retriever(thread_id: Optional[str]):
    """Fetch the retriever for a thread if available."""
    if thread_id and thread_id in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[thread_id]
    return None


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """
    Build a FAISS retriever for the uploaded PDF and store it for the thread.

    Returns a summary dict that can be surfaced in the UI.
    """
    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(docs)

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}
        )

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_METADATA[str(thread_id)] = {
            "filename": filename or os.path.basename(temp_path),
            "documents": len(docs),
            "chunks": len(chunks),
        }

        return {
            "filename": filename or os.path.basename(temp_path),
            "documents": len(docs),
            "chunks": len(chunks),
        }
    finally:
        # The FAISS store keeps copies of the text, so the temp file is safe to remove.
        try:
            os.remove(temp_path)
        except OSError:
            pass


# **************** Tools *******************
# search tool
search_tool = DuckDuckGoSearchRun(region="us-en")

# calculator tool
@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

# stock price tool
@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch the current stock price for a given ticker symbol using Alpha Vantage.
    """
    try:
        api_key = os.getenv("ALPHAVANTAGE_API_KEY")
        if not api_key:
            return {"error": "Missing ALPHAVANTAGE_API_KEY in environment variables"}

        url = (
            f"https://www.alphavantage.co/query"
            f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        )
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# rag tool
@tool
def rag_tool(query: str, thread_id: Optional[str] = None) -> dict:
    """
    Retrieve relevant information from the uploaded PDF for this chat thread.
    Always include the thread_id when calling this tool.
    """
    retriever = _get_retriever(thread_id)
    if retriever is None:
        return {
            "error": "No document indexed for this chat. Upload a PDF first.",
            "query": query,
        }

    result = retriever.invoke(query)
    context = [doc.page_content for doc in result]
    metadata = [doc.metadata for doc in result]

    return {
        "query": query,
        "context": context,
        "metadata": metadata,
        "source_file": _THREAD_METADATA.get(str(thread_id), {}).get("filename"),
    }


# Make tool list
tools = [search_tool, get_stock_price, calculator, rag_tool]

# Make the LLM tool-aware
llm_with_tools = llm.bind_tools(tools)


# ***************** State ***********************
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ***************** Graph Nodes ******************
def chat_node(state: ChatState, config=None):
    """LLM node that may answer or request a tool call."""
    thread_id = None
    if config and isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id")

    system_message = SystemMessage(
        content=(
            "You are a helpful assistant. For questions about the uploaded PDF, call "
            "the `rag_tool` and include the thread_id "
            f"`{thread_id}`. You can also use the web search, stock price, and "
            "calculator tools when helpful. If no document is available, ask the user "
            "to upload a PDF."
        )
    )

    messages = [system_message, *state["messages"]]
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}


tool_node = ToolNode(tools)


# **************** Database Connection *******************
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn= conn)


# ***************** Graph ***************************
graph = StateGraph(ChatState)

# add node
graph.add_node('chat_node', chat_node)
graph.add_node("tools", tool_node)

# add edges
graph.add_edge(START, 'chat_node')
# If the LLM asked for a tool, go to the tool node; else finish
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer= checkpointer)

# Alias for UI layers that expect `model`
model = llm


def _ensure_chat_names_table() -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chat_names (thread_id TEXT PRIMARY KEY, name TEXT NOT NULL)"
    )
    conn.commit()


def load_chat_names() -> Dict[str, str]:
    _ensure_chat_names_table()
    cur = conn.execute("SELECT thread_id, name FROM chat_names")
    return {row[0]: row[1] for row in cur.fetchall()}


def save_chat_name(thread_id: Any, name: str) -> None:
    _ensure_chat_names_table()
    conn.execute(
        "INSERT OR REPLACE INTO chat_names (thread_id, name) VALUES (?, ?)",
        (str(thread_id), name),
    )
    conn.commit()


# **************** Helpers *******************
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def thread_has_document(thread_id: str) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS


def thread_document_metadata(thread_id: str) -> dict:
    return _THREAD_METADATA.get(str(thread_id), {})
