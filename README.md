# CryptoPulse

CryptoPulse is a four-module cryptocurrency intelligence system for retrieval-augmented chat, market sentiment, and demo-ready frontend workflows.

## Architecture

```text
Browser
  -> frontend/ React + Vite UI
  -> chatbot/ FastAPI REST API
     -> rag/ Milvus + BAAI/bge-m3 + BM25 retrieval
     -> lora/ AutoDL vLLM LoRA inference
```

The stable cross-module contracts live in `docs/INTERFACES.md`. Root and module progress are tracked in `feature_list.json` files, `progress.md`, and `session-handoff.md`.

## Modules

| Module | Role | Main command |
|--------|------|--------------|
| `frontend/` | Chat, dashboard, and recording UI | `npm run dev` |
| `chatbot/` | REST orchestration for NER, RAG, and LoRA | `.venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000` |
| `rag/` | Corpus ingestion, hybrid retrieval, and context assembly | `.venv/bin/python -m unittest discover -s tests` |
| `lora/` | LoRA wrapper and AutoDL vLLM bridge | `.venv/bin/python -m pytest tests -q` |
| `shared/` | Backend dataclasses and enums | imported by provider modules |

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Local Milvus standalone on `127.0.0.1:19530`
- AutoDL SSH tunnel exposing vLLM at `http://127.0.0.1:6006/v1`
- Local model caches:
  - BGE-M3: `/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181`
  - BGE reranker: `/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base`

Do not install project packages into conda `base`. Use module-local virtual environments.

## Bootstrap

```bash
./init.sh

cd frontend && npm install

cd ../chatbot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cd ../rag
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

cd ../lora
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

For full no-mock Chatbot, the clean setup is to install RAG dependencies into `chatbot/.venv`:

```bash
cd /Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse
chatbot/.venv/bin/pip install -r rag/requirements.txt
```

If local network policy blocks that install, use the already-created `rag/.venv` as a read-only dependency bridge when starting Chatbot:

```bash
export RAG_SITE_PACKAGES=/Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse/rag/.venv/lib/python3.11/site-packages
export PYTHONPATH="$RAG_SITE_PACKAGES:$PYTHONPATH"
export RAG_SYSTEM_SITE_PACKAGES=/Users/kevinableyyyx/anaconda3/lib/python3.11/site-packages
```

## Milvus

Start Milvus standalone with the same version used by this project:

```bash
cd ~
wget https://github.com/milvus-io/milvus/releases/download/v2.6.14/milvus-standalone-docker-compose.yml -O docker-compose.yml
sudo docker compose up -d
docker ps
```

Expected ports:

- `19530`: Milvus gRPC
- `9091`: Milvus health/API
- `9000-9001`: MinIO

The current verified RAG collection is `cryptopulse_rag_hybrid_bge_m3_bm25`.

## AutoDL LoRA Tunnel

Open the SSH tunnel in a terminal and keep it running:

```bash
ssh -CNg -L 6006:127.0.0.1:6006 -p 49576 root@connect.westb.seetacloud.com
```

Set the key only in your local shell or `.env`; never commit it:

```bash
export LORA_REMOTE_API_KEY=your-local-key
curl http://127.0.0.1:6006/v1/models \
  -H "Authorization: Bearer $LORA_REMOTE_API_KEY"
```

The expected model ids are `llama3.1-8b-instruct`, `ift-lora`, and `sentiment-lora`.

## Full No-Mock Startup

Terminal 1, Chatbot with real RAG and real AutoDL LoRA:

```bash
cd /Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse/chatbot

export RAG_SITE_PACKAGES=/Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse/rag/.venv/lib/python3.11/site-packages
export PYTHONPATH="$RAG_SITE_PACKAGES:$PYTHONPATH"
export LORA_REMOTE_API_KEY=your-local-key

USE_MOCK=false \
RAG_USE_MOCK=false \
LLM_BACKEND=lora \
LORA_USE_MOCK=false \
LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 \
USE_MILVUS_NATIVE_HYBRID=true \
USE_CROSS_ENCODER_RERANKER=false \
MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 \
EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 \
RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base \
BM25_INDEX_PATH=../rag/data/processed/bm25_index.json \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
RAG_SYSTEM_SITE_PACKAGES=/Users/kevinableyyyx/anaconda3/lib/python3.11/site-packages \
.venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Terminal 2, Frontend against the real Chatbot API:

```bash
cd /Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse/frontend
VITE_USE_MOCK=false \
VITE_API_BASE_URL=http://127.0.0.1:8000 \
npm run dev -- --host 127.0.0.1 --port 5173
```

The Settings page reads the environment injected into the current Vite process.
If `VITE_USE_MOCK` or `VITE_API_BASE_URL` changes, stop and restart
`npm run dev`; a browser refresh alone will keep the old dev-server env.

Terminal 3, verification:

```bash
cd /Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse
python scripts/verify_full_no_mock_e2e.py
```

## Recording Checklist

Use `http://127.0.0.1:5173` for the video. The full checklist is in `docs/DEMO_CHECKLIST.md`.

1. Open the Dashboard and confirm health shows API/RAG/LoRA availability.
2. Open the Chat page.
3. Ask a query such as: `Use recent crypto reports to explain the Bitcoin market outlook.`
4. Show the answer, sentiment label, entities, and source snippets.
5. Return to Dashboard and show sentiment summary data.

Non-blocking demo gaps are documented in the checklist: social media ingestion,
RAG social refresh, local LoRA training evidence, and generation-based
Faithfulness are future work and are not required for the current recording.

## Verification Commands

```bash
python -m json.tool feature_list.json >/dev/null
python -m json.tool frontend/feature_list.json >/dev/null
python -m json.tool chatbot/feature_list.json >/dev/null
python -m json.tool rag/feature_list.json >/dev/null
python -m json.tool lora/feature_list.json >/dev/null

cd frontend && npm run build
cd ../chatbot && USE_MOCK=true .venv/bin/python -m pytest tests -q
cd ../rag && .venv/bin/python -m unittest discover -s tests
cd ../lora && .venv/bin/python -m pytest tests -q
cd .. && ./init.sh
git diff --check
```

## Troubleshooting

- `curl 127.0.0.1:6006/v1/models` fails: reopen the AutoDL SSH tunnel and confirm the remote vLLM service is still running.
- `/api/health` reports RAG unavailable: confirm Docker containers are healthy and `MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25`.
- Chatbot cannot import `sentence_transformers` or `pymilvus`: install `rag/requirements.txt` into `chatbot/.venv`, or export `PYTHONPATH` with `rag/.venv/lib/python3.11/site-packages`.
- RAG model loading is slow on first request: warm up with one `/api/chat` request before recording.
- Never commit `.env`, API keys, `node_modules`, virtual environments, Milvus data, or raw/processed corpus artifacts.
