/**
 * Quick add feature dialog - accessible from anywhere via Ctrl+Shift+N
 */

import { useState, useEffect, useRef, useSyncExternalStore } from 'react';
import { getApiBaseUrl } from '../utils/api';
import { announce } from '../utils/accessibility';
import toast from 'react-hot-toast';

// Store for quick add visibility
interface QuickAddStore {
    isOpen: boolean;
}

const store: QuickAddStore = {
    isOpen: false,
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

export function openQuickAdd() {
    store.isOpen = true;
    emitChange();
}

export function closeQuickAdd() {
    store.isOpen = false;
    emitChange();
}

export function toggleQuickAdd() {
    store.isOpen = !store.isOpen;
    emitChange();
}

export function useQuickAddStore() {
    return useSyncExternalStore(subscribe, getSnapshot);
}

interface QuickAddFormData {
    description: string;
    category: string;
    priority: number;
    acceptance_criteria: string;
    notes: string;
}

const DEFAULT_FORM: QuickAddFormData = {
    description: '',
    category: 'core',
    priority: 2,
    acceptance_criteria: '',
    notes: '',
};

const CATEGORIES = ['core', 'ui', 'infrastructure', 'enhancement', 'bugfix', 'documentation'];

export function QuickAddDialog() {
    const { isOpen } = useQuickAddStore();
    const [form, setForm] = useState<QuickAddFormData>(DEFAULT_FORM);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const dialogRef = useRef<HTMLDivElement>(null);

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            requestAnimationFrame(() => {
                inputRef.current?.focus();
            });
        } else {
            // Reset form when closed
            setForm(DEFAULT_FORM);
            setShowAdvanced(false);
        }
    }, [isOpen]);

    // Close on escape
    useEffect(() => {
        function handleKeyDown(e: KeyboardEvent) {
            if (e.key === 'Escape' && isOpen) {
                closeQuickAdd();
            }
        }

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen]);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (dialogRef.current && !dialogRef.current.contains(e.target as Node)) {
                closeQuickAdd();
            }
        }

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!form.description.trim()) {
            toast.error('Description is required');
            return;
        }

        setIsSubmitting(true);

        try {
            const response = await fetch(`${getApiBaseUrl()}/api/features`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    description: form.description.trim(),
                    category: form.category,
                    priority: form.priority,
                    acceptance_criteria: form.acceptance_criteria.trim() ?
                        form.acceptance_criteria.split('\n').map(c => c.trim()).filter(Boolean) :
                        [],
                    notes: form.notes.trim(),
                }),
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: 'Failed to add feature' }));
                throw new Error(error.error || 'Failed to add feature');
            }

            const result = await response.json();
            toast.success(`Feature ${result.id} added successfully!`);
            announce(`Feature ${result.id} added: ${form.description}`);
            closeQuickAdd();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to add feature';
            toast.error(message);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleChange = (field: keyof QuickAddFormData, value: string | number) => {
        setForm(prev => ({ ...prev, [field]: value }));
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm">
            <div
                ref={dialogRef}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
                role="dialog"
                aria-modal="true"
                aria-labelledby="quick-add-title"
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-indigo-50 dark:bg-indigo-900/30 border-b border-indigo-100 dark:border-indigo-800">
                    <h2 id="quick-add-title" className="text-sm font-semibold text-indigo-800 dark:text-indigo-200 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Quick Add Feature
                    </h2>
                    <button
                        onClick={closeQuickAdd}
                        className="p-1 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 rounded transition-colors"
                        aria-label="Close"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    {/* Description */}
                    <div>
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder="Feature description (e.g., Add dark mode toggle)"
                            value={form.description}
                            onChange={e => handleChange('description', e.target.value)}
                            className="w-full px-3 py-2 text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                            disabled={isSubmitting}
                        />
                    </div>

                    {/* Category and Priority */}
                    <div className="flex gap-3">
                        <div className="flex-1">
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                Category
                            </label>
                            <select
                                value={form.category}
                                onChange={e => handleChange('category', e.target.value)}
                                className="w-full px-3 py-2 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                disabled={isSubmitting}
                            >
                                {CATEGORIES.map(cat => (
                                    <option key={cat} value={cat}>{cat}</option>
                                ))}
                            </select>
                        </div>
                        <div className="w-24">
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                Priority
                            </label>
                            <select
                                value={form.priority}
                                onChange={e => handleChange('priority', parseInt(e.target.value))}
                                className="w-full px-3 py-2 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                disabled={isSubmitting}
                            >
                                <option value={1}>P1 (High)</option>
                                <option value={2}>P2</option>
                                <option value={3}>P3</option>
                                <option value={4}>P4 (Low)</option>
                            </select>
                        </div>
                    </div>

                    {/* Advanced toggle */}
                    <button
                        type="button"
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1"
                    >
                        <svg
                            className={`w-4 h-4 transform transition-transform ${showAdvanced ? 'rotate-90' : ''}`}
                            fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        {showAdvanced ? 'Hide' : 'Show'} advanced options
                    </button>

                    {/* Advanced options */}
                    {showAdvanced && (
                        <div className="space-y-3 pt-2 border-t border-gray-200 dark:border-gray-700">
                            {/* Acceptance criteria */}
                            <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                    Acceptance Criteria (one per line)
                                </label>
                                <textarea
                                    value={form.acceptance_criteria}
                                    onChange={e => handleChange('acceptance_criteria', e.target.value)}
                                    placeholder="- User can click button&#10;- Toast notification appears"
                                    rows={3}
                                    className="w-full px-3 py-2 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 resize-none"
                                    disabled={isSubmitting}
                                />
                            </div>

                            {/* Notes */}
                            <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                                    Implementation Notes
                                </label>
                                <textarea
                                    value={form.notes}
                                    onChange={e => handleChange('notes', e.target.value)}
                                    placeholder="Any additional context or technical notes..."
                                    rows={2}
                                    className="w-full px-3 py-2 text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 resize-none"
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-2">
                        <span className="text-xs text-gray-400 dark:text-gray-500">
                            <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">⌘</kbd>
                            <span className="mx-0.5">+</span>
                            <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">⇧</kbd>
                            <span className="mx-0.5">+</span>
                            <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">N</kbd>
                        </span>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={closeQuickAdd}
                                className="px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                                disabled={isSubmitting}
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isSubmitting || !form.description.trim()}
                                className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2"
                            >
                                {isSubmitting ? (
                                    <>
                                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Adding...
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                        </svg>
                                        Add Feature
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}
