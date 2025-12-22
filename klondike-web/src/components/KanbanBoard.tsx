import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBaseUrl, apiCall } from '../utils/api';
import { FeatureListSkeleton, Skeleton } from './Skeleton';
import { PlayIcon, CheckCircleIcon, NoSymbolIcon } from '@heroicons/react/24/outline';

interface Feature {
    id: string;
    description: string;
    category: string;
    priority: number;
    status: 'not-started' | 'in-progress' | 'blocked' | 'verified';
}

interface Column {
    status: Feature['status'];
    title: string;
    color: string;
    bgColor: string;
    borderColor: string;
}

const columns: Column[] = [
    { status: 'not-started', title: 'Not Started', color: 'text-gray-600 dark:text-gray-400', bgColor: 'bg-gray-50 dark:bg-gray-800', borderColor: 'border-gray-300 dark:border-gray-600' },
    { status: 'in-progress', title: 'In Progress', color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-50 dark:bg-yellow-900/20', borderColor: 'border-yellow-300 dark:border-yellow-700' },
    { status: 'blocked', title: 'Blocked', color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-50 dark:bg-red-900/20', borderColor: 'border-red-300 dark:border-red-700' },
    { status: 'verified', title: 'Verified', color: 'text-green-600 dark:text-green-400', bgColor: 'bg-green-50 dark:bg-green-900/20', borderColor: 'border-green-300 dark:border-green-700' },
];

const priorityColors: Record<number, string> = {
    1: 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-400',
    2: 'bg-orange-100 dark:bg-orange-900/50 text-orange-700 dark:text-orange-400',
    3: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-400',
    4: 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400',
    5: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400',
};

export function KanbanBoard() {
    const navigate = useNavigate();
    const [features, setFeatures] = useState<Feature[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    useEffect(() => {
        fetchFeatures();
    }, []);

    async function fetchFeatures() {
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/features`);
            const data = await response.json();
            setFeatures(data.features || []);
        } catch (error) {
            console.error('Failed to fetch features:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleStatusChange(featureId: string, newStatus: Feature['status']) {
        setActionLoading(featureId);
        try {
            if (newStatus === 'in-progress') {
                await apiCall(
                    fetch(`${getApiBaseUrl()}/api/features/${featureId}/start`, { method: 'POST' }),
                    { successMessage: `${featureId} started!` }
                );
            } else if (newStatus === 'verified') {
                const evidence = window.prompt('Enter verification evidence:');
                if (!evidence) {
                    setActionLoading(null);
                    return;
                }
                await apiCall(
                    fetch(`${getApiBaseUrl()}/api/features/${featureId}/verify`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ evidence })
                    }),
                    { successMessage: `${featureId} verified!` }
                );
            } else if (newStatus === 'blocked') {
                const reason = window.prompt('Enter block reason:');
                if (!reason) {
                    setActionLoading(null);
                    return;
                }
                await apiCall(
                    fetch(`${getApiBaseUrl()}/api/features/${featureId}/block`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ reason })
                    }),
                    { successMessage: `${featureId} blocked` }
                );
            }
            fetchFeatures();
        } catch {
            // Error toasted by apiCall
        } finally {
            setActionLoading(null);
        }
    }

    function getFeaturesByStatus(status: Feature['status']) {
        return features.filter(f => f.status === status);
    }

    if (loading) {
        return (
            <div className="space-y-6">
                <Skeleton height={32} className="w-48" />
                <div className="flex gap-4 overflow-x-auto pb-4">
                    {columns.map(col => (
                        <div key={col.status} className="flex-shrink-0 w-72">
                            <Skeleton height={40} className="mb-4" />
                            <FeatureListSkeleton count={3} />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="h-full">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Kanban Board</h1>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                    {features.length} total features
                </div>
            </div>

            {/* Kanban columns - horizontal scroll on mobile */}
            <div className="flex gap-4 overflow-x-auto pb-4 -mx-4 px-4">
                {columns.map(column => {
                    const columnFeatures = getFeaturesByStatus(column.status);
                    return (
                        <div
                            key={column.status}
                            className={`flex-shrink-0 w-72 ${column.bgColor} rounded-lg border-2 ${column.borderColor}`}
                        >
                            {/* Column header */}
                            <div className={`px-4 py-3 border-b ${column.borderColor}`}>
                                <div className="flex items-center justify-between">
                                    <h2 className={`font-semibold ${column.color}`}>
                                        {column.title}
                                    </h2>
                                    <span className={`text-sm font-medium ${column.color} bg-white dark:bg-gray-800 px-2 py-0.5 rounded-full`}>
                                        {columnFeatures.length}
                                    </span>
                                </div>
                            </div>

                            {/* Cards container with scroll */}
                            <div className="p-2 space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto">
                                {columnFeatures.length === 0 ? (
                                    <div className="text-center py-8 text-sm text-gray-400 dark:text-gray-500">
                                        No features
                                    </div>
                                ) : (
                                    columnFeatures.map(feature => (
                                        <div
                                            key={feature.id}
                                            onClick={() => navigate(`/task/${feature.id}`)}
                                            className={`group bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3 cursor-pointer hover:shadow-md transition-shadow ${actionLoading === feature.id ? 'opacity-50' : ''}`}
                                        >
                                            {/* Feature ID and priority */}
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="font-mono text-sm font-medium text-gray-900 dark:text-white">
                                                    {feature.id}
                                                </span>
                                                <span className={`text-xs px-1.5 py-0.5 rounded ${priorityColors[feature.priority] || priorityColors[3]}`}>
                                                    P{feature.priority}
                                                </span>
                                            </div>

                                            {/* Description */}
                                            <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-2">
                                                {feature.description}
                                            </p>

                                            {/* Category */}
                                            <div className="text-xs text-gray-400 dark:text-gray-500 mb-2">
                                                {feature.category}
                                            </div>

                                            {/* Quick actions - appear on hover */}
                                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity pt-2 border-t border-gray-100 dark:border-gray-700">
                                                {feature.status === 'not-started' && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleStatusChange(feature.id, 'in-progress'); }}
                                                        className="flex-1 flex items-center justify-center gap-1 text-xs py-1 px-2 rounded bg-blue-50 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors btn-press"
                                                    >
                                                        <PlayIcon className="w-3 h-3" />
                                                        Start
                                                    </button>
                                                )}
                                                {feature.status === 'in-progress' && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleStatusChange(feature.id, 'verified'); }}
                                                        className="flex-1 flex items-center justify-center gap-1 text-xs py-1 px-2 rounded bg-green-50 dark:bg-green-900/50 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900 transition-colors btn-press"
                                                    >
                                                        <CheckCircleIcon className="w-3 h-3" />
                                                        Verify
                                                    </button>
                                                )}
                                                {(feature.status === 'not-started' || feature.status === 'in-progress') && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleStatusChange(feature.id, 'blocked'); }}
                                                        className="flex-1 flex items-center justify-center gap-1 text-xs py-1 px-2 rounded bg-red-50 dark:bg-red-900/50 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 transition-colors btn-press"
                                                    >
                                                        <NoSymbolIcon className="w-3 h-3" />
                                                        Block
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
