export interface Message {
    id: number;
    content: string;
    sender: 'user' | 'assistant';
    timestamp: string;
    file_url?: string;
    file_name?: string;
    token_count?: number;
    cost?: number;
    carbon_footprint?: number;
    evaluation_scores?: {
        faithfulness: number;
        answer_relevancy: number;
    };
    is_flagged?: boolean;
}

export interface ChatSession {
    id: string;
    title: string;
    created_at: string;
    messages: Message[];
}

export interface UsageMetrics {
    total_tokens: number;
    cost_usd: number;
    carbon_footprint_kg: number;
}
