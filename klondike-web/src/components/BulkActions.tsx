/**
 * Bulk actions toolbar for multiple feature selection
 */

/* eslint-disable react-refresh/only-export-components */
import { useState, useSyncExternalStore } from 'react';
import {
    CheckIcon,
    PlayIcon,
    NoSymbolIcon,
    XMarkIcon,
    ArrowPathIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { getApiBaseUrl } from '../utils/api';
import { announce } from '../utils/accessibility';

// Store for selected features
interface SelectionStore {
    selectedIds: Set<string>;
}

const store: SelectionStore = {
    selectedIds: new Set(),
};

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

function getSnapshot() {
    return store.selectedIds;
}

function emitChange() {
    listeners.forEach(listener => listener());
}

export function toggleSelection(id: string) {
    if (store.selectedIds.has(id)) {
        store.selectedIds = new Set([...store.selectedIds].filter(i => i !== id));
    } else {
        store.selectedIds = new Set([...store.selectedIds, id]);
    }
    emitChange();
}

export function selectAll(ids: string[]) {
    store.selectedIds = new Set(ids);
    emitChange();
}

export function clearSelection() {
    store.selectedIds = new Set();
    emitChange();
}

export function isSelected(id: string): boolean {
    return store.selectedIds.has(id);
}

export function useSelection() {
    return useSyncExternalStore(subscribe, getSnapshot);
}

// Selection checkbox component
interface SelectionCheckboxProps {
    id: string;
    className?: string;
}

export function SelectionCheckbox({ id, className = '' }: SelectionCheckboxProps) {
    const selectedIds = useSelection();
    const checked = selectedIds.has(id);

    return (
        <input
            type="checkbox"
            checked={checked}
            onChange={() => toggleSelection(id)}
            className={`w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 ${className}`}
            aria-label={`Select ${id}`}
        />
    );
}

// Bulk actions toolbar
interface BulkActionsToolbarProps {
    allIds: string[];
    onRefresh?: () => void;
}

export function BulkActionsToolbar({ allIds, onRefresh }: BulkActionsToolbarProps) {
    const selectedIds = useSelection();
    const [isProcessing, setIsProcessing] = useState(false);

    const selectedCount = selectedIds.size;
    const allSelected = selectedCount === allIds.length && allIds.length > 0;
    const someSelected = selectedCount > 0 && selectedCount < allIds.length;

    if (selectedCount === 0) {
        return null;
    }

    const handleSelectAll = () => {
        if (allSelected) {
            clearSelection();
        } else {
            selectAll(allIds);
        }
    };

    const performBulkAction = async (
        action: 'start' | 'block' | 'verify',
        endpoint: string,
        successMessage: string
    ) => {
        setIsProcessing(true);
        const ids = [...selectedIds];
        let successCount = 0;
        let failCount = 0;

        for (const id of ids) {
            try {
                const response = await fetch(`${getApiBaseUrl()}/api/features/${id}/${endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: action === 'block'
                        ? JSON.stringify({ reason: 'Blocked via bulk action' })
                        : action === 'verify'
                            ? JSON.stringify({ evidence: 'Verified via bulk action' })
                            : undefined,
                });

                if (response.ok) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch {
                failCount++;
            }
        }

        if (successCount > 0) {
            toast.success(`${successMessage}: ${successCount} features`);
            announce(`${successCount} features ${action === 'start' ? 'started' : action === 'block' ? 'blocked' : 'verified'}`);
        }
        if (failCount > 0) {
            toast.error(`Failed: ${failCount} features`);
        }

        clearSelection();
        setIsProcessing(false);
        onRefresh?.();
    };

    const handleBulkStart = () => performBulkAction('start', 'start', 'Started');
    const handleBulkBlock = () => performBulkAction('block', 'block', 'Blocked');
    const handleBulkVerify = () => performBulkAction('verify', 'verify', 'Verified');

    return (
        <div className="sticky top-0 z-20 bg-indigo-600 text-white shadow-lg rounded-lg p-3 mb-4 flex items-center justify-between animate-in slide-in-from-top duration-200">
            <div className="flex items-center gap-3">
                <input
                    type="checkbox"
                    checked={allSelected}
                    ref={input => {
                        if (input) input.indeterminate = someSelected;
                    }}
                    onChange={handleSelectAll}
                    className="w-5 h-5 rounded border-white text-indigo-800 focus:ring-white focus:ring-offset-indigo-600"
                    aria-label={allSelected ? 'Deselect all' : 'Select all'}
                />
                <span className="font-medium">
                    {selectedCount} selected
                </span>
            </div>

            <div className="flex items-center gap-2">
                {isProcessing && (
                    <ArrowPathIcon className="w-5 h-5 animate-spin" />
                )}

                <button
                    onClick={handleBulkStart}
                    disabled={isProcessing}
                    className="flex items-center gap-1 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    title="Start selected features"
                >
                    <PlayIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">Start</span>
                </button>

                <button
                    onClick={handleBulkBlock}
                    disabled={isProcessing}
                    className="flex items-center gap-1 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    title="Block selected features"
                >
                    <NoSymbolIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">Block</span>
                </button>

                <button
                    onClick={handleBulkVerify}
                    disabled={isProcessing}
                    className="flex items-center gap-1 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    title="Verify selected features"
                >
                    <CheckIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">Verify</span>
                </button>

                <div className="w-px h-6 bg-white/30" />

                <button
                    onClick={clearSelection}
                    disabled={isProcessing}
                    className="flex items-center gap-1 px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    title="Clear selection"
                >
                    <XMarkIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">Clear</span>
                </button>
            </div>
        </div>
    );
}

// Select all header checkbox
interface SelectAllCheckboxProps {
    allIds: string[];
    className?: string;
}

export function SelectAllCheckbox({ allIds, className = '' }: SelectAllCheckboxProps) {
    const selectedIds = useSelection();
    const allSelected = selectedIds.size === allIds.length && allIds.length > 0;
    const someSelected = selectedIds.size > 0 && selectedIds.size < allIds.length;

    return (
        <input
            type="checkbox"
            checked={allSelected}
            ref={input => {
                if (input) input.indeterminate = someSelected;
            }}
            onChange={() => {
                if (allSelected) {
                    clearSelection();
                } else {
                    selectAll(allIds);
                }
            }}
            className={`w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 ${className}`}
            aria-label={allSelected ? 'Deselect all features' : 'Select all features'}
        />
    );
}
