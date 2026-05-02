# CryptoPulse English Demo Recording Plan

Use this plan to record a 5-7 minute English demo of the full no-mock stack:

```text
Frontend -> Chatbot REST -> real RAG(Milvus/BGE/BM25) + real AutoDL LoRA(vLLM)
```

Do not demo unsupported features: file upload is removed, social media corpus
ingestion is not complete, and chat history is not backend-persistent after a
service restart.

## 1. Pre-Recording Setup

1. Confirm Milvus is healthy:

   ```bash
   docker ps
   ```

   Expected containers:

   - `milvus-standalone`
   - `milvus-minio`
   - `milvus-etcd`

2. Start or keep the AutoDL tunnel open:

   ```bash
   ssh -CNg -L 6006:127.0.0.1:6006 -p 49576 root@connect.westb.seetacloud.com
   ```

3. Verify AutoDL vLLM models without showing the real key on screen:

   ```bash
   curl http://127.0.0.1:6006/v1/models \
     -H "Authorization: Bearer $LORA_REMOTE_API_KEY"
   ```

   Expected model ids:

   - `llama3.1-8b-instruct`
   - `ift-lora`
   - `sentiment-lora`

4. Start Chatbot full no-mock mode from `chatbot/`:

   ```bash
   USE_MOCK=false RAG_USE_MOCK=false LLM_BACKEND=lora LORA_USE_MOCK=false \
   LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 \
   USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=false \
   MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 \
   EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 \
   RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base \
   BM25_INDEX_PATH=../rag/data/processed/bm25_index.json \
   HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
   RAG_SYSTEM_SITE_PACKAGES=/Users/kevinableyyyx/anaconda3/lib/python3.11/site-packages \
   .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000
   ```

5. Start Frontend from `frontend/`:

   ```bash
   VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8000 \
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

   The Settings page reflects the env loaded by this Vite process. Restart
   `npm run dev` after changing `VITE_USE_MOCK` or `VITE_API_BASE_URL`.

6. Run verification before recording:

   ```bash
   python scripts/verify_full_no_mock_e2e.py
   ```

   Expected output includes:

   - `full no-mock e2e ok`
   - `rag_documents_indexed: 1961`
   - `rag_collection: cryptopulse_rag_hybrid_bge_m3_bm25`
   - non-empty `source_count`

## 2. Recording Flow

1. Open `http://127.0.0.1:5173`.

2. Start on **Settings**.

   Say:

   > This is CryptoPulse running in real API mode. The frontend is connected
   > to the local Chatbot API, with mock mode disabled.

   Show:

   - `VITE_API_BASE_URL=http://127.0.0.1:8000`
   - `VITE_USE_MOCK=false`
   - `Frontend mode=real-api`
   - available endpoints

3. Move to **Dashboard**.

   Say:

   > The dashboard summarizes market sentiment and confirms the backend
   > provider health.

   Show:

   - `Frontend Mode: real-api`
   - `API Status: ok`
   - `lora: ok`
   - `rag: ok`
   - `ner: ok`
   - sentiment timeline chart
   - market tone mix chart
   - top topics

4. Click `30 Days`, then `90 Days`.

   Say:

   > Changing the time range refreshes the sentiment summary from the Chatbot API.

5. Move to **Chat**.

   Say:

   > The chat interface sends user questions to the Chatbot service, which
   > retrieves relevant documents from RAG and generates the answer using the
   > AutoDL LoRA model.

6. Click `New conversation` before the first recorded prompt if old local
   messages are present.

   Show:

   - welcome message
   - `Conversation ID: Not created`

7. Send prompt 1:

   ```text
   Use recent crypto reports to explain the Bitcoin market outlook.
   ```

   Show:

   - generated answer
   - `Sentiment: ...`
   - source titles
   - source snippets
   - non-empty `Conversation ID`

8. Send prompt 2 to demonstrate multi-turn context:

   ```text
   Based on that, what are the main risks investors should watch?
   ```

   Say:

   > The second response continues the same conversation using the existing
   > conversation ID.

9. Refresh the browser page.

   Say:

   > The frontend stores the current conversation locally, so the recording can
   > continue after a page refresh without losing the visible chat history.

   Show:

   - same Conversation ID
   - previous messages still visible

10. Click `New conversation`.

    Say:

    > A new conversation clears the local chat history and lets the backend
    > create a fresh conversation ID on the next message.

    Show:

    - welcome message
    - `Conversation ID: Not created`

11. Return to **Dashboard**.

    Say:

    > This completes the full no-mock demo: dashboard health, sentiment summary,
    > real RAG sources, real LoRA generation, and frontend conversation
    > persistence.

## 3. Recommended English Prompts

- `Use recent crypto reports to explain the Bitcoin market outlook.`
- `Based on that, what are the main risks investors should watch?`
- `What do the retrieved sources suggest about digital asset fund flows?`
- `Summarize the current crypto market sentiment in three bullet points.`

## 4. Notes To Avoid During Recording

- Do not show or say the real API key.
- Do not claim file upload is supported; the upload UI has been removed.
- Do not claim social media ingestion is complete.
- Do not claim chat history is backend-persistent after service restart; current
  demo persistence is browser local storage plus backend in-memory context during
  the running service process.

## 5. Troubleshooting

- If Chatbot reports RAG unavailable, check Milvus and
  `MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25`.
- If Chatbot reports LoRA unavailable, re-check the AutoDL tunnel,
  `$LORA_REMOTE_API_KEY`, and `/v1/models`; `sentiment-lora` and `ift-lora`
  must both appear.
- If the first chat request is slow, send one warm-up message before recording.
- If Frontend shows old UI after edits, reload the browser tab.
- If Settings still shows the old mock value after changing env, restart the
  Vite dev server.
- Never paste or record the real API key.
