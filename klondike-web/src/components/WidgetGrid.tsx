import { useState, useCallback, useMemo, useSyncExternalStore } from 'react';
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    type DragEndEvent,
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
    Cog6ToothIcon,
    XMarkIcon,
    EyeIcon,
    EyeSlashIcon,
    PencilSquareIcon,
    Bars3Icon,
} from '@heroicons/react/24/outline';

// Widget types available in the dashboard
export type WidgetType =
    | 'progress-ring'
    | 'status-chart'
    | 'feature-counts'
    | 'session-control'
    | 'priority-features'
    | 'recent-activity'
    | 'git-status';

export interface WidgetConfig {
    id: string;
    type: WidgetType;
    title: string;
    visible: boolean;
    size: 'small' | 'medium' | 'large' | 'full';
    order: number;
}

interface WidgetGridProps {
    widgets: WidgetConfig[];
    onWidgetsChange: (widgets: WidgetConfig[]) => void;
    renderWidget: (config: WidgetConfig) => React.ReactNode;
    isEditMode: boolean;
    onEditModeChange: (editMode: boolean) => void;
    showSettings?: boolean;
    onShowSettingsChange?: (show: boolean) => void;
}

// --- Widget Layout Storage ---
const STORAGE_KEY = 'klondike-widget-layout';

interface WidgetLayoutStore {
    widgets: WidgetConfig[];
}

let layoutCache: WidgetLayoutStore | null = null;
const layoutListeners = new Set<() => void>();

function getDefaultWidgets(): WidgetConfig[] {
    return [
        { id: 'feature-counts', type: 'feature-counts', title: 'Feature Counts', visible: true, size: 'full', order: 0 },
        { id: 'progress-ring', type: 'progress-ring', title: 'Overall Progress', visible: true, size: 'medium', order: 1 },
        { id: 'status-chart', type: 'status-chart', title: 'Status Distribution', visible: true, size: 'medium', order: 2 },
        { id: 'session-control', type: 'session-control', title: 'Session Control', visible: true, size: 'full', order: 3 },
        { id: 'priority-features', type: 'priority-features', title: 'Priority Features', visible: true, size: 'medium', order: 4 },
        { id: 'recent-activity', type: 'recent-activity', title: 'Recent Activity', visible: true, size: 'medium', order: 5 },
    ];
}

function loadLayout(): WidgetLayoutStore {
    if (layoutCache) return layoutCache;

    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            layoutCache = JSON.parse(stored);
            return layoutCache!;
        }
    } catch (e) {
        console.warn('Failed to load widget layout:', e);
    }

    layoutCache = { widgets: getDefaultWidgets() };
    return layoutCache;
}

function saveLayout(layout: WidgetLayoutStore): void {
    layoutCache = layout;
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
    } catch (e) {
        console.warn('Failed to save widget layout:', e);
    }
    layoutListeners.forEach(listener => listener());
}

function subscribeLayout(listener: () => void): () => void {
    layoutListeners.add(listener);
    return () => layoutListeners.delete(listener);
}

function getLayoutSnapshot(): WidgetLayoutStore {
    return loadLayout();
}

// Hook for widget layout management
export function useWidgetLayout() {
    const layout = useSyncExternalStore(subscribeLayout, getLayoutSnapshot, getLayoutSnapshot);

    const setWidgets = useCallback((widgets: WidgetConfig[]) => {
        saveLayout({ widgets });
    }, []);

    const resetToDefaults = useCallback(() => {
        saveLayout({ widgets: getDefaultWidgets() });
    }, []);

    const toggleWidget = useCallback((widgetId: string) => {
        const current = loadLayout();
        const updated = current.widgets.map(w =>
            w.id === widgetId ? { ...w, visible: !w.visible } : w
        );
        saveLayout({ widgets: updated });
    }, []);

    const updateWidgetSize = useCallback((widgetId: string, size: WidgetConfig['size']) => {
        const current = loadLayout();
        const updated = current.widgets.map(w =>
            w.id === widgetId ? { ...w, size } : w
        );
        saveLayout({ widgets: updated });
    }, []);

    return {
        widgets: layout.widgets,
        setWidgets,
        resetToDefaults,
        toggleWidget,
        updateWidgetSize,
    };
}

// --- Sortable Widget Item ---
interface SortableWidgetProps {
    config: WidgetConfig;
    isEditMode: boolean;
    onToggleVisibility: () => void;
    onSizeChange: (size: WidgetConfig['size']) => void;
    children: React.ReactNode;
}

function SortableWidget({ config, isEditMode, onToggleVisibility, onSizeChange, children }: SortableWidgetProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: config.id, disabled: !isEditMode });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    // Determine grid column span based on size
    const sizeClasses = {
        small: 'col-span-1',
        medium: 'col-span-1 lg:col-span-1',
        large: 'col-span-1 lg:col-span-2',
        full: 'col-span-1 lg:col-span-2',
    };

    if (!config.visible && !isEditMode) {
        return null;
    }

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`
                ${sizeClasses[config.size]}
                ${!config.visible ? 'opacity-50' : ''}
                ${isEditMode ? 'ring-2 ring-indigo-400 ring-opacity-50' : ''}
                relative group
            `}
        >
            {isEditMode && (
                <div className="absolute top-2 right-2 z-10 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Drag handle */}
                    <button
                        {...attributes}
                        {...listeners}
                        className="p-1 bg-gray-100 dark:bg-gray-700 rounded cursor-grab active:cursor-grabbing"
                        title="Drag to reorder"
                    >
                        <Bars3Icon className="h-4 w-4 text-gray-500" />
                    </button>

                    {/* Size selector */}
                    <select
                        value={config.size}
                        onChange={(e) => onSizeChange(e.target.value as WidgetConfig['size'])}
                        className="text-xs p-1 bg-gray-100 dark:bg-gray-700 rounded border-none cursor-pointer"
                        title="Widget size"
                    >
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                        <option value="full">Full</option>
                    </select>

                    {/* Visibility toggle */}
                    <button
                        onClick={onToggleVisibility}
                        className="p-1 bg-gray-100 dark:bg-gray-700 rounded"
                        title={config.visible ? 'Hide widget' : 'Show widget'}
                    >
                        {config.visible ? (
                            <EyeIcon className="h-4 w-4 text-gray-500" />
                        ) : (
                            <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                        )}
                    </button>
                </div>
            )}

            {children}
        </div>
    );
}

// --- Widget Settings Panel ---
interface WidgetSettingsPanelProps {
    widgets: WidgetConfig[];
    onToggleWidget: (widgetId: string) => void;
    onResetDefaults: () => void;
    onClose: () => void;
}

function WidgetSettingsPanel({ widgets, onToggleWidget, onResetDefaults, onClose }: WidgetSettingsPanelProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Dashboard Widgets
                    </h3>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                        <XMarkIcon className="h-5 w-5 text-gray-500" />
                    </button>
                </div>

                <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                    {widgets.map(widget => (
                        <div
                            key={widget.id}
                            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                        >
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => onToggleWidget(widget.id)}
                                    className={`p-1 rounded ${widget.visible
                                            ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600'
                                            : 'bg-gray-200 dark:bg-gray-600 text-gray-400'
                                        }`}
                                >
                                    {widget.visible ? (
                                        <EyeIcon className="h-4 w-4" />
                                    ) : (
                                        <EyeSlashIcon className="h-4 w-4" />
                                    )}
                                </button>
                                <span className="text-gray-900 dark:text-white">{widget.title}</span>
                            </div>
                            <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                                {widget.size}
                            </span>
                        </div>
                    ))}
                </div>

                <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={onResetDefaults}
                        className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                        Reset to Defaults
                    </button>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
}

// --- Widget Grid Controls ---
interface WidgetGridControlsProps {
    isEditMode: boolean;
    onToggleEditMode: () => void;
    onOpenSettings: () => void;
}

export function WidgetGridControls({ isEditMode, onToggleEditMode, onOpenSettings }: WidgetGridControlsProps) {
    return (
        <div className="flex items-center gap-2">
            <button
                onClick={onToggleEditMode}
                className={`p-2 rounded-lg transition-colors ${isEditMode
                        ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500'
                    }`}
                title={isEditMode ? 'Exit edit mode' : 'Edit layout'}
            >
                <PencilSquareIcon className="h-5 w-5" />
            </button>
            <button
                onClick={onOpenSettings}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500"
                title="Widget settings"
            >
                <Cog6ToothIcon className="h-5 w-5" />
            </button>
        </div>
    );
}

// --- Main Widget Grid ---
export function WidgetGrid({
    widgets,
    onWidgetsChange,
    renderWidget,
    isEditMode,
    onEditModeChange,
    showSettings: externalShowSettings,
    onShowSettingsChange: externalOnShowSettingsChange
}: WidgetGridProps) {
    const [internalShowSettings, setInternalShowSettings] = useState(false);
    const { toggleWidget, updateWidgetSize, resetToDefaults } = useWidgetLayout();

    // Use external state if provided, otherwise use internal state
    const showSettings = externalShowSettings !== undefined ? externalShowSettings : internalShowSettings;
    const setShowSettings = externalOnShowSettingsChange || setInternalShowSettings;

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    // Sort widgets by order
    const sortedWidgets = useMemo(() =>
        [...widgets].sort((a, b) => a.order - b.order),
        [widgets]
    );

    const handleDragEnd = useCallback((event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const oldIndex = sortedWidgets.findIndex(w => w.id === active.id);
            const newIndex = sortedWidgets.findIndex(w => w.id === over.id);

            const reordered = arrayMove(sortedWidgets, oldIndex, newIndex);
            const updated = reordered.map((w, i) => ({ ...w, order: i }));
            onWidgetsChange(updated);
        }
    }, [sortedWidgets, onWidgetsChange]);

    return (
        <>
            {isEditMode && (
                <div className="mb-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg flex items-center justify-between">
                    <p className="text-sm text-indigo-700 dark:text-indigo-300">
                        <strong>Edit Mode:</strong> Drag widgets to reorder, adjust size, or toggle visibility
                    </p>
                    <button
                        onClick={() => onEditModeChange(false)}
                        className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
                    >
                        Done Editing
                    </button>
                </div>
            )}

            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
            >
                <SortableContext
                    items={sortedWidgets.map(w => w.id)}
                    strategy={rectSortingStrategy}
                >
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {sortedWidgets.map(config => (
                            <SortableWidget
                                key={config.id}
                                config={config}
                                isEditMode={isEditMode}
                                onToggleVisibility={() => toggleWidget(config.id)}
                                onSizeChange={(size) => updateWidgetSize(config.id, size)}
                            >
                                {renderWidget(config)}
                            </SortableWidget>
                        ))}
                    </div>
                </SortableContext>
            </DndContext>

            {showSettings && (
                <WidgetSettingsPanel
                    widgets={sortedWidgets}
                    onToggleWidget={toggleWidget}
                    onResetDefaults={resetToDefaults}
                    onClose={() => setShowSettings(false)}
                />
            )}
        </>
    );
}
