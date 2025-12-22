import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { getApiBaseUrl, getWebSocketUrl } from '../utils/api';
import { ProgressRing } from './ProgressRing';
import { SessionControl } from './SessionControl';
import { StatusChart } from './StatusChart';
import { RecentActivityFeed } from './RecentActivityFeed';
import { DashboardStatsSkeleton, ProgressRingSkeleton, Skeleton } from './Skeleton';
import { WidgetGrid, WidgetGridControls, useWidgetLayout, type WidgetConfig } from './WidgetGrid';

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
            <div className="space-y-8">
                {/* Header skeleton */}
                <div className="flex justify-between items-center">
                    <div>
                        <Skeleton height={36} className="w-48 mb-2" />
                        <Skeleton height={16} className="w-16" />
                    </div>
                    <Skeleton width={100} height={20} />
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
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-red-800 dark:text-red-400">Error: {error}</p>
                <button
                    onClick={fetchStatus}
                    className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!status) {
        return <div>No data available</div>;
    }

    // Render individual widget based on config
    const renderWidget = (config: WidgetConfig): React.ReactNode => {
        if (!config.visible && !isEditMode) return null;
        
        switch (config.type) {
            case 'feature-counts':
                return (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Total</h3>
                            <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{status.feature_counts.total}</p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Verified</h3>
                            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{status.feature_counts.verified}</p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">In Progress</h3>
                            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{status.feature_counts.in_progress}</p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Blocked</h3>
                            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{status.feature_counts.blocked}</p>
                        </div>
                    </div>
                );
            
            case 'progress-ring':
                return (
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-full">
                        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Overall Progress</h3>
                        <div className="flex items-center justify-center gap-8">
                            <ProgressRing percentage={status.completion_percentage} size={160} strokeWidth={12} />
                            <div className="flex flex-col gap-2">
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {status.feature_counts.verified} of {status.feature_counts.total} features verified
                                </p>
                                <div className="flex flex-col gap-1 mt-2">
                                    <div className="flex items-center gap-1">
                                        <div className="w-3 h-3 rounded-full bg-green-500" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">{status.feature_counts.verified} Verified</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <div className="w-3 h-3 rounded-full bg-yellow-500" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">{status.feature_counts.in_progress} In Progress</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <div className="w-3 h-3 rounded-full bg-red-500" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">{status.feature_counts.blocked} Blocked</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            
            case 'status-chart':
                return (
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-full">
                        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Status Distribution</h3>
                        <div className="flex items-center justify-center pb-8">
                            <StatusChart
                                verified={status.feature_counts.verified}
                                inProgress={status.feature_counts.in_progress}
                                blocked={status.feature_counts.blocked}
                                notStarted={status.feature_counts.not_started}
                                size={180}
                                strokeWidth={35}
                                onSegmentClick={(segmentStatus) => {
                                    window.location.href = `/features?status=${segmentStatus}`;
                                }}
                            />
                        </div>
                    </div>
                );
            
            case 'session-control':
                return (
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
                );
            
            case 'priority-features':
                return (
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-full">
                        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Priority Features</h3>
                        <div className="space-y-4">
                            {status.priority_features.length > 0 ? (
                                status.priority_features.map((feature) => (
                                    <div key={feature.id} className="border-l-4 border-indigo-500 pl-4 py-2">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-sm font-mono font-semibold text-gray-700 dark:text-gray-300">
                                                {feature.id}
                                            </span>
                                            <span className={`text-xs px-2 py-1 rounded ${feature.status === 'verified' ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-400' :
                                                feature.status === 'in-progress' ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-400' :
                                                    feature.status === 'blocked' ? 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-400' :
                                                        'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                                            }`}>
                                                {feature.status}
                                            </span>
                                            <span className="text-xs text-gray-500 dark:text-gray-400">P{feature.priority}</span>
                                        </div>
                                        <p className="text-sm text-gray-800 dark:text-gray-200">{feature.description}</p>
                                    </div>
                                ))
                            ) : (
                                <p className="text-sm text-gray-500 dark:text-gray-400">No priority features</p>
                            )}
                        </div>
                    </div>
                );
            
            case 'recent-activity':
                return <RecentActivityFeed maxItems={10} />;
            
            default:
                return null;
        }
    };

    return (
        <div>
            {/* Header with project info, connection status, and widget controls */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                        {status.project_name}
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">v{status.project_version}</p>
                </div>
                <div className="flex items-center gap-4">
                    <WidgetGridControls
                        isEditMode={isEditMode}
                        onToggleEditMode={() => setIsEditMode(!isEditMode)}
                        onOpenSettings={() => setShowSettings(!showSettings)}
                    />
                    <div className="flex items-center gap-2">
                        <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                            {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Customizable Widget Grid */}
            <WidgetGrid
                widgets={widgets}
                onWidgetsChange={setWidgets}
                renderWidget={renderWidget}
                isEditMode={isEditMode}
                onEditModeChange={setIsEditMode}
            />
        </div>
    );
}
