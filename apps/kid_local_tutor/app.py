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
from .compiled_store import CompiledStore


# Default configuration (change these to match your setup)
DEFAULT_DB_DIR = os.getenv("TUTOR_DB_DIR", "data/embeddings")
DEFAULT_COLLECTION = os.getenv("TUTOR_COLLECTION", "corpus")
DEFAULT_MODEL = os.getenv("TUTOR_MODEL", "models/llm/tinyllama.gguf")
DEFAULT_MEMORY_FILE = os.getenv("TUTOR_MEMORY", "data/memory.json")
DEFAULT_COMPILED_DIR = os.getenv("TUTOR_COMPILED_DIR", "")
DEFAULT_VECTOR_MODE = os.getenv("TUTOR_VECTOR_MODE", "0").strip()


@st.cache_resource(show_spinner=True)
def get_services() -> tuple[Orchestrator, MSONMemory]:
    """Initialise and cache the vector store, QnA pipeline, orchestrator and memory.

    Returns
    -------
    tuple
        (orchestrator, memory) ready to use in the UI.
    """
    # Choose retrieval backend.
    # Correctness-first default: compiled artifacts are authoritative.
    #
    # Rules:
    # - Compiled mode is required for normal use.
    # - Uncompiled mode is development-only and requires explicit opt-in.
    compiled_dir = (DEFAULT_COMPILED_DIR.strip() or "compiled")
    compiled_path = Path(compiled_dir)
    has_compiled = compiled_path.exists() and compiled_path.is_dir() and any(compiled_path.iterdir())

    allow_uncompiled = os.getenv("ALLOW_UNCOMPILED_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
    vector_mode = os.getenv("TUTOR_VECTOR_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}

    if has_compiled:
        store = CompiledStore(str(compiled_path))
    else:
        if not allow_uncompiled:
            raise RuntimeError(
                "Refusing to run without compiled knowledge artifacts. "
                "This system is correctness-first and requires a compiled corpus. "
                "Run: ak compile --sources sources --out compiled. "
                "Development-only override: ALLOW_UNCOMPILED_MODE=1 TUTOR_VECTOR_MODE=1."
            )
        if not vector_mode:
            raise RuntimeError(
                "Uncompiled mode requested, but vector mode is not enabled. "
                "Set TUTOR_VECTOR_MODE=1 (development only)."
            )
        st.session_state["uncompiled_mode"] = True
        store = VectorStore(DEFAULT_DB_DIR, DEFAULT_COLLECTION)

    # Create Q&A pipeline
    qna = TutorQnA(vector_store=store, llm_path=DEFAULT_MODEL)
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
    if st.session_state.get("uncompiled_mode"):
        st.warning(
            "Running in uncompiled mode (development only). "
            "Answers may be incomplete or unverifiable. "
            "Compile a corpus and restart for correctness-first operation."
        )


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
