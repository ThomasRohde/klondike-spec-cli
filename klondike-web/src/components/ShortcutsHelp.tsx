/**
 * Keyboard shortcuts help overlay
 */

import { type ReactNode } from 'react';
import { useKeyboardShortcuts, formatShortcut, type ShortcutAction } from '../hooks/useKeyboardShortcuts';

interface KeyboardBadgeProps {
    children: ReactNode;
}

function KeyboardBadge({ children }: KeyboardBadgeProps) {
    return (
        <kbd className="inline-flex items-center justify-center min-w-[24px] px-1.5 py-0.5 text-xs font-semibold font-mono bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded shadow-sm">
            {children}
        </kbd>
    );
}

interface ShortcutRowProps {
    shortcut: ShortcutAction;
}

function ShortcutRow({ shortcut }: ShortcutRowProps) {
    const formatted = formatShortcut(shortcut.key, shortcut.modifiers);

    return (
        <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-700 dark:text-gray-300">
                {shortcut.description}
            </span>
            <KeyboardBadge>{formatted}</KeyboardBadge>
        </div>
    );
}

interface ShortcutCategoryProps {
    category: string;
    shortcuts: ShortcutAction[];
}

function ShortcutCategory({ category, shortcuts }: ShortcutCategoryProps) {
    return (
        <div className="mb-6 last:mb-0">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
                {category}
            </h3>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {shortcuts.map((shortcut, index) => (
                    <ShortcutRow key={`${shortcut.key}-${index}`} shortcut={shortcut} />
                ))}
            </div>
        </div>
    );
}

export function ShortcutsHelpOverlay() {
    const { shortcuts, helpVisible, hideHelp } = useKeyboardShortcuts();

    if (!helpVisible) return null;

    // Group shortcuts by category
    const categories = shortcuts.reduce<Record<string, ShortcutAction[]>>((acc, shortcut) => {
        if (!acc[shortcut.category]) {
            acc[shortcut.category] = [];
        }
        acc[shortcut.category].push(shortcut);
        return acc;
    }, {});

    const categoryOrder = ['Navigation', 'Actions', 'Help'];
    const sortedCategories = Object.keys(categories).sort((a, b) => {
        const aIndex = categoryOrder.indexOf(a);
        const bIndex = categoryOrder.indexOf(b);
        if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
        if (aIndex === -1) return 1;
        if (bIndex === -1) return -1;
        return aIndex - bIndex;
    });

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={hideHelp}
            role="dialog"
            aria-modal="true"
            aria-labelledby="shortcuts-title"
        >
            <div
                className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-lg w-full max-h-[80vh] overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h2 id="shortcuts-title" className="text-lg font-semibold text-gray-900 dark:text-white">
                        Keyboard Shortcuts
                    </h2>
                    <button
                        onClick={hideHelp}
                        className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        aria-label="Close shortcuts help"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="px-6 py-4 overflow-y-auto max-h-[calc(80vh-120px)]">
                    {sortedCategories.map(category => (
                        <ShortcutCategory
                            key={category}
                            category={category}
                            shortcuts={categories[category]}
                        />
                    ))}
                </div>

                {/* Footer */}
                <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        Press <KeyboardBadge>Esc</KeyboardBadge> or <KeyboardBadge>?</KeyboardBadge> to close
                    </p>
                </div>
            </div>
        </div>
    );
}

// Floating help button
export function ShortcutsHelpButton() {
    const { toggleHelp } = useKeyboardShortcuts();

    return (
        <button
            onClick={toggleHelp}
            className="fixed bottom-4 right-4 z-40 p-3 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-full shadow-lg hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors"
            aria-label="Show keyboard shortcuts (Shift + ?)"
            title="Keyboard shortcuts (Shift + ?)"
        >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span className="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 text-[10px] font-bold bg-blue-500 text-white rounded-full">
                ?
            </span>
        </button>
    );
}
