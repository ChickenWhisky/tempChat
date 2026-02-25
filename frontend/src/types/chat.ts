export type ModelMessagePart = 
  | { part_kind: 'system-prompt'; content: string }
  | { part_kind: 'user-prompt'; content: string }
  | { part_kind: 'text'; content: string };

export type ChatMessage = {
  id: string;
  role: 'model-request' | 'model-response';
  parts: ModelMessagePart[];
  status: "streaming" | "complete" | "error";
};

export type StreamEvent = 
  | { type: "start"; message_id: string }
  | { type: "token"; message_id: string; content: string }
  | { type: "end"; message_id: string }
  | { type: "error"; message_id: string; error: string };
