import { Command } from 'cmdk';
import { useEffect, useState, useCallback, useRef } from 'react';
import { getApiBaseUrl } from '../utils/api';

interface Feature {
    id: string;
    description: string;
    status: string;
    priority: number;
}

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
}

/**
 * Command palette for quick navigation and actions.
 * Opens with Cmd+K / Ctrl+K, supports fuzzy search.
 */
export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
    const [features, setFeatures] = useState<Feature[]>([]);
    const hasFetched = useRef(false);

    // Fetch features when palette opens (only once)
    useEffect(() => {
        if (!isOpen || hasFetched.current) return;
        
        hasFetched.current = true;
        
        fetch(`${getApiBaseUrl()}/api/features`)
            .then(res => res.json())
            .then(data => {
                setFeatures(data.features || []);
            })
            .catch(console.error);
    }, [isOpen]);

    const handleAction = useCallback((action: string) => {
        switch (action) {
            case 'refresh':
                window.location.reload();
                break;
            case 'toggle-dark':
                document.documentElement.classList.toggle('dark');
                break;
            default:
                console.log('Unknown action:', action);
        }
    }, []);

    const handleSelect = useCallback((value: string) => {
        // Parse the command value and navigate/execute
        if (value.startsWith('feature:')) {
            const featureId = value.replace('feature:', '');
            window.location.href = `/features/${featureId}`;
        } else if (value.startsWith('nav:')) {
            const path = value.replace('nav:', '');
            window.location.href = path;
        } else if (value.startsWith('action:')) {
            const action = value.replace('action:', '');
            handleAction(action);
        }
        onClose();
    }, [onClose, handleAction]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />
            
            {/* Command palette */}
            <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl">
                <Command
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
                    onKeyDown={(e) => {
                        if (e.key === 'Escape') {
                            onClose();
                        }
                    }}
                >
                    <Command.Input 
                        placeholder="Search features, navigate, or run commands..."
                        className="w-full px-4 py-3 text-lg border-b border-gray-200 dark:border-gray-700 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none"
                        autoFocus
                    />
                    
                    <Command.List className="max-h-80 overflow-y-auto p-2">
                        <Command.Empty className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                            No results found.
                        </Command.Empty>

                        {/* Navigation */}
                        <Command.Group heading="Navigation" className="mb-2">
                            <Command.Item 
                                value="nav:/"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="text-lg">🏠</span>
                                <span>Dashboard</span>
                            </Command.Item>
                            <Command.Item 
                                value="nav:/features"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="text-lg">📋</span>
                                <span>All Features</span>
                            </Command.Item>
                            <Command.Item 
                                value="nav:/config"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="text-lg">⚙️</span>
                                <span>Configuration</span>
                            </Command.Item>
                        </Command.Group>

                        {/* Quick Filters */}
                        <Command.Group heading="Filter by Status" className="mb-2">
                            <Command.Item 
                                value="nav:/features?status=in-progress"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="w-2 h-2 rounded-full bg-yellow-500" />
                                <span>In Progress Features</span>
                            </Command.Item>
                            <Command.Item 
                                value="nav:/features?status=blocked"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="w-2 h-2 rounded-full bg-red-500" />
                                <span>Blocked Features</span>
                            </Command.Item>
                            <Command.Item 
                                value="nav:/features?status=not-started"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="w-2 h-2 rounded-full bg-gray-500" />
                                <span>Not Started Features</span>
                            </Command.Item>
                        </Command.Group>

                        {/* Actions */}
                        <Command.Group heading="Actions" className="mb-2">
                            <Command.Item 
                                value="action:refresh"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="text-lg">🔄</span>
                                <span>Refresh Page</span>
                            </Command.Item>
                            <Command.Item 
                                value="action:toggle-dark"
                                onSelect={handleSelect}
                                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                            >
                                <span className="text-lg">🌙</span>
                                <span>Toggle Dark Mode</span>
                            </Command.Item>
                        </Command.Group>

                        {/* Features */}
                        {features.length > 0 && (
                            <Command.Group heading="Features" className="mb-2">
                                {features.slice(0, 10).map(feature => (
                                    <Command.Item 
                                        key={feature.id}
                                        value={`feature:${feature.id} ${feature.description}`}
                                        onSelect={() => handleSelect(`feature:${feature.id}`)}
                                        className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 aria-selected:bg-indigo-100 dark:aria-selected:bg-indigo-900/50"
                                    >
                                        <span className={`w-2 h-2 rounded-full ${
                                            feature.status === 'verified' ? 'bg-green-500' :
                                            feature.status === 'in-progress' ? 'bg-yellow-500' :
                                            feature.status === 'blocked' ? 'bg-red-500' :
                                            'bg-gray-400'
                                        }`} />
                                        <span className="font-mono text-xs text-gray-500 dark:text-gray-400">
                                            {feature.id}
                                        </span>
                                        <span className="truncate">{feature.description}</span>
                                    </Command.Item>
                                ))}
                            </Command.Group>
                        )}
                    </Command.List>

                    {/* Footer with keyboard hints */}
                    <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-4">
                            <span><kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">↑↓</kbd> Navigate</span>
                            <span><kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">↵</kbd> Select</span>
                            <span><kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">Esc</kbd> Close</span>
                        </div>
                    </div>
                </Command>
            </div>
        </div>
    );
}
