import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, StreamEvent } from '../types/chat';
import { MessageItem } from './MessageItem';
import { Send, Loader2, Bot } from 'lucide-react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';

interface ChatAreaProps {
    conversationId: string;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ conversationId }) => {
    const storageKey = `chatMessages_${conversationId}`;

    const [messages, setMessages] = useState<ChatMessage[]>(() => {
        const savedMessagesJson = localStorage.getItem(storageKey);
        if (savedMessagesJson) {
            try {
                const parsedMessages = JSON.parse(savedMessagesJson) as ChatMessage[];
                const validatedMessages: ChatMessage[] = [];
                
                for (const message of parsedMessages) {
                    if (message.status === 'error') {
                        if (validatedMessages.length > 0 && validatedMessages[validatedMessages.length - 1].role === 'model-request') {
                            validatedMessages.pop();
                        }
                    } else {
                        validatedMessages.push(message);
                    }
                }
                
                if (validatedMessages.length > 0 && validatedMessages[validatedMessages.length - 1].role === 'model-request') {
                    validatedMessages.pop();
                }
                return validatedMessages;
            } catch (error) {
                console.error('Failed to parse chat messages from local storage', error);
            }
        }
        return [];
    });
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setIsLoading(false);
        setInput('');
        const savedMessagesJson = localStorage.getItem(`chatMessages_${conversationId}`);
        if (savedMessagesJson) {
            try {
                const parsedMessages = JSON.parse(savedMessagesJson) as ChatMessage[];
                setMessages(parsedMessages);
            } catch (error) {
                setMessages([]);
            }
        } else {
            setMessages([]);
        }
    }, [conversationId]);

    useEffect(() => {
        if (conversationId) {
            localStorage.setItem(storageKey, JSON.stringify(messages));
        }
    }, [messages, storageKey, conversationId]);

    useEffect(() => {
        if (scrollRef.current) {
            const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                 scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }
    }, [messages]);

    useEffect(() => {
        const fetchHistory = async () => {
            if (!conversationId) return;

            try {
                const apiUrl = import.meta.env.VITE_API_URL || '';
                const endpoint = apiUrl.endsWith('/api') 
                    ? `${apiUrl}/chat/${conversationId}/history` 
                    : `${apiUrl}/api/chat/${conversationId}/history`;
                
                const response = await fetch(endpoint);
                if (!response.ok) return;
                
                const data = await response.json();
                if (Array.isArray(data) && data.length > 0) {
                    const transformedMessages: ChatMessage[] = data.map((msg: any) => ({
                        id: crypto.randomUUID(), 
                        role: msg.kind === 'request' ? 'model-request' : 'model-response',
                        parts: (msg.parts || []).map((part: any) => ({
                            part_kind: part.part_kind,
                            content: typeof part.content === 'string' ? part.content : JSON.stringify(part.content)
                        })),
                        status: 'complete' as const
                    }));
                    
                    setMessages(transformedMessages);
                }
            } catch (error) {
                console.error("Failed to fetch durable chat history:", error);
            }
        };

        fetchHistory();
    }, [conversationId]);

    const handleSendMessage = async () => {
        if (!input.trim() || isLoading || !conversationId) return;

        const userMsgId = crypto.randomUUID();
        const assistantMsgId = crypto.randomUUID();
        const userMessage: ChatMessage = {
            id: userMsgId,
            role: 'model-request',
            parts: [{ part_kind: 'user-prompt', content: input }],
            status: 'complete'
        };

        setMessages(previousMessages => [...previousMessages, userMessage]);
        setInput('');
        setIsLoading(true);

        let currentAssistantContent = "";

        try {
            const apiUrl = import.meta.env.VITE_API_URL || '';
            const endpoint = apiUrl.endsWith('/api') ? `${apiUrl}/chat` : `${apiUrl}/api/chat`;
            await fetchEventSource(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: input, 
                    message_id: assistantMsgId,
                    conversation_id: conversationId
                }),
                onmessage(event) {
                    const data: StreamEvent = JSON.parse(event.data);

                    if (data.type === 'start') {
                        setMessages(previousMessages => {
                            if (previousMessages.some(message => message.id === data.message_id)) return previousMessages;
                            return [...previousMessages, {
                                id: data.message_id,
                                role: 'model-response',
                                parts: [{ part_kind: 'text', content: '' }],
                                status: 'streaming'
                            }];
                        });
                    } else if (data.type === 'token') {
                        currentAssistantContent += data.content;
                        setMessages(previousMessages => previousMessages.map(message => 
                            message.id === data.message_id 
                                ? { ...message, parts: [{ part_kind: 'text', content: currentAssistantContent }] } 
                                : message
                        ));
                    } else if (data.type === 'end') {
                        setMessages(previousMessages => previousMessages.map(message => 
                            message.id === data.message_id ? { ...message, status: 'complete' } : message
                        ));
                        setIsLoading(false);
                    } else if (data.type === 'error') {
                        setMessages(previousMessages => previousMessages.map(message => 
                            message.id === data.message_id ? { ...message, status: 'error' } : message
                        ));
                        setIsLoading(false);
                    }
                },
                onerror(error) {
                    setIsLoading(false);
                    throw error;
                }
            });
        } catch (error) {
            console.error("Failed to connect to stream", error);
            setIsLoading(false);
        }
    };

    return (
        <Card className="flex flex-col h-full w-full rounded-none border-y-0 border-r-0 shadow-none">
            <CardHeader className="p-4 border-b flex flex-row justify-between items-center bg-background/95 backdrop-blur">
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                    <Bot className="w-5 h-5 text-primary" />
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

            <CardContent className="flex-1 p-0 overflow-hidden">
                <ScrollArea ref={scrollRef} className="h-full">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full min-h-[400px] opacity-60 space-y-4">
                            <div className="p-4 rounded-full bg-muted ring-1 ring-border">
                               <Bot size={48} className="text-primary" />
                            </div>
                            <p className="text-muted-foreground font-medium">Start a conversation with the AI</p>
                        </div>
                    ) : (
                        <div className="space-y-px py-4">
                            {messages.map(message => <MessageItem key={message.id} message={message} />)}
                        </div>
                    )}
                </ScrollArea>
            </CardContent>

            <CardFooter className="p-4 border-t bg-muted/50 flex flex-col gap-2">
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
                        disabled={isLoading || !input.trim() || !conversationId}
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
