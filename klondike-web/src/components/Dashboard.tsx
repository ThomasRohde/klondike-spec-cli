import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { getApiBaseUrl, getWebSocketUrl } from '../utils/api';

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
    last_session: {
        id: number;
        date: string;
        focus: string;
    } | null;
    git_status: {
        is_clean: boolean;
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
            <div className="flex items-center justify-center h-64">
                <div className="text-lg text-gray-600">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">Error: {error}</p>
                <button
                    onClick={fetchStatus}
                    className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!status) {
        return <div>No data available</div>;
    }

    return (
        <div>
            {/* Header with project info and connection status */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900">
                        {status.project_name}
                    </h2>
                    <p className="text-sm text-gray-600">v{status.project_version}</p>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm text-gray-600">
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            </div>

            {/* Feature status cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Features</h3>
                    <p className="text-4xl font-bold text-indigo-600">{status.feature_counts.total}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Verified</h3>
                    <p className="text-4xl font-bold text-green-600">{status.feature_counts.verified}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">In Progress</h3>
                    <p className="text-4xl font-bold text-yellow-600">{status.feature_counts.in_progress}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Blocked</h3>
                    <p className="text-4xl font-bold text-red-600">{status.feature_counts.blocked}</p>
                </div>
            </div>

            {/* Progress bar */}
            <div className="bg-white p-6 rounded-lg shadow mb-8">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Overall Progress</h3>
                <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                        className="bg-indigo-600 h-4 rounded-full transition-all duration-500"
                        style={{ width: `${status.completion_percentage}%` }}
                    />
                </div>
                <p className="text-sm text-gray-600 mt-2">{status.completion_percentage.toFixed(1)}% Complete</p>
            </div>

            {/* Current session */}
            {status.last_session && (
                <div className="bg-white p-6 rounded-lg shadow mb-8">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">Current Session</h3>
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 bg-indigo-100 rounded-full p-3">
                            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-900">Session #{status.last_session.id}</p>
                            <p className="text-sm text-gray-600">{status.last_session.date}</p>
                            <p className="mt-2 text-gray-800">{status.last_session.focus}</p>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Priority features */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">Priority Features</h3>
                    <div className="space-y-4">
                        {status.priority_features.length > 0 ? (
                            status.priority_features.map((feature) => (
                                <div key={feature.id} className="border-l-4 border-indigo-500 pl-4 py-2">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-mono font-semibold text-gray-700">
                                            {feature.id}
                                        </span>
                                        <span className={`text-xs px-2 py-1 rounded ${feature.status === 'verified' ? 'bg-green-100 text-green-800' :
                                            feature.status === 'in-progress' ? 'bg-yellow-100 text-yellow-800' :
                                                feature.status === 'blocked' ? 'bg-red-100 text-red-800' :
                                                    'bg-gray-100 text-gray-800'
                                            }`}>
                                            {feature.status}
                                        </span>
                                        <span className="text-xs text-gray-500">P{feature.priority}</span>
                                    </div>
                                    <p className="text-sm text-gray-800">{feature.description}</p>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-gray-500">No priority features</p>
                        )}
                    </div>
                </div>

                {/* Recent commits */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">Recent Commits</h3>
                    <div className="space-y-3">
                        {status.git_status.recent_commits.slice(0, 5).map((commit) => (
                            <div key={commit.hash} className="border-l-2 border-gray-300 pl-4 py-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-mono text-gray-500">
                                        {commit.hash.slice(0, 7)}
                                    </span>
                                    <span className="text-xs text-gray-500">{commit.date}</span>
                                </div>
                                <p className="text-sm text-gray-800">{commit.message}</p>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="flex items-center gap-2">
                            <span className={`text-sm font-medium ${status.git_status.is_clean ? 'text-green-600' : 'text-yellow-600'
                                }`}>
                                {status.git_status.is_clean ? '✓ Clean' : '⚠ Uncommitted changes'}
                            </span>
                            <span className="text-sm text-gray-500">
                                on <span className="font-mono">{status.git_status.branch}</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
