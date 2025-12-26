import { useSyncExternalStore } from 'react';

interface ProgressRingProps {
    percentage: number;
    size?: number;
    strokeWidth?: number;
    className?: string;
}

// Simple store to track if component has mounted (for initial animation)
let hasMounted = false;
const listeners = new Set<() => void>();
function subscribe(callback: () => void) {
    listeners.add(callback);
    return () => listeners.delete(callback);
}
function getSnapshot() {
    return hasMounted;
}
function setMounted() {
    hasMounted = true;
    listeners.forEach(l => l());
}

/**
 * Animated SVG progress ring with gold gradient and percentage display.
 * Uses the Klondike gold-rush color palette for a distinctive look.
 */
export function ProgressRing({
    percentage,
    size = 160,
    strokeWidth = 12,
    className = '',
}: ProgressRingProps) {
    const mounted = useSyncExternalStore(subscribe, getSnapshot, () => false);

    // Schedule mount update after first render
    if (!mounted) {
        // Use queueMicrotask to avoid setState during render
        queueMicrotask(setMounted);
    }

    // Use 0 on first render, then actual percentage
    const displayPercentage = mounted ? percentage : 0;

    // Calculate SVG parameters
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (displayPercentage / 100) * circumference;

    const center = size / 2;

    // Generate unique gradient ID for this instance
    const gradientId = `goldGradient-${size}-${strokeWidth}`;

    return (
        <div className={`progress-ring-container ${className}`}>
            <svg
                width={size}
                height={size}
                className="transform -rotate-90"
            >
                {/* Define the gold gradient */}
                <defs>
                    <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="var(--gold-400)" />
                        <stop offset="50%" stopColor="var(--gold-500)" />
                        <stop offset="100%" stopColor="var(--gold-600)" />
                    </linearGradient>
                    {/* Glow filter */}
                    <filter id={`glow-${gradientId}`} x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                        <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>

                {/* Background ring */}
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    strokeWidth={strokeWidth}
                    className="progress-ring-bg"
                />

                {/* Animated progress ring with gold gradient */}
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke={`url(#${gradientId})`}
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    filter={`url(#glow-${gradientId})`}
                    className="transition-all duration-1000 ease-out"
                    style={{
                        filter: 'drop-shadow(0 0 8px rgba(234, 179, 8, 0.4))',
                    }}
                />

                {/* Decorative end cap indicator */}
                {displayPercentage > 0 && displayPercentage < 100 && (
                    <circle
                        cx={center + radius * Math.cos(((displayPercentage / 100) * 360 - 90) * Math.PI / 180)}
                        cy={center + radius * Math.sin(((displayPercentage / 100) * 360 - 90) * Math.PI / 180)}
                        r={strokeWidth / 3}
                        fill="white"
                        className="transition-all duration-1000 ease-out"
                        style={{
                            filter: 'drop-shadow(0 0 4px rgba(234, 179, 8, 0.6))',
                        }}
                    />
                )}
            </svg>

            {/* Percentage text in center */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span
                    className="font-display text-4xl font-bold gold-gradient-text transition-all duration-500"
                >
                    {displayPercentage.toFixed(1)}%
                </span>
                <span className="text-xs font-medium text-[var(--neutral-slate)] mt-1 uppercase tracking-wider">
                    Complete
                </span>
            </div>
        </div>
    );
}
