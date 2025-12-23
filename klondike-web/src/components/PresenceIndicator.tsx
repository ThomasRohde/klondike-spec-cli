/**
 * Real-time collaboration indicators showing active users
 */

import { useState, useEffect, useMemo, useSyncExternalStore } from 'react';
import { useLocation } from 'react-router-dom';
import { UserCircleIcon, EyeIcon } from '@heroicons/react/24/solid';
import { getWebSocketUrl } from '../utils/api';

// User presence data
interface UserPresence {
    id: string;
    name: string;
    avatar?: string;
    color: string;
    currentView: string;
    lastSeen: number;
}

// Presence store with useSyncExternalStore pattern
interface PresenceStore {
    users: Map<string, UserPresence>;
    ws: WebSocket | null;
    userId: string;
}

const store: PresenceStore = {
    users: new Map(),
    ws: null,
    userId: generateUserId(),
};

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

function getSnapshot() {
    return store.users;
}

function emitChange() {
    listeners.forEach(listener => listener());
}

// Generate random user ID for this session
function generateUserId(): string {
    return `user-${Math.random().toString(36).substring(2, 9)}`;
}

// Generate random avatar color
function generateUserColor(): string {
    const colors = [
        '#ef4444', '#f97316', '#f59e0b', '#84cc16',
        '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
        '#6366f1', '#8b5cf6', '#a855f7', '#ec4899',
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Get display name from localStorage or generate
function getUserName(): string {
    let name = localStorage.getItem('klondike-user-name');
    if (!name) {
        const adjectives = ['Happy', 'Swift', 'Clever', 'Bold', 'Calm', 'Bright'];
        const animals = ['Fox', 'Owl', 'Bear', 'Wolf', 'Hawk', 'Lynx'];
        name = `${adjectives[Math.floor(Math.random() * adjectives.length)]} ${animals[Math.floor(Math.random() * animals.length)]}`;
        localStorage.setItem('klondike-user-name', name);
    }
    return name;
}

// Connect to presence WebSocket
export function initializePresence() {
    if (store.ws) return;

    try {
        const wsUrl = getWebSocketUrl('/ws/presence');
        store.ws = new WebSocket(wsUrl);

        store.ws.onopen = () => {
            console.log('Presence WebSocket connected');
            sendPresence(window.location.pathname);
        };

        store.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                // Skip malformed messages
                if (!message || typeof message.type !== 'string') {
                    return;
                }

                if (message.type === 'presence') {
                    // Single user update - validate user object exists
                    const user: UserPresence | undefined = message.user;
                    if (user && typeof user.id === 'string' && user.id !== store.userId) {
                        store.users.set(user.id, user);
                        emitChange();
                    }
                } else if (message.type === 'presenceList') {
                    // Full list of active users
                    store.users.clear();
                    if (Array.isArray(message.users)) {
                        for (const user of message.users as UserPresence[]) {
                            if (user && user.id && user.id !== store.userId) {
                                store.users.set(user.id, user);
                            }
                        }
                    }
                    emitChange();
                } else if (message.type === 'userLeft') {
                    // User disconnected - validate userId exists
                    if (typeof message.userId === 'string') {
                        store.users.delete(message.userId);
                        emitChange();
                    }
                }
            } catch (error) {
                // Only log actual parsing errors, not invalid message structure
                if (error instanceof SyntaxError) {
                    console.error('Failed to parse presence message JSON:', error);
                }
            }
        };

        store.ws.onclose = () => {
            console.log('Presence WebSocket closed');
            store.ws = null;
            // Reconnect after delay
            setTimeout(initializePresence, 5000);
        };

        store.ws.onerror = () => {
            console.log('Presence WebSocket error - connection unavailable');
            // Don't retry too aggressively on error
        };
    } catch {
        console.log('Presence WebSocket not available');
    }
}

// Send presence update
export function sendPresence(view: string) {
    if (!store.ws || store.ws.readyState !== WebSocket.OPEN) return;

    const presence: UserPresence = {
        id: store.userId,
        name: getUserName(),
        color: localStorage.getItem('klondike-user-color') || generateUserColor(),
        currentView: view,
        lastSeen: Date.now(),
    };

    // Store color for consistency
    localStorage.setItem('klondike-user-color', presence.color);

    store.ws.send(JSON.stringify({
        type: 'presence',
        user: presence,
    }));
}

// Hook to use presence data
export function usePresence() {
    const users = useSyncExternalStore(subscribe, getSnapshot);
    return useMemo(() => [...users.values()], [users]);
}

// Hook to track and broadcast current view
export function usePresenceTracking() {
    const location = useLocation();

    useEffect(() => {
        initializePresence();
    }, []);

    useEffect(() => {
        sendPresence(location.pathname);
    }, [location.pathname]);
}

// Avatar component
interface UserAvatarProps {
    user: UserPresence;
    size?: 'sm' | 'md' | 'lg';
    showStatus?: boolean;
}

export function UserAvatar({ user, size = 'md', showStatus = true }: UserAvatarProps) {
    const sizeClasses = {
        sm: 'w-6 h-6 text-xs',
        md: 'w-8 h-8 text-sm',
        lg: 'w-10 h-10 text-base',
    };

    const initials = user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);

    return (
        <div className="relative" title={`${user.name} - ${getViewLabel(user.currentView)}`}>
            {user.avatar ? (
                <img
                    src={user.avatar}
                    alt={user.name}
                    className={`${sizeClasses[size]} rounded-full ring-2 ring-white dark:ring-gray-800`}
                />
            ) : (
                <div
                    className={`${sizeClasses[size]} rounded-full ring-2 ring-white dark:ring-gray-800 flex items-center justify-center font-medium text-white`}
                    style={{ backgroundColor: user.color }}
                >
                    {initials}
                </div>
            )}
            {showStatus && (
                <span
                    className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full ring-2 ring-white dark:ring-gray-800"
                    title="Online"
                />
            )}
        </div>
    );
}

// Get human-readable view label
function getViewLabel(path: string): string {
    if (path === '/dashboard' || path === '/') return 'Dashboard';
    if (path === '/specs') return 'Spec Explorer';
    if (path === '/kanban') return 'Kanban Board';
    if (path === '/timeline') return 'Timeline';
    if (path === '/dependencies') return 'Dependencies';
    if (path === '/activity') return 'Activity Log';
    if (path === '/config') return 'Config';
    if (path.startsWith('/task/')) return `Feature ${path.split('/')[2]}`;
    return path;
}

// Avatar stack component
interface UserStackProps {
    maxVisible?: number;
    showViews?: boolean;
}

export function UserStack({ maxVisible = 3, showViews = false }: UserStackProps) {
    const users = usePresence();
    const [showTooltip, setShowTooltip] = useState(false);

    if (users.length === 0) {
        return null;
    }

    const visibleUsers = users.slice(0, maxVisible);
    const hiddenCount = users.length - maxVisible;

    return (
        <div
            className="relative"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            <div className="flex -space-x-2">
                {visibleUsers.map((user) => (
                    <UserAvatar key={user.id} user={user} size="sm" />
                ))}
                {hiddenCount > 0 && (
                    <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 ring-2 ring-white dark:ring-gray-800 flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-400">
                        +{hiddenCount}
                    </div>
                )}
            </div>

            {/* Tooltip with full user list */}
            {showTooltip && (
                <div className="absolute top-full right-0 mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 px-3 z-50 min-w-48">
                    <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                        {users.length} online
                    </div>
                    <div className="space-y-2">
                        {users.map((user) => (
                            <div key={user.id} className="flex items-center gap-2">
                                <UserAvatar user={user} size="sm" showStatus={false} />
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                        {user.name}
                                    </div>
                                    {showViews && (
                                        <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                            <EyeIcon className="w-3 h-3" />
                                            {getViewLabel(user.currentView)}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// Presence indicator for header/layout
export function PresenceIndicator() {
    const users = usePresence();

    // Initialize presence tracking
    usePresenceTracking();

    return (
        <div className="flex items-center gap-2">
            <UserStack maxVisible={3} showViews />
            {users.length === 0 && (
                <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                    <UserCircleIcon className="w-4 h-4" />
                    <span>Solo</span>
                </div>
            )}
        </div>
    );
}

// Settings component for user name
export function PresenceSettings() {
    const [name, setName] = useState(getUserName());
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        localStorage.setItem('klondike-user-name', name);
        setSaved(true);
        sendPresence(window.location.pathname);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Collaboration Settings
            </h3>
            <div className="space-y-3">
                <div>
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                        Display Name
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="Your name"
                        />
                        <button
                            onClick={handleSave}
                            className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
                        >
                            {saved ? '✓ Saved' : 'Save'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
