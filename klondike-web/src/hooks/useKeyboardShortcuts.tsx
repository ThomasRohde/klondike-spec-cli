/**
 * Keyboard shortcuts hook for global application shortcuts
 */

import { useEffect, useSyncExternalStore } from 'react';
import { useNavigate } from 'react-router-dom';
import { openQuickAdd } from '../components/QuickAddDialog';

export interface ShortcutAction {
    key: string;
    modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[];
    description: string;
    category: string;
    action: () => void;
}

interface ShortcutStore {
    shortcuts: Map<string, ShortcutAction>;
    helpVisible: boolean;
}

let store: ShortcutStore = {
    shortcuts: new Map(),
    helpVisible: false,
};

// We need a version number to force React to re-render when store changes
let storeVersion = 0;

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

function getSnapshot() {
    // Return version to trigger re-renders
    return storeVersion;
}

function emitChange() {
    storeVersion++;
    listeners.forEach(listener => listener());
}

function getShortcutKey(key: string, modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[]): string {
    const mods = modifiers ? [...modifiers].sort().join('+') + '+' : '';
    return mods + key.toLowerCase();
}

export function registerShortcut(action: ShortcutAction) {
    const key = getShortcutKey(action.key, action.modifiers);
    store.shortcuts.set(key, action);
    emitChange();
    return () => {
        store.shortcuts.delete(key);
        emitChange();
    };
}

export function showShortcutsHelp() {
    store.helpVisible = true;
    emitChange();
}

export function hideShortcutsHelp() {
    store.helpVisible = false;
    emitChange();
}

export function toggleShortcutsHelp() {
    store.helpVisible = !store.helpVisible;
    emitChange();
}

export function useShortcutsStore() {
    // Subscribe to version changes
    useSyncExternalStore(subscribe, getSnapshot);
    // Return actual store data (the subscription above triggers re-renders)
    return store;
}

export function useKeyboardShortcuts() {
    const storeState = useShortcutsStore();
    const navigate = useNavigate();

    // Register global shortcuts
    useEffect(() => {
        const unsubscribers: (() => void)[] = [];

        // Navigation shortcuts
        unsubscribers.push(registerShortcut({
            key: 'd',
            modifiers: ['ctrl'],
            description: 'Go to Dashboard',
            category: 'Navigation',
            action: () => navigate('/'),
        }));

        unsubscribers.push(registerShortcut({
            key: 'e',
            modifiers: ['ctrl'],
            description: 'Go to Spec Explorer',
            category: 'Navigation',
            action: () => navigate('/spec'),
        }));

        unsubscribers.push(registerShortcut({
            key: 't',
            modifiers: ['ctrl'],
            description: 'Go to Task Viewer',
            category: 'Navigation',
            action: () => navigate('/tasks'),
        }));

        unsubscribers.push(registerShortcut({
            key: 'a',
            modifiers: ['ctrl'],
            description: 'Go to Activity Log',
            category: 'Navigation',
            action: () => navigate('/activity'),
        }));

        unsubscribers.push(registerShortcut({
            key: 'b',
            modifiers: ['ctrl'],
            description: 'Go to Kanban Board',
            category: 'Navigation',
            action: () => navigate('/kanban'),
        }));

        unsubscribers.push(registerShortcut({
            key: ',',
            modifiers: ['ctrl'],
            description: 'Go to Configuration',
            category: 'Navigation',
            action: () => navigate('/config'),
        }));

        // Action shortcuts
        unsubscribers.push(registerShortcut({
            key: 'k',
            modifiers: ['ctrl'],
            description: 'Open Command Palette',
            category: 'Actions',
            action: () => {
                // Dispatch custom event for command palette
                window.dispatchEvent(new CustomEvent('open-command-palette'));
            },
        }));

        unsubscribers.push(registerShortcut({
            key: 'n',
            modifiers: ['ctrl', 'shift'],
            description: 'Add New Feature',
            category: 'Actions',
            action: openQuickAdd,
        }));

        unsubscribers.push(registerShortcut({
            key: '/',
            description: 'Focus Search',
            category: 'Actions',
            action: () => {
                const searchInput = document.querySelector<HTMLInputElement>('[data-search-input]');
                searchInput?.focus();
            },
        }));

        // Help shortcuts
        unsubscribers.push(registerShortcut({
            key: '?',
            modifiers: ['shift'],
            description: 'Show Keyboard Shortcuts',
            category: 'Help',
            action: toggleShortcutsHelp,
        }));

        unsubscribers.push(registerShortcut({
            key: '/',
            modifiers: ['ctrl'],
            description: 'Show Keyboard Shortcuts (Alternative)',
            category: 'Help',
            action: toggleShortcutsHelp,
        }));

        return () => {
            unsubscribers.forEach(unsub => unsub());
        };
    }, [navigate]);

    // Global keyboard listener
    useEffect(() => {
        function handleKeyDown(e: KeyboardEvent) {
            // Don't trigger shortcuts in input fields
            const target = e.target as HTMLElement;
            if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
                // Only allow Escape in inputs
                if (e.key !== 'Escape') {
                    return;
                }
            }

            // Build shortcut key
            const modifiers: ('ctrl' | 'alt' | 'shift' | 'meta')[] = [];
            if (e.ctrlKey || e.metaKey) modifiers.push('ctrl');
            if (e.altKey) modifiers.push('alt');
            if (e.shiftKey && e.key.length > 1) modifiers.push('shift'); // Only count shift for non-printable

            // Special handling for ? (shift + /)
            const key = e.key === '?' ? '?' : e.key.toLowerCase();

            const shortcutKey = getShortcutKey(key, modifiers.length > 0 ? modifiers : undefined);
            const action = store.shortcuts.get(shortcutKey);

            if (action) {
                e.preventDefault();
                e.stopPropagation();
                action.action();
            }

            // Escape closes help overlay
            if (e.key === 'Escape' && store.helpVisible) {
                hideShortcutsHelp();
            }
        }

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    return {
        shortcuts: Array.from(storeState.shortcuts.values()),
        helpVisible: storeState.helpVisible,
        showHelp: showShortcutsHelp,
        hideHelp: hideShortcutsHelp,
        toggleHelp: toggleShortcutsHelp,
    };
}

// Format keyboard shortcut for display
export function formatShortcut(key: string, modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[]): string {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

    const modLabels = (modifiers || []).map(mod => {
        switch (mod) {
            case 'ctrl': return isMac ? '⌘' : 'Ctrl';
            case 'alt': return isMac ? '⌥' : 'Alt';
            case 'shift': return '⇧';
            case 'meta': return isMac ? '⌘' : 'Win';
            default: return mod;
        }
    });

    const keyLabel = key.length === 1 ? key.toUpperCase() : key;
    return [...modLabels, keyLabel].join(isMac ? '' : '+');
}
