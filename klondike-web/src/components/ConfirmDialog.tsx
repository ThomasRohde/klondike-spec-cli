import { useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useFocusTrap } from '../utils/accessibility';

interface ConfirmDialogProps {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    title: string;
    message: string | ReactNode;
    confirmText?: string;
    cancelText?: string;
    variant?: 'danger' | 'warning' | 'default';
}

/**
 * Confirmation dialog for destructive actions.
 * Keyboard accessible with Enter to confirm and Escape to cancel.
 */
export function ConfirmDialog({
    isOpen,
    onConfirm,
    onCancel,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'default',
}: ConfirmDialogProps) {
    const containerRef = useFocusTrap<HTMLDivElement>(isOpen);

    // Handle keyboard events
    useEffect(() => {
        if (!isOpen) return;

        function handleKeyDown(e: KeyboardEvent) {
            if (e.key === 'Escape') {
                e.preventDefault();
                onCancel();
            } else if (e.key === 'Enter' && !e.shiftKey) {
                // Only confirm if not focused on cancel button
                const activeElement = document.activeElement;
                if (!activeElement?.getAttribute('data-cancel-button')) {
                    e.preventDefault();
                    onConfirm();
                }
            }
        }

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onConfirm, onCancel]);

    // Prevent body scroll
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

    const variantStyles = {
        danger: {
            icon: 'bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400',
            button: 'bg-red-600 hover:bg-red-700 text-white',
        },
        warning: {
            icon: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-600 dark:text-yellow-400',
            button: 'bg-yellow-600 hover:bg-yellow-700 text-white',
        },
        default: {
            icon: 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400',
            button: 'bg-indigo-600 hover:bg-indigo-700 text-white',
        },
    };

    const styles = variantStyles[variant];

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
                onClick={onCancel}
                aria-hidden="true"
            />

            {/* Dialog */}
            <div className="flex min-h-full items-center justify-center p-4">
                <div
                    ref={containerRef}
                    role="alertdialog"
                    aria-modal="true"
                    aria-labelledby="confirm-dialog-title"
                    aria-describedby="confirm-dialog-message"
                    className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6"
                >
                    <div className="flex items-start gap-4">
                        {/* Icon */}
                        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${styles.icon}`}>
                            <ExclamationTriangleIcon className="w-6 h-6" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <h3
                                id="confirm-dialog-title"
                                className="text-lg font-semibold text-gray-900 dark:text-white"
                            >
                                {title}
                            </h3>
                            <p
                                id="confirm-dialog-message"
                                className="mt-2 text-sm text-gray-600 dark:text-gray-400"
                            >
                                {message}
                            </p>
                        </div>

                        {/* Close button */}
                        <button
                            onClick={onCancel}
                            aria-label="Close"
                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                            <XMarkIcon className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Actions */}
                    <div className="mt-6 flex gap-3 justify-end">
                        <button
                            onClick={onCancel}
                            data-cancel-button="true"
                            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                        >
                            {cancelText}
                        </button>
                        <button
                            onClick={onConfirm}
                            autoFocus
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${styles.button}`}
                        >
                            {confirmText}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

interface UndoToastState {
    id: string;
    message: string;
    onUndo: () => void;
    timeRemaining: number;
}

/**
 * Hook for managing undo-able actions.
 * Shows a toast with countdown timer and undo button.
 */
export function useUndoableAction() {
    const [pendingAction, setPendingAction] = useState<UndoToastState | null>(null);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const executeRef = useRef<(() => void) | null>(null);

    const clearTimer = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
    }, []);

    const executeAction = useCallback(() => {
        if (executeRef.current) {
            executeRef.current();
            executeRef.current = null;
        }
        clearTimer();
        setPendingAction(null);
    }, [clearTimer]);

    const cancelAction = useCallback(() => {
        if (pendingAction?.onUndo) {
            pendingAction.onUndo();
        }
        clearTimer();
        setPendingAction(null);
        executeRef.current = null;
    }, [pendingAction, clearTimer]);

    const startUndoableAction = useCallback((
        message: string,
        executeCallback: () => void,
        undoCallback: () => void,
        durationSeconds: number = 5
    ) => {
        // Clear any existing action
        clearTimer();

        const id = Date.now().toString();
        executeRef.current = executeCallback;

        setPendingAction({
            id,
            message,
            onUndo: undoCallback,
            timeRemaining: durationSeconds,
        });

        // Start countdown
        timerRef.current = setInterval(() => {
            setPendingAction(prev => {
                if (!prev) return null;

                const newTime = prev.timeRemaining - 1;
                if (newTime <= 0) {
                    executeAction();
                    return null;
                }

                return { ...prev, timeRemaining: newTime };
            });
        }, 1000);
    }, [clearTimer, executeAction]);

    // Cleanup on unmount
    useEffect(() => {
        return () => clearTimer();
    }, [clearTimer]);

    return {
        pendingAction,
        startUndoableAction,
        executeAction,
        cancelAction,
    };
}

interface UndoToastProps {
    message: string;
    timeRemaining: number;
    onUndo: () => void;
    onDismiss: () => void;
}

/**
 * Toast component with undo option and countdown timer.
 */
export function UndoToast({ message, timeRemaining, onUndo, onDismiss }: UndoToastProps) {
    return (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
            <div className="bg-gray-900 dark:bg-gray-700 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-4">
                <span className="text-sm">{message}</span>

                {/* Countdown */}
                <div className="flex items-center gap-2">
                    <div className="relative w-8 h-8">
                        <svg className="w-8 h-8 -rotate-90">
                            <circle
                                cx="16"
                                cy="16"
                                r="14"
                                stroke="currentColor"
                                strokeWidth="2"
                                fill="none"
                                className="text-gray-600"
                            />
                            <circle
                                cx="16"
                                cy="16"
                                r="14"
                                stroke="currentColor"
                                strokeWidth="2"
                                fill="none"
                                className="text-indigo-400"
                                strokeDasharray={`${(timeRemaining / 5) * 88} 88`}
                                strokeLinecap="round"
                            />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-xs font-medium">
                            {timeRemaining}
                        </span>
                    </div>

                    <button
                        onClick={onUndo}
                        className="px-3 py-1 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 rounded transition-colors"
                    >
                        Undo
                    </button>

                    <button
                        onClick={onDismiss}
                        aria-label="Dismiss"
                        className="p-1 text-gray-400 hover:text-white rounded"
                    >
                        <XMarkIcon className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}

/**
 * Confirmation with built-in undo support.
 * Shows dialog, then undo toast with timer.
 */
interface UseConfirmWithUndoOptions {
    title: string;
    message: string;
    confirmText?: string;
    variant?: 'danger' | 'warning' | 'default';
    undoMessage?: string;
    undoDuration?: number;
}

export function useConfirmWithUndo() {
    const [dialogConfig, setDialogConfig] = useState<UseConfirmWithUndoOptions | null>(null);
    const [isOpen, setIsOpen] = useState(false);
    const actionRef = useRef<{
        onConfirm: () => void;
        onUndo: () => void;
    } | null>(null);

    const { pendingAction, startUndoableAction, cancelAction, executeAction } = useUndoableAction();

    const confirm = useCallback((
        options: UseConfirmWithUndoOptions,
        onConfirm: () => void,
        onUndo: () => void
    ) => {
        setDialogConfig(options);
        actionRef.current = { onConfirm, onUndo };
        setIsOpen(true);
    }, []);

    const handleConfirm = useCallback(() => {
        setIsOpen(false);
        const action = actionRef.current;

        if (action && dialogConfig) {
            startUndoableAction(
                dialogConfig.undoMessage || 'Action performed',
                action.onConfirm,
                action.onUndo,
                dialogConfig.undoDuration || 5
            );
        }
    }, [dialogConfig, startUndoableAction]);

    const handleCancel = useCallback(() => {
        setIsOpen(false);
        actionRef.current = null;
    }, []);

    return {
        confirm,
        dialogProps: dialogConfig ? {
            isOpen,
            onConfirm: handleConfirm,
            onCancel: handleCancel,
            title: dialogConfig.title,
            message: dialogConfig.message,
            confirmText: dialogConfig.confirmText,
            variant: dialogConfig.variant,
        } : null,
        undoToastProps: pendingAction ? {
            message: pendingAction.message,
            timeRemaining: pendingAction.timeRemaining,
            onUndo: cancelAction,
            onDismiss: executeAction,
        } : null,
    };
}
