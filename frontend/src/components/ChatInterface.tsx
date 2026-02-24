import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, StreamEvent } from '../types/chat';
import { MessageItem } from './MessageItem';
import { Send, Loader2,Bot} from 'lucide-react';
import { fetchEventSource } from '@microsoft/fetch-event-source';

export const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMsgId = crypto.randomUUID();
        const userMessage: ChatMessage = {
            id: userMsgId,
            role: 'user',
            content: input,
            status: 'complete'
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        // Placeholder for assistant message content
        let currentAssistantContent = "";

        try {
            await fetchEventSource('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: input }),
                onmessage(ev) {
                    const data: StreamEvent = JSON.parse(ev.data);

                    if (data.type === 'start') {
                        setMessages(prev => [...prev, {
                            id: data.message_id,
                            role: 'assistant',
                            content: '',
                            status: 'streaming'
                        }]);
                    } else if (data.type === 'token') {
                        currentAssistantContent += data.content;
                        setMessages(prev => prev.map(m => 
                            m.id === data.message_id 
                                ? { ...m, content: currentAssistantContent } 
                                : m
                        ));
                    } else if (data.type === 'end') {
                        setMessages(prev => prev.map(m => 
                            m.id === data.message_id 
                                ? { ...m, status: 'complete' } 
                                : m
                        ));
                        setIsLoading(false);
                    } else if (data.type === 'error') {
                        setMessages(prev => prev.map(m => 
                            m.id === data.message_id 
                                ? { ...m, status: 'error' } 
                                : m
                        ));
                        setIsLoading(false);
                        console.error("Stream Error:", data.error);
                    }
                },
                onerror(err) {
                    setIsLoading(false);
                    throw err; // fetch-event-source will retry if we don't handle it
                }
            });
        } catch (error) {
            console.error("Failed to connect to stream", error);
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen max-w-4xl mx-auto border-x bg-white dark:bg-slate-950">
            {/* Header */}
            <header className="p-4 border-b flex justify-between items-center bg-white dark:bg-slate-900 sticky top-0 z-10">
                <h1 className="text-xl font-bold text-slate-800 dark:text-white">AI Chatbot</h1>
                <div className="text-xs flex items-center gap-2 text-slate-500">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Connected to Backend
                </div>
            </header>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1 py-4 scroll-smooth">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full opacity-50 space-y-4">
                        <div className="p-4 rounded-full bg-slate-100 dark:bg-slate-800">
                           <Bot size={48} className="text-blue-500" />
                        </div>
                        <p className="text-slate-600 dark:text-slate-400 font-medium">Start a conversation with the AI</p>
                    </div>
                ) : (
                    messages.map(m => <MessageItem key={m.id} message={m} />)
                )}
            </div>

            {/* Input */}
            <div className="p-4 border-t bg-slate-50 dark:bg-slate-900">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        placeholder="Type your message..."
                        className="w-full p-3 pr-12 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 p-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                    </button>
                </div>
                <p className="mt-2 text-[10px] text-center text-slate-400">
                    Phase 1: Basic Streaming without Temporal
                </p>
            </div>
        </div>
    );
};
