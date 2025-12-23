/**
 * Feature timeline visualization showing project history
 */

import { useState, useEffect, useMemo } from 'react';
import {
    CheckCircleIcon,
    PlayIcon,
    NoSymbolIcon,
    ClockIcon,
    CodeBracketIcon,
    CalendarIcon,
    FunnelIcon,
    ChevronDownIcon,
    ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { getApiBaseUrl } from '../utils/api';
import { Skeleton } from './Skeleton';

// Timeline event types
interface TimelineEvent {
    id: string;
    type: 'feature-verified' | 'feature-started' | 'feature-blocked' | 'session-start' | 'session-end' | 'commit';
    timestamp: string;
    title: string;
    description?: string;
    metadata?: Record<string, string>;
}

interface SessionData {
    sessionNumber: number;
    focus: string;
    startedAt: string;
    endedAt?: string;
    summary?: string;
}

interface FeatureData {
    id: string;
    description: string;
    status: string;
    verifiedAt?: string;
    lastWorkedOn?: string;
}

interface CommitData {
    hash: string;
    author: string;
    date: string;
    message: string;
}

// Group events by date
function groupEventsByDate(events: TimelineEvent[]): Map<string, TimelineEvent[]> {
    const groups = new Map<string, TimelineEvent[]>();

    for (const event of events) {
        const date = new Date(event.timestamp).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });

        if (!groups.has(date)) {
            groups.set(date, []);
        }
        groups.get(date)!.push(event);
    }

    return groups;
}

// Event icon component
function EventIcon({ type }: { type: TimelineEvent['type'] }) {
    const iconClass = 'w-4 h-4';

    switch (type) {
        case 'feature-verified':
            return <CheckCircleIcon className={`${iconClass} text-green-500`} />;
        case 'feature-started':
            return <PlayIcon className={`${iconClass} text-blue-500`} />;
        case 'feature-blocked':
            return <NoSymbolIcon className={`${iconClass} text-red-500`} />;
        case 'session-start':
        case 'session-end':
            return <ClockIcon className={`${iconClass} text-purple-500`} />;
        case 'commit':
            return <CodeBracketIcon className={`${iconClass} text-gray-500`} />;
        default:
            return <CalendarIcon className={`${iconClass} text-gray-400`} />;
    }
}

// Event background color
function getEventBgColor(type: TimelineEvent['type']): string {
    switch (type) {
        case 'feature-verified':
            return 'bg-green-100 dark:bg-green-900/30 border-green-200 dark:border-green-800';
        case 'feature-started':
            return 'bg-blue-100 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800';
        case 'feature-blocked':
            return 'bg-red-100 dark:bg-red-900/30 border-red-200 dark:border-red-800';
        case 'session-start':
        case 'session-end':
            return 'bg-purple-100 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800';
        case 'commit':
            return 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
        default:
            return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
    }
}

// Individual timeline event
interface TimelineEventCardProps {
    event: TimelineEvent;
    isExpanded: boolean;
    onToggle: () => void;
}

function TimelineEventCard({ event, isExpanded, onToggle }: TimelineEventCardProps) {
    const time = new Date(event.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
    });

    return (
        <div className={`relative flex gap-4 pb-6 last:pb-0`}>
            {/* Timeline connector */}
            <div className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getEventBgColor(event.type)} border`}>
                    <EventIcon type={event.type} />
                </div>
                <div className="flex-1 w-px bg-gray-200 dark:bg-gray-700 mt-2" />
            </div>

            {/* Event content */}
            <div className="flex-1 min-w-0">
                <div
                    className={`rounded-lg border p-3 cursor-pointer transition-colors hover:shadow-sm ${getEventBgColor(event.type)}`}
                    onClick={onToggle}
                >
                    <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {event.title}
                                </span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {time}
                                </span>
                            </div>
                            {event.description && !isExpanded && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 truncate mt-1">
                                    {event.description}
                                </p>
                            )}
                        </div>
                        {(event.description ?? event.metadata) && (
                            <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                                {isExpanded ? (
                                    <ChevronDownIcon className="w-4 h-4" />
                                ) : (
                                    <ChevronRightIcon className="w-4 h-4" />
                                )}
                            </button>
                        )}
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
                            {event.description && (
                                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                    {event.description}
                                </p>
                            )}
                            {event.metadata && Object.keys(event.metadata).length > 0 && (
                                <div className="mt-2 space-y-1">
                                    {Object.entries(event.metadata).map(([key, value]) => (
                                        <div key={key} className="flex items-center gap-2 text-xs">
                                            <span className="text-gray-500 dark:text-gray-400 capitalize">
                                                {key.replace(/_/g, ' ')}:
                                            </span>
                                            <span className="text-gray-700 dark:text-gray-300 font-mono">
                                                {value}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Date group header
function DateHeader({ date }: { date: string }) {
    return (
        <div className="sticky top-0 z-10 bg-gray-50/95 dark:bg-gray-900/95 backdrop-blur-sm py-2 px-4 -mx-4 mb-4">
            <div className="flex items-center gap-2">
                <CalendarIcon className="w-4 h-4 text-gray-400" />
                <span className="font-medium text-gray-700 dark:text-gray-300">
                    {date}
                </span>
            </div>
        </div>
    );
}

// Date range filter
interface DateRangeFilterProps {
    startDate: string;
    endDate: string;
    onStartChange: (date: string) => void;
    onEndChange: (date: string) => void;
    eventTypes: TimelineEvent['type'][];
    selectedTypes: TimelineEvent['type'][];
    onTypeToggle: (type: TimelineEvent['type']) => void;
}

function DateRangeFilter({
    startDate,
    endDate,
    onStartChange,
    onEndChange,
    eventTypes,
    selectedTypes,
    onTypeToggle,
}: DateRangeFilterProps) {
    const typeLabels: Record<TimelineEvent['type'], string> = {
        'feature-verified': 'Verified',
        'feature-started': 'Started',
        'feature-blocked': 'Blocked',
        'session-start': 'Session Start',
        'session-end': 'Session End',
        'commit': 'Commits',
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
            <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                    <FunnelIcon className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters</span>
                </div>

                <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600 dark:text-gray-400">From:</label>
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => onStartChange(e.target.value)}
                        className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                </div>

                <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600 dark:text-gray-400">To:</label>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => onEndChange(e.target.value)}
                        className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                </div>

                <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" />

                <div className="flex flex-wrap gap-2">
                    {eventTypes.map((type) => (
                        <button
                            key={type}
                            onClick={() => onTypeToggle(type)}
                            className={`px-2 py-1 text-xs rounded-full transition-colors ${selectedTypes.includes(type)
                                    ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-700'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border border-transparent'
                                }`}
                        >
                            {typeLabels[type]}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

// Main timeline component
export function FeatureTimeline() {
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [selectedTypes, setSelectedTypes] = useState<TimelineEvent['type'][]>([
        'feature-verified',
        'feature-started',
        'feature-blocked',
        'session-start',
        'session-end',
    ]);

    const allEventTypes: TimelineEvent['type'][] = [
        'feature-verified',
        'feature-started',
        'feature-blocked',
        'session-start',
        'session-end',
        'commit',
    ];

    useEffect(() => {
        fetchTimelineData();
    }, []);

    async function fetchTimelineData() {
        setLoading(true);
        const timelineEvents: TimelineEvent[] = [];

        try {
            // Fetch features for verified/started/blocked events
            const featuresRes = await fetch(`${getApiBaseUrl()}/api/features`);
            const featuresData = await featuresRes.json();

            for (const feature of featuresData.features as FeatureData[]) {
                if (feature.verifiedAt) {
                    timelineEvents.push({
                        id: `verified-${feature.id}`,
                        type: 'feature-verified',
                        timestamp: feature.verifiedAt,
                        title: `${feature.id} Verified`,
                        description: feature.description,
                        metadata: { feature_id: feature.id },
                    });
                }

                if (feature.lastWorkedOn && feature.status === 'in-progress') {
                    timelineEvents.push({
                        id: `started-${feature.id}`,
                        type: 'feature-started',
                        timestamp: feature.lastWorkedOn,
                        title: `${feature.id} Started`,
                        description: feature.description,
                        metadata: { feature_id: feature.id },
                    });
                }

                if (feature.status === 'blocked' && feature.lastWorkedOn) {
                    timelineEvents.push({
                        id: `blocked-${feature.id}`,
                        type: 'feature-blocked',
                        timestamp: feature.lastWorkedOn,
                        title: `${feature.id} Blocked`,
                        description: feature.description,
                        metadata: { feature_id: feature.id },
                    });
                }
            }

            // Fetch sessions
            const progressRes = await fetch(`${getApiBaseUrl()}/api/progress`);
            const progressData = await progressRes.json();

            for (const session of progressData.sessions as SessionData[]) {
                timelineEvents.push({
                    id: `session-start-${session.sessionNumber}`,
                    type: 'session-start',
                    timestamp: session.startedAt,
                    title: `Session #${session.sessionNumber} Started`,
                    description: session.focus,
                    metadata: { session: String(session.sessionNumber) },
                });

                if (session.endedAt) {
                    timelineEvents.push({
                        id: `session-end-${session.sessionNumber}`,
                        type: 'session-end',
                        timestamp: session.endedAt,
                        title: `Session #${session.sessionNumber} Ended`,
                        description: session.summary,
                        metadata: { session: String(session.sessionNumber) },
                    });
                }
            }

            // Fetch commits
            const commitsRes = await fetch(`${getApiBaseUrl()}/api/commits?count=50`);
            const commitsData = await commitsRes.json();

            for (const commit of commitsData as CommitData[]) {
                timelineEvents.push({
                    id: `commit-${commit.hash}`,
                    type: 'commit',
                    timestamp: commit.date,
                    title: commit.message.split('\n')[0].substring(0, 60),
                    description: commit.message,
                    metadata: { hash: commit.hash.substring(0, 7), author: commit.author },
                });
            }

            // Sort by timestamp descending (most recent first)
            timelineEvents.sort((a, b) =>
                new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
            );

            setEvents(timelineEvents);
        } catch (error) {
            console.error('Failed to fetch timeline data:', error);
        } finally {
            setLoading(false);
        }
    }

    // Filter events
    const filteredEvents = useMemo(() => {
        return events.filter((event) => {
            // Type filter
            if (!selectedTypes.includes(event.type)) return false;

            // Date range filter
            const eventDate = new Date(event.timestamp);
            if (startDate && eventDate < new Date(startDate)) return false;
            if (endDate && eventDate > new Date(endDate + 'T23:59:59')) return false;

            return true;
        });
    }, [events, selectedTypes, startDate, endDate]);

    // Group by date
    const groupedEvents = useMemo(() =>
        groupEventsByDate(filteredEvents),
        [filteredEvents]
    );

    function toggleEvent(id: string) {
        setExpandedEvents((prev) => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    }

    function toggleType(type: TimelineEvent['type']) {
        setSelectedTypes((prev) => {
            if (prev.includes(type)) {
                return prev.filter((t) => t !== type);
            }
            return [...prev, type];
        });
    }

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <Skeleton width={200} height={32} />
                </div>
                <Skeleton height={60} />
                <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="flex gap-4">
                            <Skeleton width={32} height={32} rounded="full" />
                            <Skeleton height={80} className="flex-1" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                    Timeline
                </h2>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                    {filteredEvents.length} events
                </div>
            </div>

            <DateRangeFilter
                startDate={startDate}
                endDate={endDate}
                onStartChange={setStartDate}
                onEndChange={setEndDate}
                eventTypes={allEventTypes}
                selectedTypes={selectedTypes}
                onTypeToggle={toggleType}
            />

            {filteredEvents.length === 0 ? (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <CalendarIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No events match your filters</p>
                </div>
            ) : (
                <div className="space-y-6">
                    {Array.from(groupedEvents.entries()).map(([date, dateEvents]) => (
                        <div key={date}>
                            <DateHeader date={date} />
                            <div className="pl-4">
                                {dateEvents.map((event) => (
                                    <TimelineEventCard
                                        key={event.id}
                                        event={event}
                                        isExpanded={expandedEvents.has(event.id)}
                                        onToggle={() => toggleEvent(event.id)}
                                    />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
