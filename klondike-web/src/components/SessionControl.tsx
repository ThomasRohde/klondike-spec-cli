import { useState, useEffect } from 'react';
import { getApiBaseUrl, apiCall } from '../utils/api';
import {
    PlayIcon,
    StopIcon,
    ExclamationTriangleIcon,
    ChevronDownIcon,
    ChevronUpIcon,
} from '@heroicons/react/24/outline';

interface SessionData {
    session_number: number;
    date: string;
    focus: string;
}

interface GitStatus {
    is_clean: boolean;
    branch: string;
    has_uncommitted?: boolean;
}

interface SessionControlProps {
    currentSession: SessionData | null;
    isSessionActive: boolean;
    gitStatus: GitStatus | null;
    onSessionChange: () => void;
}

export function SessionControl({
    currentSession,
    isSessionActive,
    gitStatus,
    onSessionChange,
}: SessionControlProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [loading, setLoading] = useState(false);

    // Start session form state
    const [focus, setFocus] = useState('');

    // End session form state
    const [summary, setSummary] = useState('');
    const [completed, setCompleted] = useState('');
    const [blockers, setBlockers] = useState('');
    const [nextSteps, setNextSteps] = useState('');
    const [showEndConfirm, setShowEndConfirm] = useState(false);

    // Reset form when session changes
    useEffect(() => {
        if (!isSessionActive) {
            setSummary('');
            setCompleted('');
            setBlockers('');
            setNextSteps('');
            setShowEndConfirm(false);
        }
    }, [isSessionActive]);

    const handleStartSession = async () => {
        if (!focus.trim()) return;

        setLoading(true);
        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/session/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ focus: focus.trim() }),
                }),
                {
                    loadingMessage: 'Starting session...',
                    successMessage: (data: { session?: { session_number: number } }) =>
                        `Session ${data.session?.session_number || ''} started!`,
                    errorMessage: 'Failed to start session',
                }
            );
            setFocus('');
            setIsExpanded(false);
            onSessionChange();
        } catch (error) {
            // Error already handled by apiCall
        } finally {
            setLoading(false);
        }
    };

    const handleEndSession = async () => {
        setLoading(true);
        try {
            const payload: {
                summary?: string;
                completed?: string[];
                blockers?: string[];
                nextSteps?: string[];
            } = {};

            if (summary.trim()) payload.summary = summary.trim();
            if (completed.trim()) {
                payload.completed = completed
                    .split('\n')
                    .map((s) => s.trim())
                    .filter(Boolean);
            }
            if (blockers.trim()) {
                payload.blockers = blockers
                    .split('\n')
                    .map((s) => s.trim())
                    .filter(Boolean);
            }
            if (nextSteps.trim()) {
                payload.nextSteps = nextSteps
                    .split('\n')
                    .map((s) => s.trim())
                    .filter(Boolean);
            }

            await apiCall(
                fetch(`${getApiBaseUrl()}/api/session/end`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                }),
                {
                    loadingMessage: 'Ending session...',
                    successMessage: 'Session ended successfully!',
                    errorMessage: 'Failed to end session',
                }
            );
            setShowEndConfirm(false);
            setIsExpanded(false);
            onSessionChange();
        } catch (error) {
            // Error already handled by apiCall
        } finally {
            setLoading(false);
        }
    };

    const hasUncommittedChanges = gitStatus && !gitStatus.is_clean;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
            {/* Header with expand/collapse */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors rounded-t-lg"
            >
                <div className="flex items-center gap-3">
                    {isSessionActive ? (
                        <>
                            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                            <span className="font-medium text-gray-900 dark:text-white">
                                Session #{currentSession?.session_number} Active
                            </span>
                        </>
                    ) : (
                        <>
                            <div className="w-3 h-3 bg-gray-400 rounded-full" />
                            <span className="font-medium text-gray-600 dark:text-gray-400">
                                No Active Session
                            </span>
                        </>
                    )}
                </div>
                {isExpanded ? (
                    <ChevronUpIcon className="w-5 h-5 text-gray-500" />
                ) : (
                    <ChevronDownIcon className="w-5 h-5 text-gray-500" />
                )}
            </button>

            {/* Expanded content */}
            {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700">
                    {/* Git status warning */}
                    {hasUncommittedChanges && (
                        <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-start gap-2">
                            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <span className="font-medium text-yellow-800 dark:text-yellow-400">
                                    Uncommitted changes detected
                                </span>
                                <p className="text-yellow-700 dark:text-yellow-500 mt-0.5">
                                    You have uncommitted changes on branch{' '}
                                    <code className="bg-yellow-100 dark:bg-yellow-900/50 px-1 rounded">
                                        {gitStatus?.branch}
                                    </code>
                                    . Consider committing before {isSessionActive ? 'ending' : 'starting'} a session.
                                </p>
                            </div>
                        </div>
                    )}

                    {isSessionActive ? (
                        /* End Session Form */
                        <div className="mt-4 space-y-4">
                            {/* Current session info */}
                            <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                                <p className="text-sm text-indigo-800 dark:text-indigo-300">
                                    <span className="font-medium">Focus:</span> {currentSession?.focus}
                                </p>
                                <p className="text-sm text-indigo-700 dark:text-indigo-400 mt-1">
                                    Started: {currentSession?.date}
                                </p>
                            </div>

                            {showEndConfirm ? (
                                <>
                                    <div className="space-y-3">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                Summary (optional)
                                            </label>
                                            <input
                                                type="text"
                                                value={summary}
                                                onChange={(e) => setSummary(e.target.value)}
                                                placeholder="Brief summary of what was accomplished..."
                                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                Completed Items (one per line)
                                            </label>
                                            <textarea
                                                value={completed}
                                                onChange={(e) => setCompleted(e.target.value)}
                                                placeholder="F001 - Feature implemented&#10;F002 - Bug fixed"
                                                rows={3}
                                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                Blockers (one per line)
                                            </label>
                                            <textarea
                                                value={blockers}
                                                onChange={(e) => setBlockers(e.target.value)}
                                                placeholder="Optional: any blockers encountered..."
                                                rows={2}
                                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                Next Steps (one per line, auto-generated if empty)
                                            </label>
                                            <textarea
                                                value={nextSteps}
                                                onChange={(e) => setNextSteps(e.target.value)}
                                                placeholder="Leave empty to auto-generate from priority features..."
                                                rows={2}
                                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex gap-3">
                                        <button
                                            onClick={handleEndSession}
                                            disabled={loading}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                        >
                                            <StopIcon className="w-5 h-5" />
                                            {loading ? 'Ending...' : 'Confirm End Session'}
                                        </button>
                                        <button
                                            onClick={() => setShowEndConfirm(false)}
                                            disabled={loading}
                                            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <button
                                    onClick={() => setShowEndConfirm(true)}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    <StopIcon className="w-5 h-5" />
                                    End Session
                                </button>
                            )}
                        </div>
                    ) : (
                        /* Start Session Form */
                        <div className="mt-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Session Focus <span className="text-red-500">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={focus}
                                    onChange={(e) => setFocus(e.target.value)}
                                    placeholder="F001 - Implement feature description..."
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && focus.trim()) {
                                            handleStartSession();
                                        }
                                    }}
                                />
                                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                    Describe what you'll be working on in this session
                                </p>
                            </div>

                            <button
                                onClick={handleStartSession}
                                disabled={loading || !focus.trim()}
                                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <PlayIcon className="w-5 h-5" />
                                {loading ? 'Starting...' : 'Start Session'}
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
