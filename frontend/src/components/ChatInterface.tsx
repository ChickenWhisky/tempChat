import React, { useState, useEffect } from 'react';
import { ConversationSidebar } from './ConversationSidebar';
import { ChatArea } from './ChatArea';
import type { Conversation } from '../types/conversation';

export const ChatInterface: React.FC = () => {
    const [conversations, setConversations] = useState<Conversation[]>(() => {
        const savedConversationsJson = localStorage.getItem('appConversations');
        if (savedConversationsJson) {
            try {
                return JSON.parse(savedConversationsJson);
            } catch (error) {
                console.error('Failed to parse appConversations from local storage', error);
            }
        }
        return [];
    });

    const [activeConversationId, setActiveConversationId] = useState<string>(() => {
        const savedActiveId = localStorage.getItem('activeConversationId');
        if (savedActiveId) return savedActiveId;
        return '';
    });

    useEffect(() => {
        localStorage.setItem('appConversations', JSON.stringify(conversations));
    }, [conversations]);

    useEffect(() => {
        localStorage.setItem('activeConversationId', activeConversationId);
    }, [activeConversationId]);

    useEffect(() => {
        if (conversations.length > 0 && !activeConversationId) {
            setActiveConversationId(conversations[0].id);
        } else if (conversations.length === 0 && activeConversationId) {
            setActiveConversationId('');
        }
    }, [conversations, activeConversationId]);

    const handleAddConversation = () => {
        const newId = crypto.randomUUID();
        const nextIndex = conversations.length + 1;
        const newConversation: Conversation = {
            id: newId,
            title: `convo-${nextIndex}`, 
            createdAt: Date.now()
        };
        setConversations(previousConversations => [newConversation, ...previousConversations]);
        setActiveConversationId(newId);
    };

    const handleDeleteConversation = async (id: string) => {
        setConversations(previousConversations => previousConversations.filter(conversation => conversation.id !== id));
        if (activeConversationId === id) {
            setActiveConversationId('');
        }
        
        localStorage.removeItem(`chatMessages_${id}`);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || '';
            const endpoint = apiUrl.endsWith('/api') 
                ? `${apiUrl}/chat/${id}` 
                : `${apiUrl}/api/chat/${id}`;
                
            await fetch(endpoint, {
                method: 'DELETE'
            });
            console.log(`Backend workflow terminology requested for ${id}`);
        } catch (error) {
            console.error("Failed to delete conversation on backend", error);
        }
    };

    return (
        <div className="flex h-screen w-full bg-background overflow-hidden">
            <ConversationSidebar 
                conversations={conversations}
                activeConversationId={activeConversationId}
                onSelectConversation={setActiveConversationId}
                onAddConversation={handleAddConversation}
                onDeleteConversation={handleDeleteConversation}
            />
            
            <main className="flex-1 flex flex-col h-full min-w-0">
                {activeConversationId ? (
                    <ChatArea key={activeConversationId} conversationId={activeConversationId} />
                ) : (
                    <div className="flex flex-col items-center justify-center h-full opacity-60 space-y-4">
                        <p className="text-muted-foreground font-medium">Select or create a conversation to begin.</p>
                    </div>
                )}
            </main>
        </div>
    );
};
