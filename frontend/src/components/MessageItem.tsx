import React from 'react';
import { ChatMessage } from '../types/chat';
import { Bot, User } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={cn(
      "flex w-full gap-4 p-4",
      isAssistant ? "bg-slate-50 dark:bg-slate-900" : "bg-white dark:bg-slate-950"
    )}>
      <div className={cn(
        "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow",
        isAssistant ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-700"
      )}>
        {isAssistant ? <Bot size={18} /> : <User size={18} />}
      </div>
      <div className="flex-1 space-y-2 overflow-hidden">
        <p className="text-sm font-medium text-slate-500">
          {isAssistant ? "Assistant" : "You"}
        </p>
        <div className="prose prose-slate dark:prose-invert max-w-none text-slate-800 dark:text-slate-200">
          {message.content}
          {message.status === 'streaming' && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-blue-600 animate-pulse align-middle" />
          )}
        </div>
        {message.status === 'error' && (
          <p className="text-xs text-red-500 font-medium">An error occurred during streaming.</p>
        )}
      </div>
    </div>
  );
};
