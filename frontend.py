import streamlit as st
from backend import (
    chatbot,
    ingest_pdf,
    load_chat_names,
    model,
    retrieve_all_threads,
    save_chat_name,
    thread_document_metadata,
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# ***************** Utility functions ********************
def generate_thread_id():
    return str(uuid.uuid4())

def add_thread(thread_id):
    key = str(thread_id)
    if key not in st.session_state['chat_threads']:
        st.session_state['chat_threads'][key] = "New Chat"

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={"configurable": {"thread_id": str(thread_id)}}
    )
    return state.values.get("messages", [])

# ***************** Session Setup ********************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = {}
    names = load_chat_names()
    for tid in retrieve_all_threads():
        k = str(tid)
        st.session_state['chat_threads'][k] = names.get(k, "New Chat")

if 'ingested_docs' not in st.session_state:
    st.session_state['ingested_docs'] = {}

add_thread(st.session_state['thread_id'])

thread_key = str(st.session_state["thread_id"])
thread_docs = st.session_state["ingested_docs"].setdefault(thread_key, {})
selected_thread = None

# ***************** Sidebar UI ********************
st.sidebar.title("LangGraph PDF Chatbot")
st.sidebar.markdown(f"**Thread ID:** `{thread_key}`")

if st.sidebar.button("New Chat", use_container_width=True):
    reset_chat()
    st.rerun()

if thread_docs:
    latest_doc = list(thread_docs.values())[-1]
    st.sidebar.success(
        f"Using `{latest_doc.get('filename')}` "
        f"({latest_doc.get('chunks')} chunks from {latest_doc.get('documents')} pages)"
    )
else:
    st.sidebar.info("No PDF indexed yet.")

uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat", type=["pdf"])
if uploaded_pdf:
    if uploaded_pdf.name in thread_docs:
        st.sidebar.info(f"`{uploaded_pdf.name}` already processed for this chat.")
    else:
        with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_key,
                filename=uploaded_pdf.name,
            )
            thread_docs[uploaded_pdf.name] = summary
            status_box.update(label="✅ PDF indexed", state="complete", expanded=False)

st.sidebar.header('My conversations')

for thread_id, name in reversed(list(st.session_state['chat_threads'].items())):
    if st.sidebar.button(name, key=str(thread_id)):
        selected_thread = thread_id

# ***************** Main UI ********************
st.title("Multi Utility Chatbot")

# loading the conversation history
for message in st.session_state['message_history']:
    if message['role'] == 'tool' or not message['content']:
        continue
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input("Ask about your document or use tools")

if user_input:

    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    tid = str(st.session_state['thread_id'])
    if st.session_state['chat_threads'][tid] == "New Chat":
        summary_state = model.invoke(
            f"Summarize in max 4 words: {user_input}"
        ).content
        st.session_state['chat_threads'][tid] = summary_state
        save_chat_name(tid, summary_state)

    CONFIG = {
        'configurable': {'thread_id': tid},
        "metadata": {"thread_id": tid},
        "run_name": "chat_turn"
    }

    # Use a mutable holder so the generator can set/modify it
    status_holder = {"box": None}

    def ai_only_stream():
        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode="messages",
        ):
            # Lazily create & update the SAME status container when any tool runs
            if isinstance(message_chunk, ToolMessage):
                tool_name = getattr(message_chunk, "name", "tool")
                if status_holder["box"] is None:
                    status_holder["box"] = st.status(
                        f"🔧 Using `{tool_name}` …", expanded=True
                    )
                else:
                    status_holder["box"].update(
                        label=f"🔧 Using `{tool_name}` …",
                        state="running",
                        expanded=True,
                    )

            # Stream ONLY assistant tokens
            if isinstance(message_chunk, AIMessage):
                yield message_chunk.content

    with st.chat_message("assistant"):
        ai_message = st.write_stream(ai_only_stream())

    # Finalize only if a tool was actually used
    if status_holder["box"] is not None:
        status_holder["box"].update(
            label="✅ Tool finished", state="complete", expanded=False
        )
    
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    doc_meta = thread_document_metadata(thread_key)
    if doc_meta:
        st.caption(
            f"Document indexed: {doc_meta.get('filename')} "
            f"(chunks: {doc_meta.get('chunks')}, pages: {doc_meta.get('documents')})"
        )

st.divider()

if selected_thread:
    st.session_state['thread_id'] = selected_thread
    messages = load_conversation(selected_thread)
    temp_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = 'user'
        elif isinstance(msg, AIMessage):
            role = 'assistant'
        else:
            continue
        temp_messages.append({'role': role, 'content': msg.content})
    st.session_state['message_history'] = temp_messages
    st.session_state['ingested_docs'].setdefault(str(selected_thread), {})
    st.rerun()
