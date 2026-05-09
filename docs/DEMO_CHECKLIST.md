# CryptoPulse English Presentation and Demo Script

Use this plan to record a 15-20 minute English presentation video for the PLP
Practice Module deliverable. The video should include slides plus a live system
demo.

Briefing alignment:

- Demonstrate a language processing system for a real-world business problem.
- Show at least two text mining tasks.
- Show sentiment mining or a conversational UI.
- Show model building with a self-built deep learning component or fine-tuned
  pretrained model.
- Mention datasets, solution approach, test results, conclusions, references,
  individual contribution, and GenAI/LLM usage.

Do not claim unsupported features: file upload is not exposed in the frontend,
social media ingestion is not complete, and chat history is not backend
persistent after a service restart.

## 1. Target Timing

| Segment | Time | Goal |
| --- | ---: | --- |
| Opening and problem | 1.5 min | Explain why crypto research needs language processing |
| Dataset and scope | 2 min | Describe collected reports and exclusions |
| PLP skills mapping | 2 min | Map the project to the four course modules |
| Architecture and methods | 4 min | Explain Frontend, Chatbot, RAG, LoRA, and Milvus |
| Testing and results | 2 min | Show evidence that the system runs end to end |
| Live demo | 6-7 min | Show Settings, Dashboard, Chat, sources, persistence |
| Conclusion and limitations | 1.5 min | Summarize value, risks, and next steps |

Target total: 17-18 minutes.

## 2. Pre-Recording Setup

Run these checks before starting the recording. Do not show the real API key on
screen.

1. Confirm Milvus is healthy:

   ```bash
   docker ps
   ```

   Expected containers:

   - `milvus-standalone`
   - `milvus-minio`
   - `milvus-etcd`

2. Keep the AutoDL tunnel open:

   ```bash
   ssh -CNg -L 6006:127.0.0.1:6006 -p 49576 root@connect.westb.seetacloud.com
   ```

3. Verify AutoDL vLLM models using the environment variable, not the literal key:

   ```bash
   export LORA_REMOTE_API_KEY=your-local-key
   curl http://127.0.0.1:6006/v1/models \
     -H "Authorization: Bearer $LORA_REMOTE_API_KEY"
   ```

   Expected model ids:

   - `llama3.1-8b-instruct`
   - `ift-lora`
   - `sentiment-lora`

4. Start Chatbot full no-mock mode from `chatbot/`:

   ```bash
   export RAG_SITE_PACKAGES=/path/to/CryptoPulse/rag/.venv/lib/python3.11/site-packages
   export PYTHONPATH="$RAG_SITE_PACKAGES:$PYTHONPATH"
   export RAG_SYSTEM_SITE_PACKAGES=/path/to/python3.11/site-packages

   USE_MOCK=false RAG_USE_MOCK=false LLM_BACKEND=lora LORA_USE_MOCK=false \
   NER_BACKEND=lora \
   LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 \
   LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY \
   USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=false \
   MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 \
   EMBEDDING_MODEL_NAME=/path/to/bge-m3-snapshot \
   RERANK_MODEL_NAME=/path/to/bge-reranker-base \
   BM25_INDEX_PATH=../rag/data/processed/bm25_index.json \
   HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
   RAG_SYSTEM_SITE_PACKAGES=/path/to/python3.11/site-packages \
   .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000
   ```

5. Start Frontend from `frontend/`:

   ```bash
   VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8000 \
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

6. Run full-stack verification before recording:

   ```bash
   python scripts/verify_full_no_mock_e2e.py
   ```

   Expected output includes:

   - `full no-mock e2e ok`
   - `rag_documents_indexed: 1961`
   - `rag_collection: cryptopulse_rag_hybrid_bge_m3_bm25`
   - non-empty `source_count`

7. Browser preparation:

   - Open `http://127.0.0.1:5173`.
   - Use English narration only.
   - Clear old chat state with `New conversation` if needed.
   - Hide terminals that expose environment variables or API keys.

## 3. Slide Script

Use these as slide titles and narration notes. Keep each slide concise.

### Slide 1: Project Title

Title: `CryptoPulse: Retrieval-Augmented Crypto Market Sentiment Assistant`

Say:

> This project is CryptoPulse, a language processing system for crypto market
> research. It combines document retrieval, sentiment analysis, information
> extraction, and a conversational interface to help users understand market
> outlook and risk from crypto research reports.

Show:

- Team member names.
- Course: Graduate Certificate in Practical Language Processing.
- Practice Module submission.

### Slide 2: Business Problem

Say:

> Crypto market information is fragmented across long research reports,
> regulatory documents, market updates, and digital asset fund flow reports.
> Analysts and investors need to quickly answer questions such as market
> direction, key risks, fund flow trends, and regulatory themes. Manually
> reading all documents is slow and inconsistent.

Show:

- Problem: too many long documents.
- Users: analysts, students, retail research users, investment teams.
- Decision support need: concise answer plus traceable evidence.

### Slide 3: Project Objective

Say:

> Our objective is to build and test a language processing system that turns
> crypto text data into actionable market insight. The system should answer
> natural language questions, retrieve supporting sources, estimate sentiment,
> identify key topics, and present a dashboard suitable for demo and analysis.

Show:

- Natural language Q&A.
- Sentiment analysis.
- Topic/entity extraction.
- Source-grounded answers.
- Dashboard summary.

### Slide 4: Dataset and Scope

Say:

> The corpus is self-collected from public crypto market reports, regulatory
> documents, protocol papers, and digital asset research PDFs. We processed the
> documents into chunks and indexed them into Milvus. In the current demo,
> social media ingestion is intentionally excluded, so we do not claim social
> media coverage as completed.

Show:

- Public PDFs and reports.
- Regulatory and compliance documents.
- DeFi and protocol papers.
- Processed RAG collection: `cryptopulse_rag_hybrid_bge_m3_bm25`.
- Indexed document evidence: `1961` chunks/documents from the verification run.

### Slide 5: PLP Skills Coverage

Say:

> CryptoPulse demonstrates skills from all four PLP modules. For text
> analytics, it preprocesses documents and retrieves relevant chunks. For new
> media and sentiment mining, it classifies market sentiment and extracts
> topics. For machine learning, it uses BGE-M3 embeddings and LoRA-adapted LLM
> inference. For conversational UI, it provides a text-based multi-turn
> assistant with source evidence.

Show:

- Text Analytics: preprocessing, chunking, retrieval.
- Sentiment Mining: bullish, bearish, neutral sentiment.
- Machine Learning: BGE-M3, BM25 hybrid retrieval, LoRA models.
- Conversational UI: chat, conversation id, multi-turn context.

### Slide 6: System Architecture

Say:

> The frontend is a Vite React application. It calls the Chatbot REST API. The
> Chatbot coordinates entity extraction, sentiment, retrieval, and generation.
> RAG uses Milvus with BGE-M3 dense embeddings and BM25 sparse retrieval. LoRA
> generation runs on an AutoDL vLLM service with OpenAI-compatible endpoints.

Show:

```text
Frontend -> Chatbot REST -> RAG(Milvus + BGE-M3 + BM25) -> Sources
                         -> AutoDL LoRA(vLLM) -> Answer + Sentiment
```

Mention:

- `GET /api/health`
- `GET /api/sentiment/summary`
- `POST /api/chat`

### Slide 7: Text Mining Tasks

Say:

> The system performs multiple text mining tasks. First, it performs retrieval
> and ranking over document chunks. Second, it performs sentiment classification.
> Third, it extracts entities and topics for the chat response and dashboard.
> Fourth, it performs text generation for the final user-facing answer.

Show:

- Information retrieval and ranking.
- Sentiment classification.
- Entity/topic extraction.
- Text generation and summarization.

### Slide 8: Model Building and GenAI Usage

Say:

> The project uses pretrained models, but also includes task-specific LoRA
> adapters deployed through vLLM. The sentiment adapter returns structured
> bullish, bearish, or neutral sentiment. The instruction-following adapter
> generates answers. We also used GenAI tools during development for coding
> assistance, debugging, and documentation support, while the final system logic
> and tests were verified locally.

Show:

- `sentiment-lora`.
- `ift-lora`.
- vLLM OpenAI-compatible `/v1/chat/completions`.
- GenAI disclosure: development assistance, not a replacement for testing.

Pros and cons to say:

> The advantage of LLMs is flexible reasoning and fluent summarization. The
> risk is hallucination, so CryptoPulse uses RAG source snippets and health
> checks to keep answers grounded and inspectable.

### Slide 9: Testing and Evidence

Say:

> We verified the system through module tests and a full no-mock end-to-end
> script. The most important evidence is that the frontend can call the Chatbot
> API, the Chatbot can reach real RAG and real AutoDL LoRA, and the chat response
> returns non-empty sources.

Show:

- `python scripts/verify_full_no_mock_e2e.py`.
- Expected: `full no-mock e2e ok`.
- RAG collection: `cryptopulse_rag_hybrid_bge_m3_bm25`.
- Source count greater than zero.
- Frontend build and module tests can be mentioned if already run.

### Slide 10: Limitations and Future Work

Say:

> The current version is suitable for a controlled local demo. The main
> limitations are that social media ingestion is not completed, chat history is
> stored in browser local storage and backend memory rather than a database, and
> real-time streaming can be added later. Future work includes persistent
> conversation storage, social media corpus refresh, better evaluation metrics,
> and production authentication.

Show:

- No social media claim.
- No backend-persistent chat after restart.
- Future: SSE/WebSocket streaming, persistent DB, social corpus, production auth.

### Slide 11: Individual Contributions

Say:

> The final report will include individual contribution details. In the video,
> briefly summarize responsibility areas: data and RAG, chatbot and API,
> LoRA/modeling, and frontend/demo integration.

Fill in with real names:

- Member 1: data preparation and RAG.
- Member 2: chatbot API and integration.
- Member 3: LoRA modeling and evaluation.
- Member 4, if applicable: frontend and demo documentation.

## 4. Live Demo Script

Keep the live demo around 6-7 minutes. Speak slowly and let each screen stay
visible for a few seconds.

### Step 1: Open Settings

Action:

- Open `http://127.0.0.1:5173`.
- Click `Settings`.

Say:

> I will now switch from slides to the live system. This is the frontend running
> in real API mode. It is connected to the local Chatbot API, and mock mode is
> disabled.

Show:

- `VITE_API_BASE_URL=http://127.0.0.1:8000`
- `VITE_USE_MOCK=false`
- `Frontend mode=real-api`
- Available endpoints.

### Step 2: Open Dashboard

Action:

- Click `Dashboard`.

Say:

> The dashboard summarizes market sentiment and also shows backend health. Here
> we can confirm that the frontend is using the real API, and the backend reports
> LoRA, RAG, and NER as available.

Show:

- `Frontend Mode: real-api`
- `API Status: ok`
- `lora: ok`
- `rag: ok`
- `ner: ok`
- Sentiment timeline chart.
- Market tone mix chart.
- Top topics.

### Step 3: Change Dashboard Time Range

Action:

- Click `30 Days`.
- Wait two seconds.
- Click `90 Days`.

Say:

> Changing the time range refreshes the sentiment summary from the Chatbot API.
> The dashboard is not a static screenshot; it is calling the backend endpoint.

### Step 4: Open Chat and Start a New Conversation

Action:

- Click `Chat`.
- Click `New conversation` if old messages exist.

Say:

> The chat interface is the conversational UI. A new conversation starts without
> an id. The backend creates the conversation id after the first successful
> request.

Show:

- `Conversation ID: Not created`.
- Welcome message.
- Text input fixed at the bottom.

### Step 5: Ask First Question

Action:

Send:

```text
Use recent crypto reports to explain the Bitcoin market outlook.
```

Say while it loads:

> This request goes through the Chatbot API. The backend retrieves relevant
> document chunks from Milvus, sends context to the LoRA generation service, and
> returns an answer with sentiment and source snippets.

After response:

Show:

- Generated answer.
- `Sentiment: ...`.
- Non-empty source titles.
- Source snippets.
- Non-empty conversation id.

Say:

> The answer is not just generated text. It includes traceable sources from the
> RAG collection, so the user can inspect why the answer was produced.

### Step 6: Ask Follow-Up Question

Action:

Send:

```text
Based on that, what are the main risks investors should watch?
```

Say:

> This second question demonstrates multi-turn usage. The frontend sends the
> existing conversation id, so the backend can continue the conversation instead
> of treating it as a completely separate request.

After response:

Show:

- Same conversation id.
- Second assistant response.
- Sentiment.
- New or relevant source snippets.

### Step 7: Refresh Persistence Check

Action:

- Refresh the page.

Say:

> The frontend stores the current conversation locally in the browser. After a
> page refresh, the visible conversation id and message history remain available.
> This is local browser persistence, not a database-backed history after backend
> restart.

Show:

- Same conversation id.
- Previous messages still visible.

### Step 8: New Conversation Reset

Action:

- Click `New conversation`.

Say:

> Starting a new conversation clears the local chat state. The next message will
> let the backend create a new conversation id.

Show:

- Welcome message.
- `Conversation ID: Not created`.

### Step 9: Return to Dashboard

Action:

- Click `Dashboard`.

Say:

> This completes the live demo. We have shown the real backend mode, dashboard
> health, sentiment summary, real RAG sources, real LoRA generation, and
> frontend conversation persistence.

## 5. Recommended Demo Prompts

Use these prompts only in English:

- `Use recent crypto reports to explain the Bitcoin market outlook.`
- `Based on that, what are the main risks investors should watch?`
- `What do the retrieved sources suggest about digital asset fund flows?`
- `Summarize the current crypto market sentiment in three bullet points.`

## 6. Closing Script

Say:

> In conclusion, CryptoPulse demonstrates a complete language processing
> application for crypto market intelligence. It uses text analytics for
> document processing and retrieval, sentiment mining for market tone,
> machine-learning models for embeddings and LoRA-based generation, and a
> conversational UI for user interaction. The system is verified in a full
> no-mock local setup, while the remaining work is mainly production hardening:
> persistent history, streaming output, social media ingestion, and stronger
> quantitative evaluation.

## 7. Recording Rules

- Do not show or say the real API key.
- Do not open `chatbot/.env` during recording.
- Do not claim file upload is supported.
- Do not claim social media ingestion is complete.
- Do not claim chat history survives backend restart.
- If a model response contains an awkward phrase, explain that the source
  grounding and traceable snippets are the main demo evidence.
- Keep terminal windows hidden unless showing non-sensitive verification output.

## 8. Troubleshooting

- If Chatbot reports RAG unavailable, check Milvus and
  `MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25`.
- If Chatbot reports LoRA unavailable, re-check the AutoDL tunnel,
  `$LORA_REMOTE_API_KEY`, and `/v1/models`; `sentiment-lora` and `ift-lora`
  must both appear.
- If the first chat request is slow, send one warm-up message before recording.
- If Frontend shows old UI after edits, reload the browser tab.
- If Settings shows old mock values after changing env, restart the Vite dev
  server.
- If browser refresh does not keep chat messages, check local storage keys:
  `cryptopulse.chat.conversation_id` and `cryptopulse.chat.messages`.
