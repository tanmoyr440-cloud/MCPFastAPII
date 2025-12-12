import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const endpoints = {
    sessions: '/sessions',
    messages: (sessionId: string) => `/sessions/${sessionId}/messages`,
    messagesWithRag: (sessionId: string) => `/sessions/${sessionId}/messages/with-rag`,
};
