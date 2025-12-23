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
 * Animated SVG progress ring with percentage display.
 * Color transitions from red (0%) through yellow (50%) to green (100%).
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

    // Calculate color based on percentage (red -> yellow -> green)
    const getColor = (pct: number): string => {
        if (pct <= 0) return '#ef4444'; // red-500
        if (pct >= 100) return '#22c55e'; // green-500

        if (pct <= 50) {
            // Red to yellow (0-50%)
            const ratio = pct / 50;
            const r = 239; // Start with red
            const g = Math.round(68 + (186 - 68) * ratio); // 68 -> 186
            const b = 68 - Math.round(68 * ratio); // 68 -> 0
            return `rgb(${r}, ${g}, ${b})`;
        } else {
            // Yellow to green (50-100%)
            const ratio = (pct - 50) / 50;
            const r = Math.round(239 - (239 - 34) * ratio); // 239 -> 34
            const g = Math.round(186 + (197 - 186) * ratio); // 186 -> 197
            const b = Math.round(0 + (94 - 0) * ratio); // 0 -> 94
            return `rgb(${r}, ${g}, ${b})`;
        }
    };

    const ringColor = getColor(displayPercentage);
    const center = size / 2;

    return (
        <div className={`relative inline-flex items-center justify-center ${className}`}>
            <svg
                width={size}
                height={size}
                className="transform -rotate-90"
            >
                {/* Background ring */}
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    className="text-gray-200 dark:text-gray-700"
                />
                {/* Progress ring */}
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke={ringColor}
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className="transition-all duration-1000 ease-out"
                    style={{
                        filter: 'drop-shadow(0 0 6px rgba(0, 0, 0, 0.1))',
                    }}
                />
            </svg>
            {/* Percentage text in center */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span
                    className="text-3xl font-bold transition-colors duration-500"
                    style={{ color: ringColor }}
                >
                    {displayPercentage.toFixed(1)}%
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Complete
                </span>
            </div>
        </div>
    );
}
