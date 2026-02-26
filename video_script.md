# Auto Heal AI: Project Walkthrough & Resilience Demo Script

This script provides a structured guide for a video demonstration of the project. It covers the technical architecture and showcases the system's resilience using Temporal and Redis.

---

## Part 1: Architecture Overview
**Visuals:** Open the project root in your IDE.

**Script:**
"Welcome to the Auto Heal AI demonstration. This project is a production-grade chatbot designed for extreme resilience. Before we break things, let's look at the core components:

1.  **[Frontend](file:///home/thomasm/Desktop/autoHealAi/frontend):** A React application using Vite and Tailwind CSS. It communicates with the backend via REST and Server-Sent Events (SSE).
2.  **[Backend](file:///home/thomasm/Desktop/autoHealAi/backend/src/main.py):** A FastAPI server that also hosts our **Temporal Worker**. This is the 'brain' of the operation.
3.  **[Temporal Workflow](file:///home/thomasm/Desktop/autoHealAi/backend/src/workflows/chat.py):** Instead of standard request-response, every conversation is a durable Temporal Workflow. This means if the server restarts, the conversation doesn't die.
4.  **[Redis](file:///home/thomasm/Desktop/autoHealAi/docker-compose.yml#L42):** Used for Pub/Sub. When the LLM starts 'typing', Temporal signals the backend, which publishes to Redis, which then streams to your browser via SSE.
5.  **[PostgreSQL](file:///home/thomasm/Desktop/autoHealAi/docker-compose.yml#L49):** The source of truth for Temporal, storing every event and state transition."

---

## Part 2: Demo - Redis Failure (Streaming Interruption)
**Goal:** Show that while streaming depends on Redis, the core logic is durable.

**Steps:**
1.  **Normal State:** Send a message in the UI. Point out the smooth streaming text.
2.  **The Crash:** Run `docker compose stop redis`.
3.  **The Impact:** Send another message.
    - *Observation:* The message will eventually appear in the history, but the "real-time" streaming animation is gone.
4.  **The Explanation:** 
    "Even though our streaming layer (Redis) is down, the **Temporal Workflow** is still running. It receives the signal, talks to the LLM, and saves the history to Postgres. When you refresh the page, the history is fetched directly from the durable Workflow, so no data was actually lost."
5.  **Recovery:** Run `docker compose start redis`.

---

## Part 3: Demo - Backend Failure (The "Auto-Heal")
**Goal:** Show Temporal's ability to resume an interrupted long-running task.

**Steps:**
1.  **The Setup:** Ask the AI a long-form question, like: *"Write a 5-paragraph essay on the history of AI."*
2.  **The Kill:** While the AI is halfway through streaming the response, run:
    `docker compose stop backend`
3.  **The Silence:** The UI will stop updating. The backend process is dead.
4.  **The Recovery:** Wait 5 seconds, then run:
    `docker compose start backend`
5.  **The Result:** 
    "Watch what happens now. The Temporal Worker reconnects. It sees there is an unfinished workflow step. It doesn't restart from the beginning—it resumes exactly where it left off. If we refresh the UI in a few moments, the entire essay will be there, completed automatically."

---

## Part 4: Conclusion
**Script:**
"By combining Pydantic AI's agentic capabilities with Temporal's durable execution and Redis for real-time delivery, we've built a system that 'auto-heals'. You can lose your database connection, crash your containers, or restart your servers—the conversation never breaks. This is the future of resilient AI applications."
