import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    PlayIcon, 
    CheckCircleIcon, 
    StopIcon, 
    PlusIcon, 
    PencilIcon,
    ArrowPathIcon,
    CodeBracketIcon,
} from '@heroicons/react/24/outline';
import { getApiBaseUrl } from '../utils/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { getWebSocketUrl } from '../utils/api';

interface Activity {
    id: string;
    type: 'feature_started' | 'feature_verified' | 'feature_blocked' | 'feature_added' | 'feature_updated' | 'session_started' | 'session_ended' | 'commit';
    featureId?: string;
    description: string;
    timestamp: string;
    metadata?: Record<string, string>;
}

interface RecentActivityFeedProps {
    maxItems?: number;
    showHeader?: boolean;
    compact?: boolean;
}

const activityIcons: Record<string, { icon: typeof PlayIcon; color: string; bg: string }> = {
    feature_started: { icon: PlayIcon, color: 'text-blue-600', bg: 'bg-blue-100 dark:bg-blue-900/50' },
    feature_verified: { icon: CheckCircleIcon, color: 'text-green-600', bg: 'bg-green-100 dark:bg-green-900/50' },
    feature_blocked: { icon: StopIcon, color: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/50' },
    feature_added: { icon: PlusIcon, color: 'text-indigo-600', bg: 'bg-indigo-100 dark:bg-indigo-900/50' },
    feature_updated: { icon: PencilIcon, color: 'text-yellow-600', bg: 'bg-yellow-100 dark:bg-yellow-900/50' },
    session_started: { icon: ArrowPathIcon, color: 'text-purple-600', bg: 'bg-purple-100 dark:bg-purple-900/50' },
    session_ended: { icon: CheckCircleIcon, color: 'text-purple-600', bg: 'bg-purple-100 dark:bg-purple-900/50' },
    commit: { icon: CodeBracketIcon, color: 'text-gray-600', bg: 'bg-gray-100 dark:bg-gray-700' },
};

/**
 * Format a timestamp to relative time (e.g., "2 min ago").
 */
function formatRelativeTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) {
        return 'just now';
    } else if (diffMinutes < 60) {
        return `${diffMinutes} min ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hr ago`;
    } else if (diffDays === 1) {
        return 'yesterday';
    } else if (diffDays < 7) {
        return `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}

/**
 * Recent activity feed with live updates.
 * Shows feature changes, session events, and commits.
 */
export function RecentActivityFeed({ 
    maxItems = 10, 
    showHeader = true,
    compact = false 
}: RecentActivityFeedProps) {
    const navigate = useNavigate();
    const [activities, setActivities] = useState<Activity[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // WebSocket for live updates
    const { lastMessage } = useWebSocket(getWebSocketUrl('/api/updates'));

    const fetchActivities = useCallback(async () => {
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/activity?limit=${maxItems}`);
            if (!response.ok) {
                throw new Error('Failed to fetch activities');
            }
            const data = await response.json();
            setActivities(data.activities || []);
            setError(null);
        } catch (err) {
            // Silently fail - activity feed is not critical
            setError(err instanceof Error ? err.message : 'Failed to load');
        } finally {
            setLoading(false);
        }
    }, [maxItems]);

    // Initial fetch
    useEffect(() => {
        fetchActivities();
    }, [fetchActivities]);

    // Refetch on WebSocket updates
    useEffect(() => {
        if (lastMessage) {
            fetchActivities();
        }
    }, [lastMessage, fetchActivities]);

    const handleActivityClick = (activity: Activity) => {
        if (activity.featureId) {
            navigate(`/task/${activity.featureId}`);
        } else if (activity.type === 'session_started' || activity.type === 'session_ended') {
            navigate('/activity');
        }
    };

    if (loading) {
        return (
            <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="flex items-start gap-3 animate-pulse">
                        <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700" />
                        <div className="flex-1 space-y-2">
                            <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded" />
                            <div className="h-3 w-1/4 bg-gray-200 dark:bg-gray-700 rounded" />
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                <p className="text-sm">{error}</p>
                <button 
                    onClick={fetchActivities}
                    className="mt-2 text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (activities.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p className="text-sm">No recent activity</p>
            </div>
        );
    }

    return (
        <div>
            {showHeader && (
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Recent Activity
                    </h3>
                    <button
                        onClick={() => navigate('/activity')}
                        className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                        View all
                    </button>
                </div>
            )}
            
            <div className="space-y-3">
                {activities.map((activity) => {
                    const iconConfig = activityIcons[activity.type] || activityIcons.feature_updated;
                    const Icon = iconConfig.icon;
                    const isClickable = !!activity.featureId || activity.type.startsWith('session_');
                    
                    return (
                        <div
                            key={activity.id}
                            onClick={() => isClickable && handleActivityClick(activity)}
                            className={`
                                flex items-start gap-3 
                                ${compact ? 'p-2' : 'p-3'} 
                                rounded-lg 
                                ${isClickable ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50' : ''}
                                transition-colors
                            `}
                        >
                            {/* Icon */}
                            <div className={`
                                flex-shrink-0 
                                ${compact ? 'w-6 h-6' : 'w-8 h-8'} 
                                rounded-full flex items-center justify-center 
                                ${iconConfig.bg} ${iconConfig.color}
                            `}>
                                <Icon className={compact ? 'w-3 h-3' : 'w-4 h-4'} />
                            </div>
                            
                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <p className={`
                                    text-gray-900 dark:text-gray-100 
                                    ${compact ? 'text-sm' : 'text-sm'}
                                    truncate
                                `}>
                                    {activity.featureId && (
                                        <span className="font-mono font-medium text-indigo-600 dark:text-indigo-400 mr-1">
                                            {activity.featureId}
                                        </span>
                                    )}
                                    {activity.description}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    {formatRelativeTime(activity.timestamp)}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * Compact activity indicator showing count of recent changes.
 */
export function ActivityIndicator() {
    const [count, setCount] = useState(0);
    const { lastMessage } = useWebSocket(getWebSocketUrl('/api/updates'));
    
    useEffect(() => {
        if (lastMessage) {
            setCount(prev => prev + 1);
            // Reset count after 10 seconds
            const timer = setTimeout(() => setCount(0), 10000);
            return () => clearTimeout(timer);
        }
    }, [lastMessage]);

    if (count === 0) return null;

    return (
        <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-indigo-600 rounded-full">
            {count > 9 ? '9+' : count}
        </span>
    );
}
