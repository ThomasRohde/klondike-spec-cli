import { useState } from 'react';

interface StatusChartProps {
    verified: number;
    inProgress: number;
    blocked: number;
    notStarted: number;
    size?: number;
    strokeWidth?: number;
    onSegmentClick?: (status: string) => void;
    className?: string;
}

interface Segment {
    status: string;
    label: string;
    count: number;
    color: string;
    hoverColor: string;
}

/**
 * Donut chart showing feature status distribution.
 * Hover reveals count/percentage, click filters to status.
 */
export function StatusChart({
    verified,
    inProgress,
    blocked,
    notStarted,
    size = 200,
    strokeWidth = 40,
    onSegmentClick,
    className = '',
}: StatusChartProps) {
    const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);

    const total = verified + inProgress + blocked + notStarted;
    if (total === 0) {
        return (
            <div className={`flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
                <span className="text-gray-400 text-sm">No features</span>
            </div>
        );
    }

    const segments: Segment[] = [
        { status: 'verified', label: 'Verified', count: verified, color: '#22c55e', hoverColor: '#16a34a' },
        { status: 'in-progress', label: 'In Progress', count: inProgress, color: '#eab308', hoverColor: '#ca8a04' },
        { status: 'blocked', label: 'Blocked', count: blocked, color: '#ef4444', hoverColor: '#dc2626' },
        { status: 'not-started', label: 'Not Started', count: notStarted, color: '#6b7280', hoverColor: '#4b5563' },
    ].filter(s => s.count > 0);

    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const center = size / 2;

    // Calculate segment offsets
    let currentOffset = 0;
    const segmentData = segments.map(segment => {
        const percentage = (segment.count / total) * 100;
        const length = (percentage / 100) * circumference;
        const offset = currentOffset;
        currentOffset += length;
        return {
            ...segment,
            percentage,
            length,
            offset: circumference - offset,
            dashArray: `${length} ${circumference - length}`,
        };
    });

    const hoveredData = hoveredSegment
        ? segmentData.find(s => s.status === hoveredSegment)
        : null;

    return (
        <div className={`flex flex-col items-center ${className}`}>
            <div className="relative inline-flex items-center justify-center">
                <svg
                    width={size}
                    height={size}
                    className="transform -rotate-90 overflow-visible"
                    role="img"
                    aria-label={`Status distribution: ${segments.map(s => `${s.label}: ${s.count}`).join(', ')}`}
                >
                    {/* Background circle */}
                    <circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={strokeWidth}
                        className="text-gray-100 dark:text-gray-800"
                    />
                    {/* Segments (render in reverse order so first segment is on top) */}
                    {[...segmentData].reverse().map(segment => (
                        <circle
                            key={segment.status}
                            cx={center}
                            cy={center}
                            r={radius}
                            fill="none"
                            stroke={hoveredSegment === segment.status ? segment.hoverColor : segment.color}
                            strokeWidth={strokeWidth}
                            strokeDasharray={segment.dashArray}
                            strokeDashoffset={segment.offset}
                            className="transition-all duration-300 cursor-pointer"
                            style={{
                                filter: hoveredSegment === segment.status
                                    ? 'drop-shadow(0 0 8px rgba(0, 0, 0, 0.3))'
                                    : 'none',
                                transform: hoveredSegment === segment.status
                                    ? 'scale(1.02)'
                                    : 'scale(1)',
                                transformOrigin: 'center',
                            }}
                            onMouseEnter={() => setHoveredSegment(segment.status)}
                            onMouseLeave={() => setHoveredSegment(null)}
                            onClick={() => onSegmentClick?.(segment.status)}
                            role="button"
                            aria-label={`${segment.label}: ${segment.count} features (${segment.percentage.toFixed(1)}%)`}
                            tabIndex={0}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    onSegmentClick?.(segment.status);
                                }
                            }}
                        />
                    ))}
                </svg>
                {/* Center content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    {hoveredData ? (
                        <>
                            <span
                                className="text-2xl font-bold transition-all duration-200"
                                style={{ color: hoveredData.color }}
                            >
                                {hoveredData.count}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                {hoveredData.label}
                            </span>
                            <span className="text-xs text-gray-400 dark:text-gray-500">
                                {hoveredData.percentage.toFixed(1)}%
                            </span>
                        </>
                    ) : (
                        <>
                            <span className="text-2xl font-bold text-gray-700 dark:text-gray-200">
                                {total}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                Total
                            </span>
                        </>
                    )}
                </div>
            </div>
            {/* Legend */}
            <div className="mt-3 flex flex-wrap justify-center gap-3">
                {segments.map(segment => (
                    <button
                        key={segment.status}
                        className="flex items-center gap-1 text-xs hover:opacity-80 transition-opacity"
                        onClick={() => onSegmentClick?.(segment.status)}
                        onMouseEnter={() => setHoveredSegment(segment.status)}
                        onMouseLeave={() => setHoveredSegment(null)}
                    >
                        <div
                            className="w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: segment.color }}
                        />
                        <span className="text-gray-600 dark:text-gray-400">
                            {segment.label}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
}
