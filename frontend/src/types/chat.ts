export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "streaming" | "complete" | "error";
};

export type StreamEvent = 
  | { type: "start"; message_id: string }
  | { type: "token"; message_id: string; content: string }
  | { type: "end"; message_id: string }
  | { type: "error"; message_id: string; error: string };
