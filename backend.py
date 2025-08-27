from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3

load_dotenv()



model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    max_tokens=1024
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    # take user query from state
    messages = state['messages']

    # send to llm
    response = model.invoke(messages)

    # response store state
    return {'messages': [response]}


conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn= conn)

graph = StateGraph(ChatState)

# add node
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer= checkpointer)


# at backend startup
with conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_threads (
            thread_id TEXT PRIMARY KEY,
            name TEXT
        )
    """)

def save_chat_name(thread_id, name):
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO chat_threads (thread_id, name) VALUES (?, ?)",
            (str(thread_id), name)
        )

def load_chat_names():
    rows = conn.execute("SELECT thread_id, name FROM chat_threads").fetchall()
    return {row[0]: row[1] for row in rows}
