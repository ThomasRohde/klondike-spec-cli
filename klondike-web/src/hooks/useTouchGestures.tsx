/* eslint-disable react-refresh/only-export-components */
import { useState, useRef, useCallback } from 'react';

interface SwipeState {
    startX: number;
    startY: number;
    currentX: number;
    currentY: number;
    isSwiping: boolean;
}

interface UseSwipeOptions {
    threshold?: number;       // Min distance to trigger swipe (default: 50px)
    preventScroll?: boolean;  // Prevent vertical scrolling during horizontal swipe
    onSwipeLeft?: () => void;
    onSwipeRight?: () => void;
}

interface SwipeHandlers {
    onTouchStart: (e: React.TouchEvent) => void;
    onTouchMove: (e: React.TouchEvent) => void;
    onTouchEnd: (e: React.TouchEvent) => void;
}

interface UseSwipeReturn {
    handlers: SwipeHandlers;
    offset: number;
    isSwiping: boolean;
    direction: 'left' | 'right' | null;
}

/**
 * Hook for handling swipe gestures on mobile.
 */
export function useSwipe(options: UseSwipeOptions = {}): UseSwipeReturn {
    const { threshold = 50, preventScroll = true, onSwipeLeft, onSwipeRight } = options;

    const [offset, setOffset] = useState(0);
    const [isSwiping, setIsSwiping] = useState(false);
    const [direction, setDirection] = useState<'left' | 'right' | null>(null);
    const stateRef = useRef<SwipeState>({
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0,
        isSwiping: false,
    });

    const handleTouchStart = useCallback((e: React.TouchEvent) => {
        const touch = e.touches[0];
        stateRef.current = {
            startX: touch.clientX,
            startY: touch.clientY,
            currentX: touch.clientX,
            currentY: touch.clientY,
            isSwiping: false,
        };
    }, []);

    const handleTouchMove = useCallback((e: React.TouchEvent) => {
        const touch = e.touches[0];
        const state = stateRef.current;

        state.currentX = touch.clientX;
        state.currentY = touch.clientY;

        const deltaX = state.currentX - state.startX;
        const deltaY = state.currentY - state.startY;

        // Determine if this is a horizontal swipe
        if (!state.isSwiping) {
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
                state.isSwiping = true;
                setIsSwiping(true);
            }
        }

        if (state.isSwiping) {
            if (preventScroll) {
                e.preventDefault();
            }
            setOffset(deltaX);
            setDirection(deltaX > 0 ? 'right' : 'left');
        }
    }, [preventScroll]);

    const handleTouchEnd = useCallback(() => {
        const state = stateRef.current;
        const deltaX = state.currentX - state.startX;

        if (Math.abs(deltaX) > threshold) {
            if (deltaX > 0 && onSwipeRight) {
                onSwipeRight();
            } else if (deltaX < 0 && onSwipeLeft) {
                onSwipeLeft();
            }
        }

        // Reset
        setOffset(0);
        setIsSwiping(false);
        setDirection(null);
        stateRef.current.isSwiping = false;
    }, [threshold, onSwipeLeft, onSwipeRight]);

    return {
        handlers: {
            onTouchStart: handleTouchStart,
            onTouchMove: handleTouchMove,
            onTouchEnd: handleTouchEnd,
        },
        offset,
        isSwiping,
        direction,
    };
}

interface UsePullToRefreshOptions {
    onRefresh: () => Promise<void>;
    threshold?: number;  // Pull distance to trigger refresh (default: 100px)
    disabled?: boolean;
}

interface UsePullToRefreshReturn {
    handlers: {
        onTouchStart: (e: React.TouchEvent) => void;
        onTouchMove: (e: React.TouchEvent) => void;
        onTouchEnd: () => void;
    };
    pullDistance: number;
    isRefreshing: boolean;
    isPulling: boolean;
}

/**
 * Hook for pull-to-refresh gesture.
 */
export function usePullToRefresh(options: UsePullToRefreshOptions): UsePullToRefreshReturn {
    const { onRefresh, threshold = 100, disabled = false } = options;

    const [pullDistance, setPullDistance] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isPulling, setIsPulling] = useState(false);
    const startY = useRef(0);
    const containerRef = useRef<HTMLElement | null>(null);

    const handleTouchStart = useCallback((e: React.TouchEvent) => {
        if (disabled || isRefreshing) return;

        // Only enable if at top of scroll
        const target = e.target as HTMLElement;
        containerRef.current = target.closest('[data-pull-refresh]') || target;

        if (containerRef.current.scrollTop === 0) {
            startY.current = e.touches[0].clientY;
            setIsPulling(true);
        }
    }, [disabled, isRefreshing]);

    const handleTouchMove = useCallback((e: React.TouchEvent) => {
        if (!isPulling || disabled || isRefreshing) return;

        const currentY = e.touches[0].clientY;
        const distance = currentY - startY.current;

        if (distance > 0) {
            // Apply resistance to pull
            const resistedDistance = Math.min(distance * 0.5, threshold * 1.5);
            setPullDistance(resistedDistance);
        }
    }, [isPulling, disabled, isRefreshing, threshold]);

    const handleTouchEnd = useCallback(async () => {
        if (!isPulling || disabled) return;

        setIsPulling(false);

        if (pullDistance >= threshold) {
            setIsRefreshing(true);
            setPullDistance(threshold * 0.5); // Show spinner at half height

            try {
                await onRefresh();
            } finally {
                setIsRefreshing(false);
                setPullDistance(0);
            }
        } else {
            setPullDistance(0);
        }
    }, [isPulling, disabled, pullDistance, threshold, onRefresh]);

    return {
        handlers: {
            onTouchStart: handleTouchStart,
            onTouchMove: handleTouchMove,
            onTouchEnd: handleTouchEnd,
        },
        pullDistance,
        isRefreshing,
        isPulling,
    };
}

interface PullToRefreshIndicatorProps {
    pullDistance: number;
    isRefreshing: boolean;
    threshold: number;
}

/**
 * Visual indicator for pull-to-refresh.
 */
export function PullToRefreshIndicator({
    pullDistance,
    isRefreshing,
    threshold
}: PullToRefreshIndicatorProps) {
    if (pullDistance === 0 && !isRefreshing) return null;

    const progress = Math.min(pullDistance / threshold, 1);
    const rotation = isRefreshing ? 'animate-spin' : '';

    return (
        <div
            className="flex items-center justify-center py-2 transition-all duration-200"
            style={{ height: pullDistance }}
        >
            <div
                className={`w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full ${rotation}`}
                style={{
                    opacity: progress,
                    transform: `scale(${0.5 + progress * 0.5})`
                }}
            />
        </div>
    );
}

/**
 * Check if the device supports touch events.
 */
export function useIsTouchDevice(): boolean {
    const [isTouch] = useState(() => 'ontouchstart' in window || navigator.maxTouchPoints > 0);
    return isTouch;
}
