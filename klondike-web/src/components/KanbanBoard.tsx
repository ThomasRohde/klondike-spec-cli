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
    accentColor: string;
    statusClass: string;
}

const columns: Column[] = [
    {
        status: 'not-started',
        title: 'Not Started',
        accentColor: 'var(--neutral-slate)',
        statusClass: 'kanban-column-not-started',
    },
    {
        status: 'in-progress',
        title: 'In Progress',
        accentColor: 'var(--gold-500)',
        statusClass: 'kanban-column-in-progress',
    },
    {
        status: 'blocked',
        title: 'Blocked',
        accentColor: 'var(--danger-rust)',
        statusClass: 'kanban-column-blocked',
    },
    {
        status: 'verified',
        title: 'Verified',
        accentColor: 'var(--success-green)',
        statusClass: 'kanban-column-verified',
    },
];

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
            <div className="space-y-6 animate-fade-up">
                <Skeleton height={40} className="w-48" />
                <div className="flex gap-4 overflow-x-auto pb-4">
                    {columns.map(col => (
                        <div key={col.status} className="flex-shrink-0 w-80">
                            <Skeleton height={48} className="mb-4 rounded-t-xl" />
                            <FeatureListSkeleton count={3} />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="h-full">
            {/* Header */}
            <div className="flex items-center justify-between mb-6 animate-fade-up">
                <div>
                    <h1 className="text-3xl font-display font-bold text-slate-900 dark:text-white">
                        Kanban Board
                    </h1>
                    <p className="text-sm text-[var(--neutral-slate)] mt-1">
                        Drag features to update their status
                    </p>
                </div>
                <div className="flex items-center gap-2 text-sm">
                    <span className="font-mono text-[var(--gold-600)] dark:text-[var(--gold-400)] font-bold">
                        {features.length}
                    </span>
                    <span className="text-[var(--neutral-slate)]">total features</span>
                </div>
            </div>

            {/* Decorative line */}
            <div className="deco-line mb-6" />

            {/* Kanban columns - horizontal scroll on mobile */}
            <div className="flex gap-5 overflow-x-auto pb-4 -mx-4 px-4 snap-x">
                {columns.map((column, colIndex) => {
                    const columnFeatures = getFeaturesByStatus(column.status);
                    return (
                        <div
                            key={column.status}
                            className={`kanban-column ${column.statusClass} flex-shrink-0 w-80 snap-start animate-fade-up`}
                            style={{ animationDelay: `${colIndex * 100}ms` }}
                        >
                            {/* Column header with accent */}
                            <div
                                className="kanban-column-header rounded-t-xl"
                                style={{ borderBottomColor: column.accentColor }}
                            >
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-3 h-3 rounded-full"
                                        style={{ backgroundColor: column.accentColor }}
                                    />
                                    <h2 className="font-display font-semibold text-slate-800 dark:text-slate-200">
                                        {column.title}
                                    </h2>
                                </div>
                                <span
                                    className="text-sm font-mono font-bold px-2.5 py-1 rounded-full"
                                    style={{
                                        backgroundColor: `color-mix(in srgb, ${column.accentColor} 15%, transparent)`,
                                        color: column.accentColor,
                                    }}
                                >
                                    {columnFeatures.length}
                                </span>
                            </div>

                            {/* Cards container with scroll */}
                            <div className="p-3 space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto">
                                {columnFeatures.length === 0 ? (
                                    <div className="text-center py-12">
                                        <div className="deco-diamond mx-auto mb-3 opacity-30" />
                                        <p className="text-sm text-[var(--neutral-slate)]">
                                            No features
                                        </p>
                                    </div>
                                ) : (
                                    columnFeatures.map((feature, index) => (
                                        <div
                                            key={feature.id}
                                            onClick={() => navigate(`/task/${feature.id}`)}
                                            className={`feature-card group ${actionLoading === feature.id ? 'opacity-50 pointer-events-none' : ''}`}
                                            style={{ animationDelay: `${(colIndex * 100) + (index * 50)}ms` }}
                                        >
                                            {/* Feature ID and priority */}
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="font-mono text-sm font-bold text-[var(--gold-700)] dark:text-[var(--gold-400)]">
                                                    {feature.id}
                                                </span>
                                                <span className={`priority-badge priority-${feature.priority}`}>
                                                    {feature.priority}
                                                </span>
                                            </div>

                                            {/* Description */}
                                            <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2 mb-3">
                                                {feature.description}
                                            </p>

                                            {/* Category tag */}
                                            <div className="text-xs text-[var(--neutral-slate)] font-medium uppercase tracking-wider mb-3">
                                                {feature.category}
                                            </div>

                                            {/* Quick actions - appear on hover */}
                                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-3 border-t border-[var(--parchment-200)] dark:border-white/10">
                                                {feature.status === 'not-started' && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleStatusChange(feature.id, 'in-progress'); }}
                                                        className="flex-1 flex items-center justify-center gap-1.5 text-xs py-2 px-3 rounded-lg bg-[var(--gold-100)] dark:bg-[var(--gold-900)]/30 text-[var(--gold-700)] dark:text-[var(--gold-400)] hover:bg-[var(--gold-200)] dark:hover:bg-[var(--gold-900)]/50 transition-colors font-medium btn-press"
                                                    >
                                                        <PlayIcon className="w-3.5 h-3.5" />
                                                        Start
                                                    </button>
                                                )}
                                                {feature.status === 'in-progress' && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleStatusChange(feature.id, 'verified'); }}
                                                        className="flex-1 flex items-center justify-center gap-1.5 text-xs py-2 px-3 rounded-lg bg-[var(--success-light)] dark:bg-green-900/30 text-[var(--success-green)] hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors font-medium btn-press"
                                                    >
                                                        <CheckCircleIcon className="w-3.5 h-3.5" />
                                                        Verify
                                                    </button>
                                                )}
                                                {(feature.status === 'not-started' || feature.status === 'in-progress') && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleStatusChange(feature.id, 'blocked'); }}
                                                        className="flex-1 flex items-center justify-center gap-1.5 text-xs py-2 px-3 rounded-lg bg-[var(--danger-light)] dark:bg-red-900/30 text-[var(--danger-rust)] hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors font-medium btn-press"
                                                    >
                                                        <NoSymbolIcon className="w-3.5 h-3.5" />
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
