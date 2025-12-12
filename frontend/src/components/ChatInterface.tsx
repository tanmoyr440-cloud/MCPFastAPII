import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { MetricsDisplay } from './MetricsDisplay';
import { Send, Paperclip, Bot, User, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

interface ChatInterfaceProps {
    sessionId?: string;
    onSessionCreate: (id: string) => void;
    onMetricsUpdate: (metrics: { totalTokens: number; totalCost: number; totalCarbon: number }) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId, onSessionCreate, onMetricsUpdate }) => {
    const { messages, isLoading, sendMessage, currentSessionId } = useChat(sessionId);
    const [input, setInput] = useState('');
    const [fileUrl, setFileUrl] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Calculate metrics whenever messages change
        const totalTokens = messages.reduce((acc, msg) => acc + (msg.token_count || 0), 0);
        const totalCost = messages.reduce((acc, msg) => acc + (msg.cost || 0), 0);
        const totalCarbon = messages.reduce((acc, msg) => acc + (msg.carbon_footprint || 0), 0);

        onMetricsUpdate({ totalTokens, totalCost, totalCarbon });
    }, [messages, onMetricsUpdate]);

    useEffect(() => {
        if (currentSessionId && currentSessionId !== sessionId) {
            onSessionCreate(currentSessionId);
        }
    }, [currentSessionId, sessionId, onSessionCreate]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() && !fileUrl) return;

        await sendMessage(input, fileUrl || undefined);
        setInput('');
        setFileUrl('');
    };

    return (
        <div className="flex flex-col h-full bg-gray-900 text-white">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <Bot size={48} className="mb-4 opacity-50" />
                        <p className="text-lg font-medium">How can I help you today?</p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={clsx(
                                "flex gap-4 max-w-4xl mx-auto",
                                msg.sender === 'user' ? "flex-row-reverse" : "flex-row"
                            )}
                        >
                            <div className={clsx(
                                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                                msg.sender === 'user' ? "bg-blue-600" : "bg-emerald-600"
                            )}>
                                {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                            </div>

                            <div className={clsx(
                                "flex flex-col max-w-[80%]",
                                msg.sender === 'user' ? "items-end" : "items-start"
                            )}>
                                <div className={clsx(
                                    "p-4 rounded-2xl shadow-lg",
                                    msg.sender === 'user'
                                        ? "bg-blue-600 text-white rounded-tr-none"
                                        : "bg-gray-800 text-gray-100 rounded-tl-none border border-gray-700"
                                )}>
                                    {msg.file_url && (
                                        <div className="mb-2 p-2 bg-black/20 rounded text-xs flex items-center gap-2">
                                            <Paperclip size={12} />
                                            {msg.file_name || 'Attached File'}
                                        </div>
                                    )}
                                    <div className="prose prose-invert prose-sm max-w-none">
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                    </div>
                                </div>

                                {/* Metrics for Assistant Messages */}
                                {msg.sender === 'assistant' && (
                                    <MetricsDisplay message={msg} />
                                )}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-800 bg-gray-900/95 backdrop-blur">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative">
                    <div className="relative flex items-end gap-2 bg-gray-800 rounded-xl p-2 border border-gray-700 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
                        <button
                            type="button"
                            className="p-2 text-gray-400 hover:text-white transition-colors"
                            title="Attach File (URL for now)"
                            onClick={() => {
                                const url = prompt("Enter file URL (e.g., /uploads/doc.pdf):");
                                if (url) setFileUrl(url);
                            }}
                        >
                            <Paperclip size={20} />
                        </button>

                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                            placeholder="Type a message..."
                            className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-gray-500 resize-none max-h-32 py-2"
                            rows={1}
                        />

                        <button
                            type="submit"
                            disabled={isLoading || (!input.trim() && !fileUrl)}
                            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                        </button>
                    </div>
                    {fileUrl && (
                        <div className="absolute -top-8 left-0 text-xs text-blue-400 flex items-center gap-1">
                            <Paperclip size={12} />
                            Attached: {fileUrl}
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
};
