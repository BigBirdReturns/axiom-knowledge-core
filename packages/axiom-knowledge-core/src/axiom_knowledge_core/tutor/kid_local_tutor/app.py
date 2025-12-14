"""
app.py
======

This Streamlit application provides a simple graphical interface for
interacting with the local tutor.  Parents and older students can type
questions to the AI, view the retrieved context passages, and inspect
conversation logs.  The app does not expose any network API; it runs solely
on your local machine.

Launch the app with:

```
streamlit run kid_local_tutor/app.py
```

The first time you run the app it will load the vector store and language
model from disk.  Make sure you have ingested your curriculum into
`data/embeddings` and downloaded the model weights into `models/llm`.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from .vector_store import VectorStore
from .rehydrate import TutorQnA
from .orchestrator import Orchestrator
from .memory import MSONMemory


# Default configuration (change these to match your setup)
DEFAULT_DB_DIR = os.getenv("TUTOR_DB_DIR", "data/embeddings")
DEFAULT_COLLECTION = os.getenv("TUTOR_COLLECTION", "corpus")
DEFAULT_MODEL = os.getenv("TUTOR_MODEL", "models/llm/tinyllama.gguf")
DEFAULT_MEMORY_FILE = os.getenv("TUTOR_MEMORY", "data/memory.json")


@st.cache_resource(show_spinner=True)
def get_services() -> tuple[Orchestrator, MSONMemory]:
    """Initialise and cache the vector store, QnA pipeline, orchestrator and memory.

    Returns
    -------
    tuple
        (orchestrator, memory) ready to use in the UI.
    """
    # Create vector store
    vs = VectorStore(DEFAULT_DB_DIR, DEFAULT_COLLECTION)
    # Create Q&A pipeline
    qna = TutorQnA(vector_store=vs, llm_path=DEFAULT_MODEL)
    # Create orchestrator with a single agent
    orch = Orchestrator([qna])
    # Load memory
    mem = MSONMemory(DEFAULT_MEMORY_FILE)
    return orch, mem


def main() -> None:
    st.set_page_config(page_title="Local AI Tutor", page_icon="👩‍🏫")
    st.title("📚 Local AI Tutor")
    st.markdown(
        "This tool lets you ask questions of your offline tutor, view sources, and "
        "inspect your learning history.  All data stays on your device."
    )
    # Load services
    orch, mem = get_services()

    # Sidebar controls
    st.sidebar.header("Settings")
    mode = st.sidebar.radio("Mode", ["Q&A", "Memory summary"])
    if mode == "Q&A":
        with st.form("question_form"):
            question = st.text_area("Enter your question", "", height=100)
            submitted = st.form_submit_button("Ask")
        if submitted and question.strip():
            with st.spinner("Thinking..."):
                result = orch.answer(question.strip())
            if result["error"]:
                st.error(result["answer"])
            else:
                st.markdown("### Answer")
                st.write(result["answer"])
                st.markdown("### Context")
                for idx, res in enumerate(result["context"], start=1):
                    st.markdown(f"**{idx}.** *(From {res.metadata.get('source', 'unknown')})*\n\n{res.document}")
    else:  # Memory summary
        st.markdown("### Memory Summary")
        summary = mem.dump_summary()
        st.write(summary)
        st.markdown("### Browse Reflective Log")
        # Show last 10 reflective entries
        reflective_items = list(mem.search("", category="reflective"))
        if reflective_items:
            for item in reversed(reflective_items[-10:]):
                st.markdown(f"- *{item.metadata.get('timestamp', '')}:* {item.content}")
        else:
            st.write("No reflective entries yet.")


if __name__ == "__main__":
    main()