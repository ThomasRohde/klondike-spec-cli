/**
 * Session timer widget showing elapsed time and activity
 */

import { useEffect, useState, useSyncExternalStore } from 'react';

interface SessionInfo {
    sessionNumber: number;
    focus: string;
    startTime: Date;
    isActive: boolean;
}

// Timer store for shared session state
interface TimerStore {
    session: SessionInfo | null;
    elapsedSeconds: number;
}

const store: TimerStore = {
    session: null,
    elapsedSeconds: 0,
};

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

function getSnapshot() {
    return store;
}

function emitChange() {
    listeners.forEach(listener => listener());
}

let timerInterval: ReturnType<typeof setInterval> | null = null;

export function setSessionInfo(session: SessionInfo | null) {
    store.session = session;
    store.elapsedSeconds = 0;
    
    // Clear existing interval
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    // Start new timer if session is active
    if (session?.isActive) {
        store.elapsedSeconds = Math.floor((Date.now() - session.startTime.getTime()) / 1000);
        
        timerInterval = setInterval(() => {
            if (store.session) {
                store.elapsedSeconds = Math.floor((Date.now() - store.session.startTime.getTime()) / 1000);
                emitChange();
            }
        }, 1000);
    }
    
    emitChange();
}

export function useTimerStore() {
    return useSyncExternalStore(subscribe, getSnapshot);
}

function formatElapsedTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    }
    if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
}

function formatCompactTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    const pad = (n: number) => n.toString().padStart(2, '0');
    
    if (hours > 0) {
        return `${hours}:${pad(minutes)}:${pad(secs)}`;
    }
    return `${minutes}:${pad(secs)}`;
}

interface SessionTimerWidgetProps {
    variant?: 'full' | 'compact' | 'minimal';
    className?: string;
}

export function SessionTimerWidget({ variant = 'full', className = '' }: SessionTimerWidgetProps) {
    const timerStore = useTimerStore();
    const [isBlinking, setIsBlinking] = useState(false);
    
    // Blink effect every second
    useEffect(() => {
        if (timerStore.session?.isActive) {
            const blinkInterval = setInterval(() => {
                setIsBlinking(prev => !prev);
            }, 1000);
            return () => clearInterval(blinkInterval);
        }
    }, [timerStore.session?.isActive]);
    
    if (!timerStore.session?.isActive) {
        if (variant === 'minimal') {
            return (
                <div className={`flex items-center gap-1 text-gray-400 ${className}`}>
                    <div className="w-2 h-2 rounded-full bg-gray-400" />
                    <span className="text-xs">No session</span>
                </div>
            );
        }
        
        return (
            <div className={`bg-gray-100 dark:bg-gray-800 rounded-lg p-4 ${className}`}>
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-medium">No active session</span>
                </div>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Start a session to track time
                </p>
            </div>
        );
    }
    
    const { session, elapsedSeconds } = timerStore;
    
    if (variant === 'minimal') {
        return (
            <div className={`flex items-center gap-2 ${className}`}>
                <div className={`w-2 h-2 rounded-full ${isBlinking ? 'bg-green-500' : 'bg-green-400'} transition-colors`} />
                <span className="text-xs font-mono text-gray-700 dark:text-gray-300">
                    {formatCompactTime(elapsedSeconds)}
                </span>
            </div>
        );
    }
    
    if (variant === 'compact') {
        return (
            <div className={`flex items-center gap-3 bg-green-50 dark:bg-green-900/30 rounded-lg px-3 py-2 ${className}`}>
                <div className={`w-2 h-2 rounded-full ${isBlinking ? 'bg-green-500' : 'bg-green-400'} transition-colors`} />
                <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                        Session #{session.sessionNumber}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {session.focus}
                    </div>
                </div>
                <div className="text-lg font-mono font-bold text-green-600 dark:text-green-400">
                    {formatCompactTime(elapsedSeconds)}
                </div>
            </div>
        );
    }
    
    // Full variant
    return (
        <div className={`bg-white dark:bg-gray-800 rounded-lg shadow p-4 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${isBlinking ? 'bg-green-500' : 'bg-green-400'} transition-colors`} />
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Active Session
                    </h3>
                </div>
                <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-600 dark:text-gray-400">
                    #{session.sessionNumber}
                </span>
            </div>
            
            {/* Timer Display */}
            <div className="text-center mb-3">
                <div className="text-3xl font-mono font-bold text-gray-900 dark:text-white">
                    {formatElapsedTime(elapsedSeconds)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Started {session.startTime.toLocaleTimeString()}
                </div>
            </div>
            
            {/* Focus */}
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Focus</div>
                <div className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {session.focus}
                </div>
            </div>
            
            {/* Activity indicators */}
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 dark:text-gray-400">Session Status</span>
                    <span className="text-green-600 dark:text-green-400 font-medium flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Recording
                    </span>
                </div>
            </div>
        </div>
    );
}

// Hook to automatically sync session info from API data
export function useSessionTimer(sessionData: { session_number?: number; focus?: string; started_at?: string } | null | undefined) {
    useEffect(() => {
        if (sessionData?.session_number && sessionData.focus && sessionData.started_at) {
            setSessionInfo({
                sessionNumber: sessionData.session_number,
                focus: sessionData.focus,
                startTime: new Date(sessionData.started_at),
                isActive: true,
            });
        } else {
            setSessionInfo(null);
        }
        
        return () => {
            // Cleanup on unmount - don't clear session as it may be used elsewhere
        };
    }, [sessionData?.session_number, sessionData?.focus, sessionData?.started_at]);
}
