/* eslint-disable react-refresh/only-export-components */
import { useState, useEffect, useCallback, useSyncExternalStore } from 'react';
import {
    CloudIcon,
    CloudArrowDownIcon,
    ExclamationTriangleIcon,
    ArrowPathIcon,
    XMarkIcon,
} from '@heroicons/react/24/outline';

// --- Offline State Store ---
interface OfflineState {
    isOnline: boolean;
    isServiceWorkerReady: boolean;
    hasPendingUpdate: boolean;
    lastSyncTime: Date | null;
}

let offlineState: OfflineState = {
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    isServiceWorkerReady: false,
    hasPendingUpdate: false,
    lastSyncTime: null,
};

const offlineListeners = new Set<() => void>();

function getOfflineSnapshot(): OfflineState {
    return offlineState;
}

function subscribeOffline(listener: () => void): () => void {
    offlineListeners.add(listener);
    return () => offlineListeners.delete(listener);
}

function updateOfflineState(updates: Partial<OfflineState>): void {
    offlineState = { ...offlineState, ...updates };
    offlineListeners.forEach(listener => listener());
}

// --- Service Worker Registration ---
let swRegistration: ServiceWorkerRegistration | null = null;

export async function registerServiceWorker(): Promise<void> {
    if (!('serviceWorker' in navigator)) {
        console.log('[Offline] Service workers not supported');
        return;
    }

    try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
        });

        swRegistration = registration;
        updateOfflineState({ isServiceWorkerReady: true });
        console.log('[Offline] Service worker registered');

        // Check for updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        updateOfflineState({ hasPendingUpdate: true });
                    }
                });
            }
        });

        // Handle controller change (after update applied)
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            updateOfflineState({ hasPendingUpdate: false });
        });
    } catch (error) {
        console.error('[Offline] Service worker registration failed:', error);
    }
}

export function applyServiceWorkerUpdate(): void {
    if (swRegistration?.waiting) {
        swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }
}

export function clearServiceWorkerCache(): void {
    navigator.serviceWorker.controller?.postMessage({ type: 'CLEAR_CACHE' });
}

// --- Network Status Listeners ---
function initializeNetworkListeners(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
        updateOfflineState({ isOnline: true, lastSyncTime: new Date() });
    });

    window.addEventListener('offline', () => {
        updateOfflineState({ isOnline: false });
    });
}

// Initialize on module load
if (typeof window !== 'undefined') {
    initializeNetworkListeners();
}

// --- Hook for Offline State ---
export function useOfflineState() {
    const state = useSyncExternalStore(subscribeOffline, getOfflineSnapshot, getOfflineSnapshot);

    const clearCache = useCallback(() => {
        clearServiceWorkerCache();
    }, []);

    const applyUpdate = useCallback(() => {
        applyServiceWorkerUpdate();
        // Reload to activate new service worker
        window.location.reload();
    }, []);

    return {
        ...state,
        clearCache,
        applyUpdate,
    };
}

// --- Offline Indicator Component ---
interface OfflineIndicatorProps {
    className?: string;
}

// Status dot component (extracted to avoid creating during render)
function StatusDot({
    isOnline,
    isServiceWorkerReady,
    className
}: {
    isOnline: boolean;
    isServiceWorkerReady: boolean;
    className: string
}) {
    return (
        <div
            className={`flex items-center gap-1.5 ${className}`}
            title={isOnline ? 'Online' : 'Offline - Using cached data'}
        >
            {isOnline ? (
                <CloudIcon className="h-4 w-4 text-green-500" />
            ) : (
                <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
            )}
            {!isOnline && (
                <span className="text-xs text-yellow-600 dark:text-yellow-400">Offline</span>
            )}
            {isServiceWorkerReady && isOnline && (
                <CloudArrowDownIcon className="h-3 w-3 text-gray-400" title="Offline support enabled" />
            )}
        </div>
    );
}

export function OfflineIndicator({ className = '' }: OfflineIndicatorProps) {
    const { isOnline, isServiceWorkerReady, hasPendingUpdate, applyUpdate } = useOfflineState();
    const [showBanner, setShowBanner] = useState(false);

    // Show banner when going offline
    useEffect(() => {
        if (!isOnline) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setShowBanner(true);
        } else {
            // Auto-hide after coming back online
            const timer = setTimeout(() => setShowBanner(false), 3000);
            return () => clearTimeout(timer);
        }
    }, [isOnline]);

    return (
        <>
            <StatusDot isOnline={isOnline} isServiceWorkerReady={isServiceWorkerReady} className={className} />

            {/* Offline Banner */}
            {showBanner && !isOnline && (
                <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50">
                    <div className="bg-yellow-50 dark:bg-yellow-900/50 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 shadow-lg">
                        <div className="flex items-start gap-3">
                            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                                    You're offline
                                </h4>
                                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                                    Some features may be limited. Cached data is being displayed.
                                </p>
                            </div>
                            <button
                                onClick={() => setShowBanner(false)}
                                className="p-1 hover:bg-yellow-100 dark:hover:bg-yellow-800 rounded"
                            >
                                <XMarkIcon className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Update Available Banner */}
            {hasPendingUpdate && (
                <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50">
                    <div className="bg-blue-50 dark:bg-blue-900/50 border border-blue-200 dark:border-blue-700 rounded-lg p-4 shadow-lg">
                        <div className="flex items-start gap-3">
                            <ArrowPathIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                                    Update available
                                </h4>
                                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                    A new version is available. Refresh to update.
                                </p>
                            </div>
                            <button
                                onClick={applyUpdate}
                                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                            >
                                Update
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

// --- Offline Status for Settings ---
export function OfflineSettings() {
    const { isOnline, isServiceWorkerReady, lastSyncTime, clearCache } = useOfflineState();
    const [cacheCleared, setCacheCleared] = useState(false);

    const handleClearCache = () => {
        clearCache();
        setCacheCleared(true);
        setTimeout(() => setCacheCleared(false), 3000);
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Offline Support
            </h3>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Network Status</span>
                    <span className={`text-sm font-medium ${isOnline ? 'text-green-600' : 'text-yellow-600'}`}>
                        {isOnline ? 'Online' : 'Offline'}
                    </span>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Service Worker</span>
                    <span className={`text-sm font-medium ${isServiceWorkerReady ? 'text-green-600' : 'text-gray-600'}`}>
                        {isServiceWorkerReady ? 'Active' : 'Not Registered'}
                    </span>
                </div>

                {lastSyncTime && (
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Last Sync</span>
                        <span className="text-sm text-gray-900 dark:text-white">
                            {lastSyncTime.toLocaleTimeString()}
                        </span>
                    </div>
                )}

                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={handleClearCache}
                        className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 transition-colors"
                    >
                        {cacheCleared ? '✓ Cache Cleared' : 'Clear Cached Data'}
                    </button>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                        Clears locally cached data. Fresh data will be fetched when online.
                    </p>
                </div>
            </div>
        </div>
    );
}
