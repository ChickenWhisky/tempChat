# Streaming AI Chatbot with Temporal — My Phased Build Plan

## System Goal
I set out to build a streaming AI chatbot with the following core objectives in mind:
- Stream LLM tokens directly to the frontend in real time for a snappy UX
- Maintain durable, long-lived conversation state using Temporal
- Cleanly separate the ephemeral streaming logic from the durable workflow logic
- Ensure the overall design was production-safe

---

## Phase 1 — Basic Streaming Without Temporal ✅ COMPLETED
**My Goal**: Before doing anything crazy, I needed to prove that token streaming worked end-to-end.
- [x] Spun up a Python backend (FastAPI)
- [x] Bootstrapped a React frontend using EventSource (`@microsoft/fetch-event-source`)
- [x] Got the UI rendering a fake stream of text
- [x] Containerized the whole setup using Docker Compose

**Verification Checkpoint (Passed)**:
- My browser started displaying streaming tokens progressively!
- I correctly handled explicit `start`, `token`, and `end` events.
- The stream closed cleanly without hanging connections.

---

## Phase 2 — Real LLM Streaming (No Temporal) ✅ COMPLETED
**My Goal**: I wanted to replace the fake token generator with a real LLM. Also, because I hadn't built an app that utilizes LLM capabilities from scratch before, I figured it would be better to try things out locally without Temporal first, and then move on to the heavier orchestration.
- [x] Connected the app to my local Ollama instance
- [x] Integrated a PydanticAI streaming agent
- [x] Got the agent streaming structured tokens straight to my SSE endpoint
- [x] Made some much-needed UI refinements (Dark mode, auto-scaling textareas, integrating Shadcn layout elements)

**Verification Checkpoint (Passed)**:
- Real LLM streams correctly without lag.
- Errors produce correct and caught error events in the UI.
- End events trigger completions reliably.

---

## Phase 3 — Introduce Temporal Without Streaming ✅ COMPLETED
**My Goal**: Now it was time for the fun part: adding durable workflow logic (without dealing with streaming complications just yet).
**What I Implemented**:
- [x] Set up Temporal locally via Docker Compose
- [x] Established my basic workflows, activities, and workers
- [x] Added a FastAPI POST endpoint to start and signal the workflow
- [x] Learned to store the final LLM response safely in the workflow state

**Verification Checkpoint (Passed)**:
- Conversations surprisingly persisted even across my worker restarts!
- Workflow replays did not break any logic.
- My message history grew correctly with each query.
- Activity results were stored durably as expected.

---

## Phase 4 — Combine Temporal + Streaming (Correctly) ✅ COMPLETED
**My Goal**: Reintroduce my shiny real-time streaming feature while preserving Temporal's strict determinism requirements.
**What I Implemented**:
- [x] Hooked up streaming from inside the Temporal activity right to the UI
- [x] Got my agent to push structured events to an in-memory queue
- [x] Adjusted my SSE endpoint to consume that queue
- [x] Built long-lived Temporal chat workflows using the `Signal-With-Start` pattern, enabling multi-turn conversations and refined continuous streaming

**Verification Checkpoint (Passed)**:
- Streaming works beautifully just like Phase 2!
- Verified that Temporal workflow replays *do not* cause duplicate, ghost tokens to start streaming to the user.
- The final message remains stored durably.
- Restarting my Temporal worker node explicitly does not break the active workflow.

---

## Phase 5 — Failure Handling Validation ✅ COMPLETED
**My Goal**: Make absolutely sure my system behaves correctly when things inevitably fail.
**What I Simulated**:
- [x] Induced an activity exception right in the middle of a stream
- [x] Crashed the worker pod right before the end event emitted
- [x] Disconnected the SSE client randomly
- [x] Simulated LLM network conflict resolutions
- [x] Tested reconnecting to the same exact workflow after simulating a total service outage

**Expected Behavior / Verification (All Passed)**:
- Caught `error` events emit straight to the UI on failure.
- Fixed a bug I found to prevent duplicate UI cards from popping up during stream retries when I switched browser tabs.
- Workflows explicitly logged their failure states.
- I can safely click retry on the frontend without the backend imploding.
- Successfully achieved zero nondeterministic replay errors in the Temporal logs!

---

## Phase 6 — Production Hardening ✅ COMPLETED
**My Goal**: Mature the system from an MVP architecture to something horizontally scalable and production-aware.
**What I Implemented**:
- [x] Replaced my local in-memory Python `asyncio.Queue` PubSub with a fully-fledged Redis PubSub architecture.
- [x] Cleaned up a ton of my events by consolidating the stream event types into a single `StreamEvent` model and refining my logging statements across the entire backend.

---

## Phase 7 — Post-MVP: Multiple Conversations ✅ COMPLETED
**My Goal**: Realized I needed to allow users to manage multiple independent chat sessions simultaneously, like actual ChatGPT.
**What I Implemented**:
- [x] Created durable chat history retrieval via a new API endpoint natively querying Temporal workflow state.
- [x] Built out a persistent conversational AI chat interface heavily focused on seamless streaming and history management.
- [x] Added a sleek sidebar for clicking around conversation history.
- [x] Added a "New Chat" button to kick off brand new session workflows seamlessly.

---

## Phase 8 — Future Considerations (What I'd do with more time) ⏳ PENDING
**My Goal**: Formally address the scale, capability, and long-term durability trade-offs I opted to intentionally skip during the MVP phases.
**What I plan to do next**:
- [ ] **External Database for Chat History**: Offload my chat history from Temporal's durable state straight into an external transactional database (like PostgreSQL). Relying purely on Temporal state for UI reads was super fast to build for an MVP, but it's an anti-pattern for long-term storage and high-frequency UI UI queries that I want to fix.
- [ ] **S3 Payload Offloading**: Implement payload offloading for Temporal. If someone pastes a massive code block eventually those LLM responses and deeply long conversation histories will hit Temporal's blob size limits and severely degrade my cluster performance.
- [ ] **Tool Calling/Function Calling**: Add native PydanticAI tools for my agent so the chatbot can interact with external APIs or execute dynamic Python logic *during* the stream.
- [ ] **Multiple LLM Provider Support**: Expand beyond the hardcoded local Ollama endpoint to build a frontend selector to seamlessly bounce queries against OpenAI, Anthropic, or Gemini.
- [ ] **Image Input (Multimodality)**: Add drag-and-drop support so users can upload and send images directly alongside text prompts for multimodal LLM analysis.
- [ ] **Retrieval-Augmented Generation (RAG)**: Connect my Pydantic agent to a local vector database to fetch relevant context on-the-fly, allowing the chatbot to answer questions based on my specialized or proprietary local documents.