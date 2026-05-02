# CryptoPulse Demo Checklist

Use this checklist to record the final demo with the full no-mock stack:

```text
Frontend -> Chatbot REST -> real RAG(Milvus/BGE/BM25) + real AutoDL LoRA(vLLM)
```

## 1. Start Services

1. Start Milvus and confirm all containers are healthy:

   ```bash
   docker ps
   ```

2. Start or keep the AutoDL tunnel open:

   ```bash
   ssh -CNg -L 6006:127.0.0.1:6006 -p 49576 root@connect.westb.seetacloud.com
   ```

3. Verify AutoDL vLLM models:

   ```bash
   curl http://127.0.0.1:6006/v1/models \
     -H "Authorization: Bearer $LORA_REMOTE_API_KEY"
   ```

   Expected model ids:

   - `llama3.1-8b-instruct`
   - `ift-lora`
   - `sentiment-lora`

4. Start Chatbot full no-mock mode using the command in `README.md`.

5. Start Frontend:

   ```bash
   cd frontend
   VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
   ```

   The Settings page reflects the env loaded by this Vite process. Restart
   `npm run dev` after changing `VITE_USE_MOCK` or `VITE_API_BASE_URL`.

6. Run the script check before recording:

   ```bash
   python scripts/verify_full_no_mock_e2e.py
   ```

   Expected output includes:

   - `full no-mock e2e ok`
   - `rag_documents_indexed: 1961`
   - `rag_collection: cryptopulse_rag_hybrid_bge_m3_bm25`
   - non-empty `source_count`

## 2. Recording Script

1. Open `http://127.0.0.1:5173`.
2. Show the Dashboard page.
3. Point out:
   - `Frontend Mode: real-api`
   - `API Status: ok`
   - `lora: ok`
   - `rag: ok`
   - sentiment timeline and market tone mix charts
4. Click `30 Days` and confirm the dashboard refreshes without errors.
5. Open the Chat page.
6. Send:

   ```text
   Use recent crypto reports to explain the Bitcoin market outlook.
   ```

7. Show:
   - generated answer
   - sentiment label
   - source titles
   - source snippets
   - non-empty conversation id
8. Return to Dashboard and show the final system state.

## 3. Non-Blocking Gaps To Mention If Asked

- `social_media` corpus ingestion is intentionally skipped for this demo.
- RAG social refresh remains a documented future task.
- LoRA training artifacts are deployed on AutoDL; local repo verifies the inference interface and remote vLLM integration, not the full GPU training run.
- Generation-based faithfulness evaluation is not part of this demo; current RAG faithfulness is a local grounded-answer proxy.

## 4. Troubleshooting

- If Chatbot reports RAG unavailable, check Milvus and `MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25`.
- If Chatbot reports LoRA unavailable, re-check the AutoDL tunnel, `$LORA_REMOTE_API_KEY`, and `/v1/models`; `sentiment-lora` and `ift-lora` must both appear.
- If the first chat request is slow, send one warm-up message before recording.
- If Frontend shows old UI after edits, reload the browser tab.
- If Settings still shows the old mock value after changing env, restart the Vite dev server.
- Never paste or record the real API key.
