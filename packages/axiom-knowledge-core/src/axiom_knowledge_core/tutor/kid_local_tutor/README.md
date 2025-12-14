# Kid‑Safe Local AI Tutor

This project implements a **privacy‑first, offline educational assistant** for K–12 learners.  The goal is to provide a friendly voice‑driven tutor that runs entirely on inexpensive single‑board computers (e.g. Raspberry Pi 5 or NVIDIA Jetson Orin Nano) without sending any data to the cloud.  It teaches core subjects through interactive dialogue, adapts to a child’s pace, and logs its behaviour for parental review.

## Features

- **Offline operation** – All speech recognition, language generation, and text‑to‑speech run locally.  An internet connection is only needed for optional updates or backing up the knowledge corpus.
- **Guided lessons & Q&A** – The tutor can explain topics, quiz the learner, provide hints and break complex tasks into smaller chunks.  It can also answer typed questions with cited sources using a retrieval‑augmented generation (RAG) pipeline.
- **Safe and transparent** – A multi‑layer safety filter removes profanity or adult content before it reaches the user.  Every interaction is journaled in an encrypted log along with a reflective memory explaining why the AI responded the way it did.
- **Customisable curriculum** – The immutable base knowledge is built from open‑source textbooks and documents in `data/docs/`.  Parents can add or remove material to suit their educational philosophy without any vendor lock‑in.
- **Modular architecture** – Each component (speech‑to‑text, embeddings, vector store, LLM, safety filter, memory) lives in its own module.  You can swap implementations without touching the rest of the stack.

- **Multilingual capabilities** – The tutor can operate in multiple languages.
  A lightweight language detector identifies the child’s language and the system
  will translate questions into the default working language (English by default)
  before querying the LLM.  Answers are then translated back for the learner.
  Parents can download additional Piper voices for the desired languages and
  optional Argos Translate packages to enable fully offline translation.
- **Extendable swarm orchestration** – The code includes scaffolding for a multi‑agent system where specialised agents collaborate on complex tasks under an orchestrator.  In the MVP the orchestrator simply calls the Q&A pipeline, but it can be expanded later.

## Hardware requirements

The system is intended to run on cheap, low‑power hardware.  Two suggested configurations are:

| Platform | Suggested model | Approx. cost | Notes |
|---------|----------------|--------------|------|
| **Raspberry Pi 5** (8 GB) | Use TinyLlama (~1.1B parameters) + Whisper Tiny; run everything on CPU | ~$200 | Real‑time audio transcription and 1.3 tokens/s generation.  Good entry‑level option. |
| **NVIDIA Jetson Orin Nano** (8 GB) | Use Mistral or LLaMA2 7B with CUDA offload; Whisper Base; optional NPU | ~$250 | Allows larger models with 3–4 tokens/s generation.  Ideal for more advanced use cases. |

**Peripherals**: a USB microphone, a small speaker, and a microSD card (32 GB+) are required.  For real‑time audio, set the microphone to record at 16 kHz mono.

## Installation

The following assumes a fresh install of Raspberry Pi OS 64‑bit or JetPack.  Replace any commands prefixed with `$` as appropriate for your system.

1. **Install system dependencies** – On Debian/Ubuntu run:

   ```bash
   sudo apt update && sudo apt install -y build‑essential cmake git python3 python3‑venv ffmpeg
   ```

   These packages provide compilers and audio utilities.  If using a Jetson, CUDA drivers are included with JetPack.

2. **Create a Python environment** – Inside the project directory run:

   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   The `requirements.txt` lists all Python packages used by the system (e.g. `whispercpp`, `llama‑cpp‑python`, `piper‑tts`, `chromadb`, `sentence‑transformers`, `streamlit`).  Some packages may compile native code; be patient on slower devices.

If you plan to use the multilingual features, install the optional language
packages:

```bash
pip install langdetect
# For offline translation (optional):
pip install argostranslate
```

After installing `argostranslate`, you must download translation models for
each language pair you want to support.  Use the CLI:

```bash
argospm update            # refresh model list
argospm install es_en     # install Spanish↔English model (example)
```

Repeat the `install` step for any other language pairs (e.g. `fr_en` for
French).  The tutor will automatically detect the language and translate
questions and answers using these packages.  Without translation models the
system will still work but will respond in the default language.

3. **Download models** – Place speech models and LLM weights in `models/`:

   * **Whisper** – Download a Whisper model (e.g. `tiny.en.ggml.bin`) from [ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp) and put it in `models/stt/`.
   * **Piper voice** – Download a Piper voice model (e.g. `en_US-amy-medium.onnx`) from the [Rhasspy Piper releases](https://github.com/rhasspy/piper/releases) and put it in `models/voices/`.
   * **LLM** – Download a quantised `.gguf` model (e.g. TinyLlama-1.1B-Q4.gguf) from HuggingFace and place it in `models/llm/`.  Larger models require more RAM and GPU.
   * **Embedding model** – `sentence-transformers` will automatically download `all-MiniLM-L6-v2` on first use.  To run fully offline, download and extract it into the default cache (`~/.cache/sentence_transformers/`).

4. **Prepare the knowledge corpus** – Put educational documents (PDFs or plain text) into `data/docs/`.  Then run the ingestion script to build the vector store:

   ```bash
   python -m axiom_knowledge_core.tutor.kid_local_tutor.ingest --docs data/docs --db data/embeddings --name corpus
   ```

   This will split each document into chunks, embed them, and save them into a local ChromaDB database at `data/embeddings`.

5. **Start the tutor** – Launch the parent dashboard and voice tutor:

   ```bash
   # Start the Streamlit app in one terminal
   streamlit run axiom_knowledge_core/tutor/kid_local_tutor/app.py

   # In another terminal, start the voice tutor loop
   python -m axiom_knowledge_core.tutor.kid_local_tutor.tutor_loop
   ```

   The Streamlit interface (usually at `http://localhost:8501`) lets you ask typed questions, view logs, and adjust settings.  The tutor loop listens to your microphone and speaks responses.

## Code structure

```
kid_local_tutor/
├── README.md            # This file
├── requirements.txt     # Python dependencies
├── data/                # Educational documents and embedding DB
│   ├── docs/            # Source documents (PDFs or text)
│   └── embeddings/      # Generated vector store (created by ingest)
├── models/              # Model weights (download yourself)
│   ├── llm/
│   ├── stt/
│   └── voices/
├── memory.py            # MSON memory abstractions
├── vector_store.py      # Wrapper over ChromaDB
├── utils.py             # Common helper functions
├── ingest.py            # Document ingestion script
├── rehydrate.py         # Retrieval‑augmented Q&A pipeline
├── safety.py            # Content filtering and moderation
├── tutor_loop.py        # Voice tutor loop
├── orchestrator.py      # Swarm orchestration and agent coordination
├── app.py               # Streamlit dashboard for parents and Q&A
└── __init__.py          # Makes this directory a Python package
```

## Limitations and next steps

This MVP demonstrates the architecture and provides working code skeletons.  It uses simple safety filters and heuristics for summarisation and keyword extraction.  Real deployments should:

* Fine‑tune the base LLM on age‑appropriate data to improve the tutor persona.
* Expand the safety filter using a lightweight classifier (e.g. Granite Guardian) for nuanced content moderation.
* Implement LoRA‑based persona adapters to adjust tone by grade level or subject.
* Build out multi‑agent orchestration for complex reasoning tasks and include semantic drift detection.

Feel free to experiment, customise and improve this codebase.  The modular design makes it easy to swap components or add new features.