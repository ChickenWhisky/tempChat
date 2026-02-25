import React from 'react';
import type { ChatMessage } from '../types/chat';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isAssistant = message.role === 'model-response';
  const content = message.parts.map(p => p.content).join('\n');

  return (
    <div className={cn(
      "flex w-full gap-4 p-4",
      isAssistant ? "bg-muted/50" : "bg-background"
    )}>
      <Avatar className={cn(
        "h-8 w-8 border shadow",
        isAssistant ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
      )}>
        <AvatarFallback className="bg-transparent">
          {isAssistant ? <Bot size={18} /> : <User size={18} />}
        </AvatarFallback>
      </Avatar>
      
      <div className="flex-1 space-y-2 overflow-hidden">
        <p className="text-sm font-medium text-muted-foreground">
          {isAssistant ? "Assistant" : "You"}
        </p>
        <div className="prose prose-slate dark:prose-invert max-w-none text-foreground whitespace-pre-wrap">
          {content}
          {message.status === 'streaming' && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse align-middle" />
          )}
        </div>
        {message.status === 'error' && (
          <p className="text-xs text-red-500 font-medium">An error occurred during streaming.</p>
        )}
      </div>
    </div>
  );
};

