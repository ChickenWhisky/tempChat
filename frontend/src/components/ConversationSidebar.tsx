import React from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Plus, Trash2, MessageSquare } from 'lucide-react';
import type { Conversation } from '../types/conversation';
import { Separator } from '@/components/ui/separator';

interface ConversationSidebarProps {
    conversations: Conversation[];
    activeConversationId: string;
    onSelectConversation: (id: string) => void;
    onAddConversation: () => void;
    onDeleteConversation: (id: string) => void;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
    conversations,
    activeConversationId,
    onSelectConversation,
    onAddConversation,
    onDeleteConversation,
}) => {
    return (
        <div className="w-64 border-r bg-muted/20 flex flex-col h-full shrink-0">
            <div className="p-4">
                <Button 
                    onClick={onAddConversation} 
                    className="w-full justify-start gap-2" 
                    variant="outline"
                >
                    <Plus className="h-4 w-4" />
                    New Conversation
                </Button>
            </div>
            
            <Separator />
            
            <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                    {conversations.length === 0 ? (
                        <div className="text-sm text-muted-foreground text-center p-4">
                            No conversations yet
                        </div>
                    ) : (
                        conversations.map((conv) => (
                            <div
                                key={conv.id}
                                className={`group flex items-center justify-between p-2 text-sm rounded-lg hover:bg-muted/50 cursor-pointer overflow-hidden transition-colors ${
                                    activeConversationId === conv.id ? 'bg-muted font-medium' : 'text-muted-foreground'
                                }`}
                                onClick={() => onSelectConversation(conv.id)}
                            >
                                <div className="flex items-center gap-2 min-w-0 flex-1">
                                    <MessageSquare className="h-4 w-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    <span className="truncate flex-1">{conv.title}</span>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:text-destructive shrink-0"
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        onDeleteConversation(conv.id);
                                    }}
                                    title="Delete conversation"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))
                    )}
                </div>
            </ScrollArea>
        </div>
    );
};
