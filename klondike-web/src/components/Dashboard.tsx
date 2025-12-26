import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { getApiBaseUrl, getWebSocketUrl } from '../utils/api';
import { ProgressRing } from './ProgressRing';
import { SessionControl } from './SessionControl';
import { StatusChart } from './StatusChart';
import { RecentActivityFeed } from './RecentActivityFeed';
import { DashboardStatsSkeleton, ProgressRingSkeleton, Skeleton } from './Skeleton';
import { WidgetGrid, WidgetGridControls, useWidgetLayout, type WidgetConfig } from './WidgetGrid';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface StatusData {
    project_name: string;
    project_version: string;
    completion_percentage: number;
    feature_counts: {
        verified: number;
        blocked: number;
        in_progress: number;
        not_started: number;
        total: number;
    };
    is_session_active?: boolean;
    current_session?: {
        id: number;
        date: string;
        focus: string;
    } | null;
    last_session: {
        id: number;
        date: string;
        focus: string;
    } | null;
    git_status: {
        is_clean: boolean;
        clean?: boolean;
        branch: string;
        recent_commits: Array<{
            hash: string;
            date: string;
            message: string;
        }>;
    };
    priority_features: Array<{
        id: string;
        description: string;
        status: string;
        priority: number;
    }>;
}

export function Dashboard() {
    const [status, setStatus] = useState<StatusData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isEditMode, setIsEditMode] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const { widgets, setWidgets } = useWidgetLayout();

    // WebSocket for live updates
    const { lastMessage, isConnected } = useWebSocket(getWebSocketUrl('/api/updates'));

    // Fetch initial status data
    useEffect(() => {
        fetchStatus();
    }, []);

    // Handle WebSocket updates
    useEffect(() => {
        if (lastMessage) {
            // Refresh status when any update is received
            fetchStatus();
        }
    }, [lastMessage]);

    const fetchStatus = async () => {
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/status`);
            if (!response.ok) {
                throw new Error('Failed to fetch status');
            }
            const data = await response.json();
            setStatus(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="space-y-8 animate-fade-up">
                {/* Header skeleton */}
                <div className="flex justify-between items-center">
                    <div>
                        <Skeleton height={40} className="w-64 mb-2" />
                        <Skeleton height={16} className="w-20" />
                    </div>
                    <Skeleton width={120} height={24} />
                </div>

                {/* Stats skeleton */}
                <DashboardStatsSkeleton />

                {/* Progress ring skeleton */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ProgressRingSkeleton />
                    <ProgressRingSkeleton />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="card-claim p-6 border-l-4 border-l-[var(--danger-rust)]">
                <h3 className="font-display text-lg font-semibold text-[var(--danger-rust)] mb-2">Connection Error</h3>
                <p className="text-[var(--neutral-slate)] mb-4">{error}</p>
                <button
                    onClick={fetchStatus}
                    className="btn-gold"
                >
                    Retry Connection
                </button>
            </div>
        );
    }

    if (!status) {
        return (
            <div className="card-claim p-8 text-center">
                <p className="text-[var(--neutral-slate)]">No data available</p>
            </div>
        );
    }

    // Render individual widget based on config
    const renderWidget = (config: WidgetConfig): React.ReactNode => {
        if (!config.visible && !isEditMode) return null;

        switch (config.type) {
            case 'feature-counts':
                return (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-up-delay-1">
                        {/* Total */}
                        <div className="stat-card group">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">Total</p>
                                    <p className="stat-card-value text-[var(--gold-600)] dark:text-[var(--gold-400)]">
                                        {status.feature_counts.total}
                                    </p>
                                </div>
                                <div className="p-2 rounded-lg bg-[var(--gold-100)] dark:bg-[var(--gold-900)]/30">
                                    <DocumentTextIcon className="w-5 h-5 text-[var(--gold-600)] dark:text-[var(--gold-400)]" />
                                </div>
                            </div>
                        </div>

                        {/* Verified */}
                        <div className="stat-card group">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">Verified</p>
                                    <p className="stat-card-value text-[var(--success-green)]">
                                        {status.feature_counts.verified}
                                    </p>
                                </div>
                                <div className="p-2 rounded-lg bg-[var(--success-light)] dark:bg-green-900/30">
                                    <CheckCircleIcon className="w-5 h-5 text-[var(--success-green)]" />
                                </div>
                            </div>
                        </div>

                        {/* In Progress */}
                        <div className="stat-card group">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">In Progress</p>
                                    <p className="stat-card-value text-[var(--warning-amber)]">
                                        {status.feature_counts.in_progress}
                                    </p>
                                </div>
                                <div className="p-2 rounded-lg bg-[var(--warning-light)] dark:bg-amber-900/30">
                                    <ClockIcon className="w-5 h-5 text-[var(--warning-amber)]" />
                                </div>
                            </div>
                        </div>

                        {/* Blocked */}
                        <div className="stat-card group">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">Blocked</p>
                                    <p className="stat-card-value text-[var(--danger-rust)]">
                                        {status.feature_counts.blocked}
                                    </p>
                                </div>
                                <div className="p-2 rounded-lg bg-[var(--danger-light)] dark:bg-red-900/30">
                                    <ExclamationTriangleIcon className="w-5 h-5 text-[var(--danger-rust)]" />
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case 'progress-ring':
                return (
                    <div className="widget h-full animate-fade-up-delay-2">
                        <h3 className="widget-title">Overall Progress</h3>
                        <div className="flex items-center justify-center gap-8 py-4">
                            <ProgressRing percentage={status.completion_percentage} size={180} strokeWidth={14} />
                            <div className="flex flex-col gap-3">
                                <p className="text-sm text-[var(--neutral-slate)]">
                                    <span className="font-display text-2xl font-bold text-[var(--gold-600)] dark:text-[var(--gold-400)]">
                                        {status.feature_counts.verified}
                                    </span>
                                    <span className="mx-1">/</span>
                                    <span className="font-semibold">{status.feature_counts.total}</span>
                                    <span className="block text-xs mt-1">features verified</span>
                                </p>
                                <div className="space-y-2 mt-2">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-[var(--success-green)]" />
                                        <span className="text-xs text-[var(--neutral-slate)]">{status.feature_counts.verified} Verified</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-[var(--warning-amber)]" />
                                        <span className="text-xs text-[var(--neutral-slate)]">{status.feature_counts.in_progress} In Progress</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-[var(--danger-rust)]" />
                                        <span className="text-xs text-[var(--neutral-slate)]">{status.feature_counts.blocked} Blocked</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            case 'status-chart':
                return (
                    <div className="widget h-full animate-fade-up-delay-2">
                        <h3 className="widget-title">Status Distribution</h3>
                        <div className="flex items-center justify-center py-4">
                            <StatusChart
                                verified={status.feature_counts.verified}
                                inProgress={status.feature_counts.in_progress}
                                blocked={status.feature_counts.blocked}
                                notStarted={status.feature_counts.not_started}
                                size={200}
                                strokeWidth={40}
                                onSegmentClick={(segmentStatus) => {
                                    window.location.href = `/specs?status=${segmentStatus}`;
                                }}
                            />
                        </div>
                    </div>
                );

            case 'session-control':
                return (
                    <div className="animate-fade-up-delay-3">
                        <SessionControl
                            currentSession={status.current_session || status.last_session ? {
                                session_number: (status.current_session || status.last_session)!.id,
                                date: (status.current_session || status.last_session)!.date,
                                focus: (status.current_session || status.last_session)!.focus,
                            } : null}
                            isSessionActive={status.is_session_active ?? (status.last_session !== null)}
                            gitStatus={status.git_status ? {
                                is_clean: status.git_status.is_clean ?? status.git_status.clean ?? true,
                                branch: status.git_status.branch,
                            } : null}
                            onSessionChange={fetchStatus}
                        />
                    </div>
                );

            case 'priority-features':
                return (
                    <div className="widget h-full animate-fade-up-delay-3">
                        <h3 className="widget-title">Priority Features</h3>
                        <div className="space-y-3">
                            {status.priority_features.length > 0 ? (
                                status.priority_features.map((feature, index) => (
                                    <a
                                        key={feature.id}
                                        href={`/task/${feature.id}`}
                                        className="block feature-card group"
                                        style={{ animationDelay: `${(index + 3) * 100}ms` }}
                                    >
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className="font-mono text-sm font-bold text-[var(--gold-700)] dark:text-[var(--gold-400)]">
                                                {feature.id}
                                            </span>
                                            <span className={`status-badge status-${feature.status.replace('-', '')}`}>
                                                {feature.status}
                                            </span>
                                            <span className={`priority-badge priority-${feature.priority}`}>
                                                {feature.priority}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
                                            {feature.description}
                                        </p>
                                    </a>
                                ))
                            ) : (
                                <div className="text-center py-8">
                                    <p className="text-sm text-[var(--neutral-slate)]">No priority features</p>
                                </div>
                            )}
                        </div>
                    </div>
                );

            case 'recent-activity':
                return (
                    <div className="widget h-full animate-fade-up-delay-3">
                        <RecentActivityFeed maxItems={10} showHeader={true} />
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div>
            {/* Header with project info, connection status, and widget controls */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4 mb-8 animate-fade-up">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <h2 className="text-3xl md:text-4xl font-display font-bold text-slate-900 dark:text-white">
                            {status.project_name}
                        </h2>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-[var(--neutral-slate)] bg-[var(--parchment-200)] dark:bg-white/10 px-2 py-0.5 rounded">
                            v{status.project_version}
                        </span>
                        <div className="deco-diamond" />
                        <div className="flex items-center gap-2">
                            <div className={`connection-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                            <span className="text-sm text-[var(--neutral-slate)]">
                                {isConnected ? 'Live' : 'Offline'}
                            </span>
                        </div>
                    </div>
                </div>

                <WidgetGridControls
                    isEditMode={isEditMode}
                    onToggleEditMode={() => setIsEditMode(!isEditMode)}
                    onOpenSettings={() => setShowSettings(true)}
                />
            </div>

            {/* Decorative line under header */}
            <div className="deco-line mb-8" />

            {/* Customizable Widget Grid */}
            <WidgetGrid
                widgets={widgets}
                onWidgetsChange={setWidgets}
                renderWidget={renderWidget}
                isEditMode={isEditMode}
                onEditModeChange={setIsEditMode}
                showSettings={showSettings}
                onShowSettingsChange={setShowSettings}
            />
        </div>
    );
}
