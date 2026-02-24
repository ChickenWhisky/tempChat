import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, StreamEvent } from '../types/chat';
import { MessageItem } from './MessageItem';
import { Send, Loader2, Bot } from 'lucide-react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';

export const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (scrollRef.current) {
            const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                 scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
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
        <Card className="flex flex-col h-screen max-w-4xl mx-auto rounded-none border-y-0 sm:border-y sm:rounded-xl sm:h-[calc(100vh-2rem)] sm:my-4 shadow-xl">
            {/* Header */}
            <CardHeader className="p-4 border-b flex flex-row justify-between items-center sticky top-0 z-10 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:bg-slate-950/95">
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                    <Bot className="w-5 h-5 text-blue-600" />
                    AI Chatbot
                </CardTitle>
                <div className="text-xs flex items-center gap-2 text-slate-500 font-medium">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Connected
                </div>
            </CardHeader>

            {/* Messages */}
            <CardContent className="flex-1 p-0 overflow-hidden">
                <ScrollArea ref={scrollRef} className="h-full">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full min-h-[400px] opacity-60 space-y-4">
                            <div className="p-4 rounded-full bg-slate-100 dark:bg-slate-800 ring-1 ring-slate-200 dark:ring-slate-700">
                               <Bot size={48} className="text-blue-500" />
                            </div>
                            <p className="text-slate-600 dark:text-slate-400 font-medium">Start a conversation with the AI</p>
                        </div>
                    ) : (
                        <div className="space-y-px py-4">
                            {messages.map(m => <MessageItem key={m.id} message={m} />)}
                        </div>
                    )}
                </ScrollArea>
            </CardContent>

            {/* Input */}
            <CardFooter className="p-4 border-t bg-slate-50/50 dark:bg-slate-950/50 flex flex-col gap-2">
                <div className="relative flex items-center w-full">
                    <Input
                        type="text"
                        placeholder="Type your message..."
                        className="pr-12 h-12 text-base rounded-xl"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    />
                    <Button
                        onClick={handleSendMessage}
                        disabled={isLoading || !input.trim()}
                        size="icon"
                        className="absolute right-1.5 h-9 w-9 rounded-lg"
                    >
                        {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                    </Button>
                </div>
            </CardFooter>
        </Card>
    );
};
