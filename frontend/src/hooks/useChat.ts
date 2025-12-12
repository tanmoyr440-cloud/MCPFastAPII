import { useState, useEffect, useRef } from 'react';
import { apiClient, endpoints } from '../api/client';
import type { Message, ChatSession } from '../types';

export const useChat = (sessionId?: string) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (sessionId) {
            loadSession(sessionId);
            connectWebSocket(sessionId);
        }
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, [sessionId]);

    const connectWebSocket = (sid: string) => {
        if (wsRef.current) wsRef.current.close();

        const ws = new WebSocket(`ws://localhost:8000/ws/${sid}`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'message') {
                // Update or add message
                setMessages(prev => {
                    // Check if message already exists (e.g. optimistic update)
                    const exists = prev.find(m => m.id === data.payload.id);
                    if (exists) return prev;
                    return [...prev, data.payload];
                });
            }
        };

        wsRef.current = ws;
    };

    const loadSession = async (sid: string) => {
        try {
            const res = await apiClient.get<ChatSession>(`/sessions/${sid}`);
            setMessages(res.data.messages);
            setCurrentSessionId(sid);
        } catch (error) {
            console.error("Failed to load session", error);
        }
    };

    const createSession = async () => {
        try {
            const res = await apiClient.post<ChatSession>('/sessions', { title: 'New Chat' });
            setCurrentSessionId(res.data.id);
            connectWebSocket(res.data.id);
            return res.data.id;
        } catch (error) {
            console.error("Failed to create session", error);
        }
    };

    const sendMessage = async (content: string, fileUrl?: string, fileName?: string) => {
        if (!content.trim() && !fileUrl) return;

        let sid = currentSessionId;
        if (!sid) {
            sid = await createSession();
            if (!sid) return;
        }

        setIsLoading(true);

        // Optimistic update
        const tempMsg: Message = {
            id: Date.now(), // Temporary ID
            content,
            sender: 'user',
            timestamp: new Date().toISOString(),
            file_url: fileUrl,
            file_name: fileName
        };
        setMessages(prev => [...prev, tempMsg]);

        try {
            if (fileUrl) {
                await apiClient.post(endpoints.messagesWithRag(sid), {
                    content,
                    sender: 'user',
                    file_url: fileUrl,
                    file_name: fileName
                });
            } else {
                await apiClient.post(endpoints.messages(sid), {
                    content,
                    sender: 'user'
                });
            }
        } catch (error) {
            console.error("Failed to send message", error);
            // Revert optimistic update?
        } finally {
            setIsLoading(false);
        }
    };

    return {
        messages,
        isLoading,
        sendMessage,
        createSession,
        currentSessionId
    };
};
