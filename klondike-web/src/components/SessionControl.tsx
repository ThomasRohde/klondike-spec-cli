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
        } finally {
            setLoading(false);
        }
    };

    const hasUncommittedChanges = gitStatus && !gitStatus.is_clean;

    return (
        <div className="widget">
            {/* Header with expand/collapse */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between hover:opacity-80 transition-opacity -m-6 p-6 mb-0"
            >
                <div className="flex items-center gap-3">
                    {isSessionActive ? (
                        <>
                            <div className="session-banner-pulse" />
                            <span className="font-display font-semibold text-slate-900 dark:text-white">
                                Session #{currentSession?.session_number} Active
                            </span>
                        </>
                    ) : (
                        <>
                            <div className="w-3 h-3 bg-[var(--neutral-slate)] rounded-full opacity-50" />
                            <span className="font-medium text-[var(--neutral-slate)]">
                                No Active Session
                            </span>
                        </>
                    )}
                </div>
                {isExpanded ? (
                    <ChevronUpIcon className="w-5 h-5 text-[var(--neutral-slate)]" />
                ) : (
                    <ChevronDownIcon className="w-5 h-5 text-[var(--neutral-slate)]" />
                )}
            </button>

            {/* Expanded content */}
            {isExpanded && (
                <div className="pt-4 mt-4 border-t border-[var(--parchment-200)] dark:border-white/10">
                    {/* Git status warning */}
                    {hasUncommittedChanges && (
                        <div className="mb-4 p-4 bg-[var(--warning-light)] dark:bg-amber-900/20 border border-[var(--warning-amber)]/30 rounded-lg flex items-start gap-3">
                            <ExclamationTriangleIcon className="w-5 h-5 text-[var(--warning-amber)] flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <span className="font-semibold text-[var(--warning-amber)]">
                                    Uncommitted changes detected
                                </span>
                                <p className="text-amber-800 dark:text-amber-300 mt-1">
                                    You have uncommitted changes on branch{' '}
                                    <code className="font-mono bg-amber-200/50 dark:bg-amber-900/50 px-1.5 py-0.5 rounded text-xs">
                                        {gitStatus?.branch}
                                    </code>
                                    . Consider committing before {isSessionActive ? 'ending' : 'starting'} a session.
                                </p>
                            </div>
                        </div>
                    )}

                    {isSessionActive ? (
                        /* End Session Form */
                        <div className="space-y-4">
                            {/* Current session info */}
                            <div className="p-4 bg-[var(--gold-100)] dark:bg-[var(--gold-900)]/20 border border-[var(--gold-300)] dark:border-[var(--gold-700)]/30 rounded-lg">
                                <p className="text-sm text-[var(--gold-800)] dark:text-[var(--gold-300)]">
                                    <span className="font-semibold">Focus:</span> {currentSession?.focus}
                                </p>
                                <p className="text-sm text-[var(--gold-700)] dark:text-[var(--gold-400)] mt-1">
                                    Started: {currentSession?.date}
                                </p>
                            </div>

                            {showEndConfirm ? (
                                <>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                                                Summary (optional)
                                            </label>
                                            <input
                                                type="text"
                                                value={summary}
                                                onChange={(e) => setSummary(e.target.value)}
                                                placeholder="Brief summary of what was accomplished..."
                                                className="w-full px-4 py-2.5 border border-[var(--parchment-300)] dark:border-white/10 rounded-lg bg-white dark:bg-[var(--slate-850)] text-slate-900 dark:text-white placeholder-[var(--neutral-slate)] focus:ring-2 focus:ring-[var(--gold-400)] focus:border-transparent transition-shadow"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                                                Completed Items (one per line)
                                            </label>
                                            <textarea
                                                value={completed}
                                                onChange={(e) => setCompleted(e.target.value)}
                                                placeholder="F001 - Feature implemented&#10;F002 - Bug fixed"
                                                rows={3}
                                                className="w-full px-4 py-2.5 border border-[var(--parchment-300)] dark:border-white/10 rounded-lg bg-white dark:bg-[var(--slate-850)] text-slate-900 dark:text-white placeholder-[var(--neutral-slate)] focus:ring-2 focus:ring-[var(--gold-400)] focus:border-transparent transition-shadow font-mono text-sm"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                                                Blockers (one per line)
                                            </label>
                                            <textarea
                                                value={blockers}
                                                onChange={(e) => setBlockers(e.target.value)}
                                                placeholder="Optional: any blockers encountered..."
                                                rows={2}
                                                className="w-full px-4 py-2.5 border border-[var(--parchment-300)] dark:border-white/10 rounded-lg bg-white dark:bg-[var(--slate-850)] text-slate-900 dark:text-white placeholder-[var(--neutral-slate)] focus:ring-2 focus:ring-[var(--gold-400)] focus:border-transparent transition-shadow font-mono text-sm"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                                                Next Steps (one per line, auto-generated if empty)
                                            </label>
                                            <textarea
                                                value={nextSteps}
                                                onChange={(e) => setNextSteps(e.target.value)}
                                                placeholder="Leave empty to auto-generate from priority features..."
                                                rows={2}
                                                className="w-full px-4 py-2.5 border border-[var(--parchment-300)] dark:border-white/10 rounded-lg bg-white dark:bg-[var(--slate-850)] text-slate-900 dark:text-white placeholder-[var(--neutral-slate)] focus:ring-2 focus:ring-[var(--gold-400)] focus:border-transparent transition-shadow font-mono text-sm"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex gap-3 pt-2">
                                        <button
                                            onClick={handleEndSession}
                                            disabled={loading}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-[var(--danger-rust)] text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium btn-press"
                                        >
                                            <StopIcon className="w-5 h-5" />
                                            {loading ? 'Ending...' : 'Confirm End Session'}
                                        </button>
                                        <button
                                            onClick={() => setShowEndConfirm(false)}
                                            disabled={loading}
                                            className="px-4 py-2.5 border border-[var(--parchment-300)] dark:border-white/10 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-[var(--parchment-100)] dark:hover:bg-white/5 disabled:opacity-50 transition-colors font-medium"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <button
                                    onClick={() => setShowEndConfirm(true)}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[var(--danger-rust)] text-white rounded-lg hover:bg-red-700 transition-colors font-medium btn-press"
                                >
                                    <StopIcon className="w-5 h-5" />
                                    End Session
                                </button>
                            )}
                        </div>
                    ) : (
                        /* Start Session Form */
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                                    Session Focus <span className="text-[var(--danger-rust)]">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={focus}
                                    onChange={(e) => setFocus(e.target.value)}
                                    placeholder="F001 - Implement feature description..."
                                    className="w-full px-4 py-2.5 border border-[var(--parchment-300)] dark:border-white/10 rounded-lg bg-white dark:bg-[var(--slate-850)] text-slate-900 dark:text-white placeholder-[var(--neutral-slate)] focus:ring-2 focus:ring-[var(--gold-400)] focus:border-transparent transition-shadow"
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && focus.trim()) {
                                            handleStartSession();
                                        }
                                    }}
                                />
                                <p className="mt-1.5 text-xs text-[var(--neutral-slate)]">
                                    Describe what you'll be working on in this session
                                </p>
                            </div>

                            <button
                                onClick={handleStartSession}
                                disabled={loading || !focus.trim()}
                                className="w-full btn-gold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
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
