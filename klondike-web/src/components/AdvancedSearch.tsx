/**
 * Advanced feature search with filters and saved queries
 */

/* eslint-disable react-refresh/only-export-components */
import { useState, useSyncExternalStore } from 'react';
import { MagnifyingGlassIcon, FunnelIcon, BookmarkIcon, XMarkIcon } from '@heroicons/react/24/outline';

export interface SearchFilters {
    query: string;
    status: string[];
    category: string[];
    priority: number[];
    hasNotes: boolean | null;
    hasCriteria: boolean | null;
}

export interface SavedQuery {
    id: string;
    name: string;
    filters: SearchFilters;
    createdAt: string;
}

const DEFAULT_FILTERS: SearchFilters = {
    query: '',
    status: [],
    category: [],
    priority: [],
    hasNotes: null,
    hasCriteria: null,
};

// Store for saved queries
interface SavedQueryStore {
    queries: SavedQuery[];
}

const store: SavedQueryStore = {
    queries: [],
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

function loadSavedQueries(): SavedQuery[] {
    if (typeof window === 'undefined') return [];
    const stored = localStorage.getItem('klondike-saved-queries');
    if (!stored) return [];
    try {
        return JSON.parse(stored);
    } catch {
        return [];
    }
}

function saveSavedQueries(queries: SavedQuery[]) {
    localStorage.setItem('klondike-saved-queries', JSON.stringify(queries));
}

// Initialize store
if (typeof window !== 'undefined') {
    store.queries = loadSavedQueries();
}

export function useSavedQueries() {
    return useSyncExternalStore(subscribe, getSnapshot);
}

export function addSavedQuery(name: string, filters: SearchFilters): SavedQuery {
    const query: SavedQuery = {
        id: `sq-${Date.now()}`,
        name,
        filters,
        createdAt: new Date().toISOString(),
    };
    store.queries = [...store.queries, query];
    saveSavedQueries(store.queries);
    emitChange();
    return query;
}

export function removeSavedQuery(id: string) {
    store.queries = store.queries.filter(q => q.id !== id);
    saveSavedQueries(store.queries);
    emitChange();
}

// Filter badge component
interface FilterBadgeProps {
    label: string;
    onRemove: () => void;
}

function FilterBadge({ label, onRemove }: FilterBadgeProps) {
    return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs rounded-full">
            {label}
            <button
                onClick={onRemove}
                className="hover:text-indigo-900 dark:hover:text-indigo-100"
                aria-label={`Remove ${label} filter`}
            >
                <XMarkIcon className="w-3 h-3" />
            </button>
        </span>
    );
}

interface AdvancedSearchProps {
    filters: SearchFilters;
    onFiltersChange: (filters: SearchFilters) => void;
    categories: string[];
    className?: string;
}

export function AdvancedSearch({
    filters,
    onFiltersChange,
    categories,
    className = ''
}: AdvancedSearchProps) {
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [saveDialogOpen, setSaveDialogOpen] = useState(false);
    const [queryName, setQueryName] = useState('');
    const savedQueriesStore = useSavedQueries();

    const handleQueryChange = (query: string) => {
        onFiltersChange({ ...filters, query });
    };

    const toggleStatus = (status: string) => {
        const newStatus = filters.status.includes(status)
            ? filters.status.filter(s => s !== status)
            : [...filters.status, status];
        onFiltersChange({ ...filters, status: newStatus });
    };

    const toggleCategory = (category: string) => {
        const newCategory = filters.category.includes(category)
            ? filters.category.filter(c => c !== category)
            : [...filters.category, category];
        onFiltersChange({ ...filters, category: newCategory });
    };

    const togglePriority = (priority: number) => {
        const newPriority = filters.priority.includes(priority)
            ? filters.priority.filter(p => p !== priority)
            : [...filters.priority, priority];
        onFiltersChange({ ...filters, priority: newPriority });
    };

    const clearFilters = () => {
        onFiltersChange(DEFAULT_FILTERS);
    };

    const hasActiveFilters =
        filters.status.length > 0 ||
        filters.category.length > 0 ||
        filters.priority.length > 0 ||
        filters.hasNotes !== null ||
        filters.hasCriteria !== null;

    const handleSaveQuery = () => {
        if (queryName.trim()) {
            addSavedQuery(queryName.trim(), filters);
            setQueryName('');
            setSaveDialogOpen(false);
        }
    };

    const handleLoadQuery = (saved: SavedQuery) => {
        onFiltersChange(saved.filters);
    };

    const activeFilterCount =
        filters.status.length +
        filters.category.length +
        filters.priority.length +
        (filters.hasNotes !== null ? 1 : 0) +
        (filters.hasCriteria !== null ? 1 : 0);

    return (
        <div className={`space-y-3 ${className}`}>
            {/* Search input with filter toggle */}
            <div className="flex gap-2">
                <div className="flex-1 relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search features..."
                        value={filters.query}
                        onChange={(e) => handleQueryChange(e.target.value)}
                        data-search-input
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
                    />
                </div>
                <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className={`
                        px-3 py-2 border rounded-lg flex items-center gap-2 transition-colors
                        ${showAdvanced
                            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400'
                            : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}
                    `}
                    aria-expanded={showAdvanced}
                >
                    <FunnelIcon className="w-5 h-5" />
                    {activeFilterCount > 0 && (
                        <span className="text-xs font-medium bg-indigo-500 text-white px-1.5 py-0.5 rounded-full">
                            {activeFilterCount}
                        </span>
                    )}
                </button>
            </div>

            {/* Active filter badges */}
            {hasActiveFilters && (
                <div className="flex flex-wrap gap-2 items-center">
                    {filters.status.map(s => (
                        <FilterBadge key={s} label={s} onRemove={() => toggleStatus(s)} />
                    ))}
                    {filters.category.map(c => (
                        <FilterBadge key={c} label={c} onRemove={() => toggleCategory(c)} />
                    ))}
                    {filters.priority.map(p => (
                        <FilterBadge key={p} label={`P${p}`} onRemove={() => togglePriority(p)} />
                    ))}
                    {filters.hasNotes !== null && (
                        <FilterBadge
                            label={filters.hasNotes ? 'Has notes' : 'No notes'}
                            onRemove={() => onFiltersChange({ ...filters, hasNotes: null })}
                        />
                    )}
                    {filters.hasCriteria !== null && (
                        <FilterBadge
                            label={filters.hasCriteria ? 'Has criteria' : 'No criteria'}
                            onRemove={() => onFiltersChange({ ...filters, hasCriteria: null })}
                        />
                    )}
                    <button
                        onClick={clearFilters}
                        className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                        Clear all
                    </button>
                </div>
            )}

            {/* Advanced filters panel */}
            {showAdvanced && (
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 space-y-4">
                    {/* Status filters */}
                    <div>
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                            Status
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {['not-started', 'in-progress', 'blocked', 'verified'].map(status => (
                                <button
                                    key={status}
                                    onClick={() => toggleStatus(status)}
                                    className={`
                                        px-3 py-1 text-xs rounded-lg transition-colors
                                        ${filters.status.includes(status)
                                            ? 'bg-indigo-500 text-white'
                                            : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'}
                                    `}
                                >
                                    {status}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Category filters */}
                    <div>
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                            Category
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {categories.map(category => (
                                <button
                                    key={category}
                                    onClick={() => toggleCategory(category)}
                                    className={`
                                        px-3 py-1 text-xs rounded-lg transition-colors
                                        ${filters.category.includes(category)
                                            ? 'bg-indigo-500 text-white'
                                            : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'}
                                    `}
                                >
                                    {category}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Priority filters */}
                    <div>
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                            Priority
                        </label>
                        <div className="flex gap-2">
                            {[1, 2, 3, 4].map(priority => (
                                <button
                                    key={priority}
                                    onClick={() => togglePriority(priority)}
                                    className={`
                                        px-3 py-1 text-xs rounded-lg transition-colors
                                        ${filters.priority.includes(priority)
                                            ? 'bg-indigo-500 text-white'
                                            : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'}
                                    `}
                                >
                                    P{priority}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Boolean filters */}
                    <div className="flex gap-4">
                        <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                                Notes
                            </label>
                            <select
                                value={filters.hasNotes === null ? '' : filters.hasNotes.toString()}
                                onChange={(e) => onFiltersChange({
                                    ...filters,
                                    hasNotes: e.target.value === '' ? null : e.target.value === 'true'
                                })}
                                className="px-3 py-1 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                            >
                                <option value="">Any</option>
                                <option value="true">Has notes</option>
                                <option value="false">No notes</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                                Criteria
                            </label>
                            <select
                                value={filters.hasCriteria === null ? '' : filters.hasCriteria.toString()}
                                onChange={(e) => onFiltersChange({
                                    ...filters,
                                    hasCriteria: e.target.value === '' ? null : e.target.value === 'true'
                                })}
                                className="px-3 py-1 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
                            >
                                <option value="">Any</option>
                                <option value="true">Has criteria</option>
                                <option value="false">No criteria</option>
                            </select>
                        </div>
                    </div>

                    {/* Save query and saved queries */}
                    <div className="pt-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                        {saveDialogOpen ? (
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    placeholder="Query name..."
                                    value={queryName}
                                    onChange={(e) => setQueryName(e.target.value)}
                                    className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                                    autoFocus
                                />
                                <button
                                    onClick={handleSaveQuery}
                                    disabled={!queryName.trim()}
                                    className="px-2 py-1 text-xs bg-indigo-500 text-white rounded disabled:opacity-50"
                                >
                                    Save
                                </button>
                                <button
                                    onClick={() => setSaveDialogOpen(false)}
                                    className="px-2 py-1 text-xs text-gray-500"
                                >
                                    Cancel
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => setSaveDialogOpen(true)}
                                disabled={!hasActiveFilters && !filters.query}
                                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
                            >
                                <BookmarkIcon className="w-4 h-4" />
                                Save query
                            </button>
                        )}

                        {savedQueriesStore.queries.length > 0 && (
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400">Saved:</span>
                                {savedQueriesStore.queries.slice(0, 3).map(saved => (
                                    <button
                                        key={saved.id}
                                        onClick={() => handleLoadQuery(saved)}
                                        className="group flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                                    >
                                        {saved.name}
                                        <XMarkIcon
                                            className="w-3 h-3 opacity-0 group-hover:opacity-100"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                removeSavedQuery(saved.id);
                                            }}
                                        />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export { DEFAULT_FILTERS };
