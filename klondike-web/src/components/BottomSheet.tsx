import { useEffect, useRef, type ReactNode } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useFocusTrap } from '../utils/accessibility';

interface BottomSheetProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: ReactNode;
    showHandle?: boolean;
}

/**
 * Mobile-friendly bottom sheet modal.
 * Slides up from the bottom on mobile devices.
 * On desktop, renders as a centered modal.
 */
export function BottomSheet({
    isOpen,
    onClose,
    title,
    children,
    showHandle = true
}: BottomSheetProps) {
    const containerRef = useFocusTrap<HTMLDivElement>(isOpen);
    const contentRef = useRef<HTMLDivElement>(null);

    // Handle escape key
    useEffect(() => {
        if (!isOpen) return;

        function handleKeyDown(e: KeyboardEvent) {
            if (e.key === 'Escape') {
                onClose();
            }
        }

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    // Prevent body scroll when open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
                onClick={onClose}
                aria-hidden="true"
            />

            {/* Sheet container */}
            <div
                ref={containerRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby={title ? 'bottom-sheet-title' : undefined}
                className="
                    absolute bottom-0 left-0 right-0 
                    md:bottom-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2
                    md:max-w-lg md:w-full md:mx-4
                    bg-white dark:bg-gray-800 
                    rounded-t-2xl md:rounded-2xl
                    shadow-xl
                    max-h-[90vh] md:max-h-[80vh]
                    flex flex-col
                    transform transition-transform duration-300 ease-out
                    animate-slide-up md:animate-none
                "
            >
                {/* Handle for mobile drag-to-close */}
                {showHandle && (
                    <div className="flex justify-center pt-3 pb-2 md:hidden">
                        <div className="w-12 h-1.5 bg-gray-300 dark:bg-gray-600 rounded-full" />
                    </div>
                )}

                {/* Header */}
                {title && (
                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                        <h2
                            id="bottom-sheet-title"
                            className="text-lg font-semibold text-gray-900 dark:text-white"
                        >
                            {title}
                        </h2>
                        <button
                            onClick={onClose}
                            aria-label="Close"
                            className="p-2 -mr-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        >
                            <XMarkIcon className="w-5 h-5" />
                        </button>
                    </div>
                )}

                {/* Content */}
                <div
                    ref={contentRef}
                    className="flex-1 overflow-y-auto px-4 py-4"
                >
                    {children}
                </div>
            </div>
        </div>
    );
}

/**
 * Touch-friendly action button for bottom sheets.
 * Minimum 44px touch target per WCAG guidelines.
 */
interface ActionButtonProps {
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'danger';
    children: ReactNode;
    disabled?: boolean;
    fullWidth?: boolean;
}

export function ActionButton({
    onClick,
    variant = 'secondary',
    children,
    disabled = false,
    fullWidth = false
}: ActionButtonProps) {
    const baseClasses = `
        min-h-[44px] min-w-[44px] 
        px-4 py-3 
        font-medium rounded-lg 
        transition-colors 
        disabled:opacity-50 disabled:cursor-not-allowed
        touch-manipulation
    `;

    const variantClasses = {
        primary: 'bg-indigo-600 text-white hover:bg-indigo-700 active:bg-indigo-800',
        secondary: 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600',
        danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800',
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`${baseClasses} ${variantClasses[variant]} ${fullWidth ? 'w-full' : ''}`}
        >
            {children}
        </button>
    );
}
