import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { ChatSession } from '../types';
import { MessageSquare, Plus, Menu, X } from 'lucide-react';
import clsx from 'clsx';

interface SessionMetrics {
    totalTokens: number;
    totalCost: number;
    totalCarbon: number;
}

interface LayoutProps {
    children: React.ReactNode;
    currentSessionId?: string;
    onSessionSelect: (id: string) => void;
    onNewChat: () => void;
    metrics?: SessionMetrics;
}

export const Layout: React.FC<LayoutProps> = ({
    children,
    currentSessionId,
    onSessionSelect,
    onNewChat,
    metrics
}) => {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    useEffect(() => {
        loadSessions();
    }, [currentSessionId]); // Reload when session changes to update titles/order

    const loadSessions = async () => {
        try {
            const res = await apiClient.get<ChatSession[]>('/sessions');
            setSessions(res.data.reverse()); // Newest first
        } catch (error) {
            console.error("Failed to load sessions", error);
        }
    };

    return (
        <div className="flex h-screen bg-gray-900 overflow-hidden">
            {/* Sidebar */}
            <div className={clsx(
                "fixed inset-y-0 left-0 z-50 w-64 bg-gray-950 border-r border-gray-800 transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="flex flex-col h-full">
                    <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                            AI Agent
                        </h1>
                        <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden text-gray-400">
                            <X size={20} />
                        </button>
                    </div>

                    <div className="p-4">
                        <button
                            onClick={onNewChat}
                            className="w-full flex items-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
                        >
                            <Plus size={20} />
                            New Chat
                        </button>
                    </div>

                    {metrics && (
                        <div className="mx-4 mb-4 p-3 bg-gray-900 rounded-lg border border-gray-800 text-xs space-y-2">
                            <h3 className="font-semibold text-gray-400 uppercase tracking-wider">Session Stats</h3>
                            <div className="flex justify-between text-gray-300">
                                <span>Tokens:</span>
                                <span>{metrics.totalTokens}</span>
                            </div>
                            <div className="flex justify-between text-gray-300">
                                <span>Cost:</span>
                                <span>${metrics.totalCost.toFixed(5)}</span>
                            </div>
                            <div className="flex justify-between text-gray-300">
                                <span>Carbon:</span>
                                <span>{metrics.totalCarbon.toExponential(2)} kg</span>
                            </div>
                        </div>
                    )}

                    <div className="flex-1 overflow-y-auto px-2 space-y-1">
                        {sessions.map((session) => (
                            <button
                                key={session.id}
                                onClick={() => onSessionSelect(session.id)}
                                className={clsx(
                                    "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-left transition-colors",
                                    currentSessionId === session.id
                                        ? "bg-gray-800 text-white"
                                        : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"
                                )}
                            >
                                <MessageSquare size={16} />
                                <span className="truncate">{session.title || 'Untitled Chat'}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-14 border-b border-gray-800 flex items-center px-4 lg:hidden">
                    <button onClick={() => setIsSidebarOpen(true)} className="text-gray-400">
                        <Menu size={24} />
                    </button>
                </header>
                <main className="flex-1 relative">
                    {children}
                </main>
            </div>
        </div>
    );
};
