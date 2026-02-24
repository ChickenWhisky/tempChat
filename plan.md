# Streaming AI Chatbot with Temporal — Phased Build plan

## System Goal
Build a streaming AI chatbot that:
- Streams LLM tokens to the frontend in real time
- Maintains durable conversation state using Temporal
- Cleanly separates streaming (non-durable) from workflow logic (durable)
- Is production-safe in design

---

## Phase 1 — Basic Streaming Without Temporal ✅ COMPLETED
**Goal**: Prove that token streaming works end-to-end.
- [x] Python backend (FastAPI + uv)
- [x] SSE endpoint with strict streaming JSON protocol mapping
- [x] React frontend using EventSource (`@microsoft/fetch-event-source`)
- [x] UI rendering streaming text
- [x] Containerized setup using Docker Compose

**Verification Checkpoint (Passed)**:
- Browser displays streaming tokens progressively.
- Explicit `start`, `token`, `end` events are handled.
- Stream closes cleanly.

---

## Phase 2 — Real LLM Streaming (No Temporal) ✅ COMPLETED
**Goal**: Replace fake token generator with real LLM.
- [] Integrate PydanticAI streaming agent
- [] Connect to local Ollama instance (OpenAI models interface)
- [] Stream structured tokens from agent to SSE
- [] UI refinements (Dark mode, auto-scaling, Shadcn layout integrations)

**Verification Checkpoint (Passed)**:
- Real LLM streams correctly.
- Errors produce correct error events.
- End events trigger completions reliably.

---

## Phase 3 — Introduce Temporal Without Streaming ⏳ PENDING
**Goal**: Add durable workflow logic without streaming.
**Implement**:
- [ ] Temporal Workflow maintaining message history
- [ ] Temporal Activity that calls LLM and returns full response (no streaming)
- [ ] FastAPI POST endpoint to start/signal workflow
- [ ] Store final response in workflow state

**Verification Checkpoint**:
- Conversations persist across worker restarts
- Workflow replay does not break
- Message history grows correctly
- Activity result stored durably

---

## Phase 4 — Combine Temporal + Streaming (Correctly) ⏳ PENDING
**Goal**: Reintroduce streaming while preserving determinism.
**Implement**:
- [ ] Streaming logic inside Activity
- [ ] Activity pushes structured events to in-memory queue
- [ ] SSE endpoint consumes queue
- [ ] Activity returns final accumulated result to Workflow
- [ ] Activity retry policy set to `maximum_attempts = 1`

**Verification Checkpoint**:
- Streaming works as before
- Workflow replay does not cause duplicate streaming
- Activity retries do not occur
- Final message stored durably
- Worker restart does not break workflow

---

## Phase 5 — Failure Handling Validation ⏳ PENDING
**Goal**: Ensure system behaves correctly under failures.
**Simulate**:
- [ ] Activity exception mid-stream
- [ ] Worker crash before end event
- [ ] SSE disconnect
- [ ] LLM timeout

**Expected Behavior / Verification**:
- `error` event emitted on failure
- No duplicate token streams
- Workflow records failure state
- User can retry safely
- No nondeterministic replay issues

---

## Phase 6 — Production Hardening ⏳ PENDING
**Goal**: Make system horizontally scalable and production-aware.
**Implement**:
- [ ] Replace in-memory queue with Redis Pub/Sub
- [ ] Add observability (structured logging, metrics)
- [ ] Add payload management (prevent exceeding Temporal payload limits)
- [ ] Offload large message histories to object storage (references in Workflow state)

**Verification Checkpoint**:
- System is horizontally scalable and production-aware.
