import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import {
    CheckCircleIcon,
    ExclamationTriangleIcon,
    ArrowRightIcon,
    ChevronDownIcon,
    ChevronRightIcon,
    ClockIcon,
} from '@heroicons/react/24/outline';

interface Session {
    sessionNumber: number;
    date: string;
    agent: string;
    duration: string;
    focus: string;
    completed: string[];
    inProgress: string[];
    blockers: string[];
    nextSteps: string[];
    technicalNotes: string[];
}

interface ProgressData {
    sessions: Session[];
    current_status: string;
    total_sessions: number;
}

export function ActivityLog() {
    const [progress, setProgress] = useState<ProgressData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedSessions, setExpandedSessions] = useState<Set<number>>(new Set([1])); // Expand first session by default

    // WebSocket for live updates
    const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/api/updates');

    // Fetch initial progress data
    useEffect(() => {
        fetchProgress();
    }, []);

    // Handle WebSocket updates
    useEffect(() => {
        if (lastMessage) {
            fetchProgress();
        }
    }, [lastMessage]);

    const fetchProgress = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/progress');
            if (!response.ok) {
                throw new Error('Failed to fetch progress');
            }
            const data = await response.json();
            setProgress(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const toggleSession = (sessionNumber: number) => {
        setExpandedSessions(prev => {
            const newSet = new Set(prev);
            if (newSet.has(sessionNumber)) {
                newSet.delete(sessionNumber);
            } else {
                newSet.add(sessionNumber);
            }
            return newSet;
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-lg text-gray-600">Loading session history...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">Error: {error}</p>
                <button
                    onClick={fetchProgress}
                    className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!progress || progress.sessions.length === 0) {
        return (
            <div>
                <h2 className="text-3xl font-bold text-gray-900 mb-6">Activity Log</h2>
                <div className="bg-white rounded-lg shadow p-6">
                    <p className="text-gray-600">No session history available yet.</p>
                </div>
            </div>
        );
    }

    // Sort sessions in reverse chronological order (most recent first)
    const sortedSessions = [...progress.sessions].sort((a, b) => b.sessionNumber - a.sessionNumber);
    const latestSessionNumber = sortedSessions[0]?.sessionNumber;

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-3xl font-bold text-gray-900">Activity Log</h2>
                <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${isConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-500'}`} />
                        {isConnected ? 'Live' : 'Offline'}
                    </span>
                    <span className="text-sm text-gray-600">
                        {progress.total_sessions} session{progress.total_sessions !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            <div className="space-y-4">
                {sortedSessions.map((session) => {
                    const isExpanded = expandedSessions.has(session.sessionNumber);
                    const isLatest = session.sessionNumber === latestSessionNumber;

                    return (
                        <div
                            key={session.sessionNumber}
                            className={`bg-white rounded-lg shadow-md border-l-4 transition-all ${isLatest
                                ? 'border-indigo-500 ring-2 ring-indigo-100'
                                : 'border-gray-300'
                                }`}
                        >
                            {/* Session Header */}
                            <div
                                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                                onClick={() => toggleSession(session.sessionNumber)}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3 flex-1">
                                        <button className="mt-1 text-gray-500 hover:text-gray-700">
                                            {isExpanded ? (
                                                <ChevronDownIcon className="h-5 w-5" />
                                            ) : (
                                                <ChevronRightIcon className="h-5 w-5" />
                                            )}
                                        </button>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="text-lg font-semibold text-gray-900">
                                                    Session #{session.sessionNumber}
                                                </h3>
                                                {isLatest && (
                                                    <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs font-medium rounded">
                                                        Latest
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-600 mb-2">
                                                {session.focus}
                                            </p>
                                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                                <span className="flex items-center gap-1">
                                                    <ClockIcon className="h-4 w-4" />
                                                    {session.date}
                                                </span>
                                                {session.duration && (
                                                    <span>{session.duration}</span>
                                                )}
                                                <span className="text-gray-400">•</span>
                                                <span>{session.agent}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Quick stats */}
                                    <div className="flex items-center gap-3 ml-4">
                                        {session.completed.length > 0 && (
                                            <div className="flex items-center gap-1 text-green-600">
                                                <CheckCircleIcon className="h-5 w-5" />
                                                <span className="text-sm font-medium">
                                                    {session.completed.length}
                                                </span>
                                            </div>
                                        )}
                                        {session.blockers.length > 0 && (
                                            <div className="flex items-center gap-1 text-amber-600">
                                                <ExclamationTriangleIcon className="h-5 w-5" />
                                                <span className="text-sm font-medium">
                                                    {session.blockers.length}
                                                </span>
                                            </div>
                                        )}
                                        {session.nextSteps.length > 0 && (
                                            <div className="flex items-center gap-1 text-blue-600">
                                                <ArrowRightIcon className="h-5 w-5" />
                                                <span className="text-sm font-medium">
                                                    {session.nextSteps.length}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Expanded Content */}
                            {isExpanded && (
                                <div className="px-4 pb-4 border-t border-gray-100">
                                    <div className="mt-4 space-y-4">
                                        {/* Completed Items */}
                                        {session.completed.length > 0 && (
                                            <div>
                                                <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                                    <CheckCircleIcon className="h-4 w-4 text-green-600" />
                                                    Completed
                                                </h4>
                                                <ul className="space-y-1">
                                                    {session.completed.map((item, idx) => (
                                                        <li
                                                            key={idx}
                                                            className="text-sm text-gray-600 flex items-start gap-2 pl-6"
                                                        >
                                                            <span className="text-green-600 mt-0.5">✓</span>
                                                            <span>{item}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* In Progress Items */}
                                        {session.inProgress.length > 0 && (
                                            <div>
                                                <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                                    <ClockIcon className="h-4 w-4 text-blue-600" />
                                                    In Progress
                                                </h4>
                                                <ul className="space-y-1">
                                                    {session.inProgress.map((item, idx) => (
                                                        <li
                                                            key={idx}
                                                            className="text-sm text-gray-600 flex items-start gap-2 pl-6"
                                                        >
                                                            <span className="text-blue-600 mt-0.5">⏳</span>
                                                            <span>{item}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* Blockers */}
                                        {session.blockers.length > 0 && (
                                            <div>
                                                <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                                    <ExclamationTriangleIcon className="h-4 w-4 text-amber-600" />
                                                    Blockers
                                                </h4>
                                                <ul className="space-y-1">
                                                    {session.blockers.map((item, idx) => (
                                                        <li
                                                            key={idx}
                                                            className="text-sm text-gray-600 flex items-start gap-2 pl-6"
                                                        >
                                                            <span className="text-amber-600 mt-0.5">⚠</span>
                                                            <span>{item}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* Next Steps */}
                                        {session.nextSteps.length > 0 && (
                                            <div>
                                                <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                                    <ArrowRightIcon className="h-4 w-4 text-blue-600" />
                                                    Next Steps
                                                </h4>
                                                <ul className="space-y-1">
                                                    {session.nextSteps.map((item, idx) => (
                                                        <li
                                                            key={idx}
                                                            className="text-sm text-gray-600 flex items-start gap-2 pl-6"
                                                        >
                                                            <span className="text-blue-600 mt-0.5">→</span>
                                                            <span>{item}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* Technical Notes */}
                                        {session.technicalNotes.length > 0 && (
                                            <div>
                                                <h4 className="text-sm font-semibold text-gray-700 mb-2">
                                                    Technical Notes
                                                </h4>
                                                <ul className="space-y-1">
                                                    {session.technicalNotes.map((note, idx) => (
                                                        <li
                                                            key={idx}
                                                            className="text-sm text-gray-600 pl-6"
                                                        >
                                                            • {note}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
