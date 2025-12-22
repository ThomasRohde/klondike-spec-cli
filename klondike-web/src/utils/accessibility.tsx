import { useEffect, useRef } from 'react';

/**
 * Live region announcements for screen readers.
 * Creates a visually hidden element that announces changes.
 */
let announcer: HTMLDivElement | null = null;

function getAnnouncer(): HTMLDivElement {
    if (!announcer) {
        announcer = document.createElement('div');
        announcer.setAttribute('role', 'status');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);
    }
    return announcer;
}

/**
 * Announce a message to screen readers.
 * Use for dynamic content changes like status updates.
 */
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
    const el = getAnnouncer();
    el.setAttribute('aria-live', priority);
    // Clear and re-set to trigger announcement
    el.textContent = '';
    setTimeout(() => {
        el.textContent = message;
    }, 100);
}

/**
 * Hook to manage focus when content changes.
 * Returns a ref to attach to the element that should receive focus.
 */
export function useFocusOnMount<T extends HTMLElement>() {
    const ref = useRef<T>(null);
    
    useEffect(() => {
        if (ref.current) {
            ref.current.focus();
        }
    }, []);
    
    return ref;
}

/**
 * Hook to trap focus within a container (for modals).
 */
export function useFocusTrap<T extends HTMLElement>(isActive: boolean) {
    const containerRef = useRef<T>(null);
    
    useEffect(() => {
        if (!isActive || !containerRef.current) return;
        
        const container = containerRef.current;
        const focusableElements = container.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        function handleKeyDown(e: KeyboardEvent) {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
        
        container.addEventListener('keydown', handleKeyDown);
        firstElement.focus();
        
        return () => {
            container.removeEventListener('keydown', handleKeyDown);
        };
    }, [isActive]);
    
    return containerRef;
}

/**
 * Skip link component for keyboard users to bypass navigation.
 */
export function SkipLink({ targetId = 'main-content' }: { targetId?: string }) {
    return (
        <a
            href={`#${targetId}`}
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-indigo-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
            Skip to main content
        </a>
    );
}

/**
 * Visually hidden component for screen reader text.
 */
export function ScreenReaderOnly({ children }: { children: React.ReactNode }) {
    return (
        <span className="sr-only">
            {children}
        </span>
    );
}

/**
 * Status indicator with proper accessibility.
 * Ensures status is communicated via text, not just color.
 */
interface AccessibleStatusProps {
    status: 'not-started' | 'in-progress' | 'blocked' | 'verified';
    showLabel?: boolean;
}

const statusLabels = {
    'not-started': 'Not started',
    'in-progress': 'In progress',
    'blocked': 'Blocked',
    'verified': 'Verified',
};

const statusColors = {
    'not-started': 'bg-gray-400',
    'in-progress': 'bg-blue-500',
    'blocked': 'bg-red-500',
    'verified': 'bg-green-500',
};

export function AccessibleStatus({ status, showLabel = true }: AccessibleStatusProps) {
    return (
        <span className="inline-flex items-center gap-1.5">
            <span
                className={`w-2 h-2 rounded-full ${statusColors[status]}`}
                aria-hidden="true"
            />
            {showLabel ? (
                <span>{statusLabels[status]}</span>
            ) : (
                <span className="sr-only">{statusLabels[status]}</span>
            )}
        </span>
    );
}

/**
 * Priority indicator with proper accessibility.
 * Shows both visual and text indication.
 */
interface AccessiblePriorityProps {
    priority: number;
    showLabel?: boolean;
}

const priorityLabels: Record<number, string> = {
    1: 'Critical priority',
    2: 'High priority',
    3: 'Medium priority',
    4: 'Low priority',
    5: 'Nice to have',
};

export function AccessiblePriority({ priority, showLabel = true }: AccessiblePriorityProps) {
    return (
        <span>
            {showLabel ? (
                <span>P{priority} ({priorityLabels[priority]})</span>
            ) : (
                <>
                    <span aria-hidden="true">P{priority}</span>
                    <span className="sr-only">{priorityLabels[priority]}</span>
                </>
            )}
        </span>
    );
}
