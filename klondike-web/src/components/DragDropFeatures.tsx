/**
 * Drag and drop feature ordering component using dnd-kit
 */

import { useMemo, useState } from 'react';
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    type DragEndEvent,
    type DragStartEvent,
    DragOverlay,
} from '@dnd-kit/core';
import {
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Bars3Icon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { getApiBaseUrl } from '../utils/api';
import { announce } from '../utils/accessibility';

// Feature type (simplified for DnD)
interface DraggableFeature {
    id: string;
    description: string;
    priority: number;
    status: string;
}

// Sortable row/card wrapper
interface SortableItemProps {
    id: string;
    children: React.ReactNode;
    disabled?: boolean;
}

export function SortableItem({ id, children, disabled = false }: SortableItemProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id, disabled });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
        zIndex: isDragging ? 100 : 'auto',
    };

    return (
        <div ref={setNodeRef} style={style} className="relative group/sortable">
            {/* Drag handle */}
            {!disabled && (
                <div
                    {...attributes}
                    {...listeners}
                    className={`absolute left-0 top-1/2 -translate-y-1/2 -ml-6 p-1 rounded cursor-grab hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 dark:text-gray-500
                        opacity-0 group-hover/sortable:opacity-100
                        transition-opacity focus:opacity-100 z-10`}
                    title="Drag to reorder"
                >
                    <Bars3Icon className="w-4 h-4" />
                </div>
            )}
            {children}
        </div>
    );
}

// Drag overlay for visual feedback during drag
interface DragOverlayItemProps {
    feature: DraggableFeature | null;
}

export function DragOverlayItem({ feature }: DragOverlayItemProps) {
    if (!feature) return null;
    
    return (
        <div className="bg-white dark:bg-gray-800 border-2 border-indigo-500 shadow-xl rounded-lg p-3 opacity-95">
            <div className="flex items-center gap-2">
                <Bars3Icon className="w-4 h-4 text-indigo-500" />
                <span className="font-medium text-gray-900 dark:text-white">
                    {feature.id}
                </span>
                <span className="text-gray-600 dark:text-gray-400 text-sm truncate max-w-xs">
                    {feature.description}
                </span>
            </div>
        </div>
    );
}

// Main DnD wrapper
interface FeatureDndContextProps {
    features: DraggableFeature[];
    onReorder: (reorderedFeatures: DraggableFeature[]) => void;
    children: React.ReactNode;
    disabled?: boolean;
}

export function FeatureDndContext({ features, onReorder, children, disabled = false }: FeatureDndContextProps) {
    const [activeFeature, setActiveFeature] = useState<DraggableFeature | null>(null);
    
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
    
    const featureIds = useMemo(() => features.map(f => f.id), [features]);
    
    function handleDragStart(event: DragStartEvent) {
        const feature = features.find(f => f.id === event.active.id);
        setActiveFeature(feature || null);
        if (feature) {
            announce(`Picked up ${feature.id}`);
        }
    }
    
    function handleDragEnd(event: DragEndEvent) {
        setActiveFeature(null);
        
        const { active, over } = event;
        
        if (!over || active.id === over.id) {
            announce('Drop cancelled');
            return;
        }
        
        const oldIndex = featureIds.indexOf(active.id as string);
        const newIndex = featureIds.indexOf(over.id as string);
        
        if (oldIndex === -1 || newIndex === -1) return;
        
        // Create new order
        const newFeatures = [...features];
        const [movedFeature] = newFeatures.splice(oldIndex, 1);
        newFeatures.splice(newIndex, 0, movedFeature);
        
        onReorder(newFeatures);
        announce(`Dropped ${active.id} at position ${newIndex + 1}`);
    }
    
    if (disabled) {
        return <>{children}</>;
    }
    
    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <SortableContext items={featureIds} strategy={verticalListSortingStrategy}>
                {children}
            </SortableContext>
            <DragOverlay>
                <DragOverlayItem feature={activeFeature} />
            </DragOverlay>
        </DndContext>
    );
}

// Hook to manage feature ordering with optimistic updates
interface UseFeatureOrderingOptions {
    onRefresh: () => void;
}

export function useFeatureOrdering(
    features: DraggableFeature[], 
    options: UseFeatureOrderingOptions
) {
    const [localOrder, setLocalOrder] = useState<DraggableFeature[] | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    
    // Compute ordered features
    const orderedFeatures = localOrder ?? features;
    
    async function handleReorder(newFeatures: DraggableFeature[]) {
        // Optimistic update
        setLocalOrder(newFeatures);
        setIsSaving(true);
        
        try {
            // Assign new priorities based on position (P1-P5 distribution)
            const totalFeatures = newFeatures.length;
            const updates = newFeatures.map((feature, index) => {
                // Distribute features across P1-P5 based on position
                const priority = Math.min(5, Math.max(1, Math.ceil(((index + 1) / totalFeatures) * 5)));
                return {
                    id: feature.id,
                    priority,
                };
            });
            
            // Send updates to API
            const response = await fetch(`${getApiBaseUrl()}/api/features/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order: updates }),
            });
            
            if (!response.ok) {
                throw new Error('Failed to save order');
            }
            
            toast.success('Order saved');
            options.onRefresh();
        } catch {
            // Revert on failure
            setLocalOrder(null);
            toast.error('Failed to save order');
        } finally {
            setIsSaving(false);
            setLocalOrder(null);
        }
    }
    
    return {
        orderedFeatures,
        isSaving,
        handleReorder,
        clearLocalOrder: () => setLocalOrder(null),
    };
}

// Status indicator for saving
interface SaveStatusProps {
    isSaving: boolean;
}

export function SaveStatus({ isSaving }: SaveStatusProps) {
    if (!isSaving) return null;
    
    return (
        <div className="fixed bottom-4 right-4 bg-indigo-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 animate-in slide-in-from-bottom z-50">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>Saving order...</span>
        </div>
    );
}
