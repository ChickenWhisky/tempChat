# Streaming AI Chatbot with Temporal — Phased Build plan

## System Goal
Build a streaming AI chatbot that:
- Streams LLM tokens to the frontend in real time
- Maintains durable conversation state using Temporal
- Cleanly separates streaming (non-durable) from workflow logic (durable)
- Is production-safe in design

---

## Phase 1 — Basic Streaming Without Temporal ✅ COMPLETED
**Goal**: Prove that token streaming works end-to-end 
- [x] Python backend (FastAPI)
- [x] React frontend using EventSource (`@microsoft/fetch-event-source`)
- [x] UI rendering streaming text
- [x] Containerized setup using Docker Compose

**Verification Checkpoint (Passed)**:
- Browser displays streaming tokens progressively.
- Explicit `start`, `token`, `end` events are handled.
- Stream closes cleanly.

---

## Phase 2 — Real LLM Streaming (No Temporal) ✅ COMPLETED
**Goal**: Replace fake token generator with real LLM & also because I havent built an App that utilizes LLM capabilities so I figured it would be better to try things without temporal and then move on to looking into integrating temporal.
- [x] Connect to local Ollama instance
- [x] Integrate PydanticAI streaming agent
- [x] Stream structured tokens from agent to SSE
- [x] UI refinements (Dark mode, auto-scaling, Shadcn layout integrations)

**Verification Checkpoint (Passed)**:
- Real LLM streams correctly.
- Errors produce correct error events.
- End events trigger completions reliably.

---

## Phase 3 — Introduce Temporal Without Streaming ✅ COMPLETED
**Goal**: Add durable workflow logic without streaming.
**Implement**:
- [x] Temporal Setup via Docker
- [x] Workflows, activities and workers established
- [x] FastAPI POST endpoint to start/signal workflow
- [x] Store final response in workflow state

**Verification Checkpoint (Passed)**:
- Conversations persist across worker restarts
- Workflow replay does not break
- Message history grows correctly
- Activity result stored durably

---

## Phase 4 — Combine Temporal + Streaming (Correctly) ✅ COMPLETED
**Goal**: Reintroduce streaming while preserving determinism.
**Implement**:
- [x] Streaming from activity to UI works
- [x] Agent pushes structured events to in-memory queue
- [x] SSE endpoint consumes queue
- [x] Long-lived Temporal chat workflows using Signal-With-Start for multi-turn conversations and refined streaming

**Verification Checkpoint (Passed)**:
- Streaming works as before
- Workflow replay does not cause duplicate streaming
- Final message stored durably
- Worker restart does not break workflow

---

## Phase 5 — Failure Handling Validation ✅ COMPLETED
**Goal**: Ensure system behaves correctly under failures.
**Simulate**:
- [x] Activity exception mid-stream
- [x] Worker crash before end event
- [x] SSE disconnect
- [x] LLM network conflict resolutions
- [x] Reconnection to same workflow in case service goes down and comes back up

**Expected Behavior / Verification**:
- `error` event emitted on failure
- Prevent duplicate cards from stream retries on tab switch
- Workflow records failure state
- User can retry safely
- No nondeterministic replay issues

---

## Phase 6 — Production Hardening ✅ COMPLETED
**Goal**: Make system horizontally scalable and production-aware for the MVP.
**Implement**:
- [x] Replace in-memory PubSub with Redis PubSub
- [x] Consolidate stream event types into a single `StreamEvent` and refine logging across the backend

---

## Phase 7 — Post-MVP: Multiple Conversations ✅ COMPLETED
**Goal**: Allow users to manage multiple independent chat sessions.
**Implement**:
- [x] Durable chat history retrieval via API endpoint and Temporal workflow query
- [x] Persistent conversational AI chat interface with streaming and history management
- [x] Sidebar for conversation history
- [x] "New Chat" button to generate new conversation sessions

---

## Phase 8 — Future Considerations (What I'd do with more time) ⏳ PENDING
**Goal**: Address scale, capabilities, and long-term durability trade-offs intentionally skipped during the MVP.
**Planned**:
- [ ] **External Database for Chat History**: Offload chat history from Temporal's durable state to an external transactional database (like PostgreSQL). Relying purely on Temporal state for UI reads is fine for an MVP but is an anti-pattern for long-term storage and high-frequency UI queries.
- [ ] **S3 Payload Offloading**: Implement payload offloading for Temporal to prevent large LLM responses and long conversation histories from hitting Temporal's blob size limits and degrading cluster performance.
- [ ] **Tool Calling/Function Calling**: Add PydanticAI tools for the agent so the chatbot can interact with external APIs or execute dynamic logic during the stream.
- [ ] **Multiple LLM Provider Support**: Expand beyond the hardcoded local Ollama endpoint to support multiple distinct LLM providers via a frontend selector.
- [ ] **Image Input (Multimodality)**: Add support for users to upload and send images alongside text prompts for multimodal LLM analysis.
- [ ] **Retrieval-Augmented Generation (RAG)**: Connect the Pydantic agent to a vector database to fetch relevant context on-the-fly, allowing the chatbot to answer questions based on specialized or proprietary documents.