/**
 * Empty state components with illustrations and onboarding hints
 */

import type { ReactNode } from 'react';

interface EmptyStateProps {
    title: string;
    description: string;
    icon?: ReactNode;
    action?: {
        label: string;
        onClick: () => void;
    };
    hint?: string;
    className?: string;
}

export function EmptyState({
    title,
    description,
    icon,
    action,
    hint,
    className = ''
}: EmptyStateProps) {
    return (
        <div className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}>
            {/* Icon/Illustration */}
            {icon && (
                <div className="w-24 h-24 mb-6 text-gray-300 dark:text-gray-600">
                    {icon}
                </div>
            )}

            {/* Title */}
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {title}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-6">
                {description}
            </p>

            {/* Action button */}
            {action && (
                <button
                    onClick={action.onClick}
                    className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
                >
                    {action.label}
                </button>
            )}

            {/* Hint */}
            {hint && (
                <div className="mt-6 text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {hint}
                </div>
            )}
        </div>
    );
}

// Pre-built empty state illustrations as SVG components
export function NoFeaturesIllustration() {
    return (
        <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            {/* Clipboard */}
            <rect x="30" y="20" width="60" height="80" rx="4" stroke="currentColor" strokeWidth="2" />
            <rect x="45" y="12" width="30" height="16" rx="2" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2" />
            <circle cx="60" cy="20" r="3" fill="currentColor" />

            {/* Lines */}
            <line x1="40" y1="45" x2="80" y2="45" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" />
            <line x1="40" y1="60" x2="70" y2="60" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" />
            <line x1="40" y1="75" x2="75" y2="75" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" />

            {/* Plus icon */}
            <circle cx="95" cy="85" r="18" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeWidth="2" />
            <line x1="95" y1="78" x2="95" y2="92" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            <line x1="88" y1="85" x2="102" y2="85" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

export function NoSessionIllustration() {
    return (
        <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            {/* Clock */}
            <circle cx="60" cy="60" r="40" stroke="currentColor" strokeWidth="2" />
            <circle cx="60" cy="60" r="35" stroke="currentColor" strokeWidth="2" strokeDasharray="4 2" />

            {/* Clock hands (paused) */}
            <line x1="60" y1="60" x2="60" y2="35" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            <line x1="60" y1="60" x2="78" y2="60" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            <circle cx="60" cy="60" r="4" fill="currentColor" />

            {/* Pause indicator */}
            <rect x="25" y="88" width="6" height="16" rx="2" fill="currentColor" fillOpacity="0.3" />
            <rect x="35" y="88" width="6" height="16" rx="2" fill="currentColor" fillOpacity="0.3" />
        </svg>
    );
}

export function NoActivityIllustration() {
    return (
        <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            {/* Calendar */}
            <rect x="20" y="30" width="80" height="70" rx="4" stroke="currentColor" strokeWidth="2" />
            <line x1="20" y1="50" x2="100" y2="50" stroke="currentColor" strokeWidth="2" />

            {/* Calendar header decorations */}
            <rect x="35" y="20" width="4" height="20" rx="2" fill="currentColor" />
            <rect x="81" y="20" width="4" height="20" rx="2" fill="currentColor" />

            {/* Empty dots */}
            <circle cx="40" cy="70" r="5" stroke="currentColor" strokeWidth="2" strokeDasharray="3 2" />
            <circle cx="60" cy="70" r="5" stroke="currentColor" strokeWidth="2" strokeDasharray="3 2" />
            <circle cx="80" cy="70" r="5" stroke="currentColor" strokeWidth="2" strokeDasharray="3 2" />
        </svg>
    );
}

export function NoResultsIllustration() {
    return (
        <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            {/* Magnifying glass */}
            <circle cx="50" cy="50" r="25" stroke="currentColor" strokeWidth="2" />
            <line x1="68" y1="68" x2="95" y2="95" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />

            {/* X mark inside */}
            <line x1="40" y1="40" x2="60" y2="60" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            <line x1="60" y1="40" x2="40" y2="60" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}

export function WelcomeIllustration() {
    return (
        <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            {/* Rocket */}
            <path d="M60 20 L80 60 L60 100 L40 60 Z" stroke="currentColor" strokeWidth="2" fill="currentColor" fillOpacity="0.1" />
            <circle cx="60" cy="50" r="8" fill="currentColor" fillOpacity="0.3" />

            {/* Flames */}
            <ellipse cx="60" cy="108" rx="8" ry="6" fill="currentColor" fillOpacity="0.4" />
            <ellipse cx="52" cy="105" rx="4" ry="3" fill="currentColor" fillOpacity="0.3" />
            <ellipse cx="68" cy="105" rx="4" ry="3" fill="currentColor" fillOpacity="0.3" />

            {/* Stars */}
            <circle cx="25" cy="35" r="2" fill="currentColor" />
            <circle cx="95" cy="45" r="2" fill="currentColor" />
            <circle cx="20" cy="80" r="1.5" fill="currentColor" />
            <circle cx="100" cy="70" r="1.5" fill="currentColor" />
        </svg>
    );
}

// Preset empty states for common scenarios
export function EmptyFeaturesState({ onAdd }: { onAdd?: () => void }) {
    return (
        <EmptyState
            title="No features yet"
            description="Start by adding your first feature. Features help you track requirements and their completion status."
            icon={<NoFeaturesIllustration />}
            action={onAdd ? { label: 'Add First Feature', onClick: onAdd } : undefined}
            hint="Use Ctrl+Shift+N to quickly add features from anywhere"
        />
    );
}

export function EmptySessionState({ onStart }: { onStart?: () => void }) {
    return (
        <EmptyState
            title="No active session"
            description="Start a coding session to track your progress and maintain context between work periods."
            icon={<NoSessionIllustration />}
            action={onStart ? { label: 'Start Session', onClick: onStart } : undefined}
            hint="Sessions help agents maintain context across coding sessions"
        />
    );
}

export function EmptyActivityState() {
    return (
        <EmptyState
            title="No recent activity"
            description="Activity will appear here as you work on features, start sessions, and make commits."
            icon={<NoActivityIllustration />}
            hint="Activity is tracked automatically as you use Klondike"
        />
    );
}

export function EmptySearchState({ query }: { query: string }) {
    return (
        <EmptyState
            title="No results found"
            description={`We couldn't find any features matching "${query}". Try adjusting your search or filters.`}
            icon={<NoResultsIllustration />}
            hint="Try using fewer or different keywords"
        />
    );
}

export function WelcomeState({ onGetStarted }: { onGetStarted?: () => void }) {
    return (
        <EmptyState
            title="Welcome to Klondike!"
            description="Klondike helps AI coding agents track features, sessions, and progress. Let's set up your first project."
            icon={<WelcomeIllustration />}
            action={onGetStarted ? { label: 'Get Started', onClick: onGetStarted } : undefined}
            hint="Run 'klondike init' in your project to get started"
        />
    );
}

// Onboarding hints component
interface OnboardingHintProps {
    title: string;
    description: string;
    step?: number;
    totalSteps?: number;
    onDismiss?: () => void;
}

export function OnboardingHint({
    title,
    description,
    step,
    totalSteps,
    onDismiss
}: OnboardingHintProps) {
    return (
        <div className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4 relative">
            {/* Step indicator */}
            {step !== undefined && totalSteps !== undefined && (
                <div className="absolute top-2 right-2 text-xs text-indigo-500 dark:text-indigo-400">
                    Step {step} of {totalSteps}
                </div>
            )}

            {/* Content */}
            <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div className="flex-1">
                    <h4 className="text-sm font-semibold text-indigo-800 dark:text-indigo-200">
                        {title}
                    </h4>
                    <p className="text-sm text-indigo-600 dark:text-indigo-300 mt-1">
                        {description}
                    </p>
                </div>
            </div>

            {/* Dismiss button */}
            {onDismiss && (
                <button
                    onClick={onDismiss}
                    className="absolute bottom-2 right-2 text-xs text-indigo-500 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-200"
                >
                    Dismiss
                </button>
            )}
        </div>
    );
}
