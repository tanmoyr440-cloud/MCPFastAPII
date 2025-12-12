import React from 'react';
import type { Message } from '../types';
import { Leaf, DollarSign, Activity, CheckCircle, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

interface MetricsDisplayProps {
    message: Message;
}

export const MetricsDisplay: React.FC<MetricsDisplayProps> = ({ message }) => {
    if (!message.token_count && !message.evaluation_scores) return null;

    return (
        <div className="mt-2 p-3 bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700/50 text-xs text-gray-400 flex flex-wrap gap-4">
            {/* Sustainability Metrics */}
            {message.token_count && (
                <div className="flex items-center gap-1" title="Total Tokens">
                    <Activity size={12} className="text-blue-400" />
                    <span>{message.token_count} tokens</span>
                </div>
            )}
            {message.cost && (
                <div className="flex items-center gap-1" title="Estimated Cost">
                    <DollarSign size={12} className="text-green-400" />
                    <span>${message.cost.toFixed(5)}</span>
                </div>
            )}
            {message.carbon_footprint && (
                <div className="flex items-center gap-1" title="Carbon Footprint">
                    <Leaf size={12} className="text-emerald-400" />
                    <span>{message.carbon_footprint.toExponential(2)} kg CO2e</span>
                </div>
            )}

            {/* Evaluation Metrics */}
            {message.evaluation_scores && (
                <>
                    <div className="w-px h-4 bg-gray-700 mx-1" /> {/* Divider */}
                    <div className={clsx("flex items-center gap-1",
                        message.evaluation_scores.faithfulness > 0.7 ? "text-green-400" : "text-yellow-400"
                    )} title="Faithfulness Score">
                        <CheckCircle size={12} />
                        <span>Faith: {message.evaluation_scores.faithfulness.toFixed(2)}</span>
                    </div>
                    <div className={clsx("flex items-center gap-1",
                        message.evaluation_scores.answer_relevancy > 0.7 ? "text-green-400" : "text-yellow-400"
                    )} title="Relevancy Score">
                        <CheckCircle size={12} />
                        <span>Rel: {message.evaluation_scores.answer_relevancy.toFixed(2)}</span>
                    </div>
                </>
            )}

            {message.is_flagged && (
                <div className="flex items-center gap-1 text-red-400 font-bold" title="Flagged for quality issues">
                    <AlertTriangle size={12} />
                    <span>Flagged</span>
                </div>
            )}
        </div>
    );
};
