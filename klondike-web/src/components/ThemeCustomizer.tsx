import { useState, useCallback, useSyncExternalStore } from 'react';
import {
    SwatchIcon,
    SunIcon,
    MoonIcon,
    XMarkIcon,
    CheckIcon,
} from '@heroicons/react/24/outline';

// --- Predefined accent colors ---
export const ACCENT_COLORS = [
    { id: 'indigo', name: 'Indigo', primary: '#6366f1', light: '#e0e7ff', dark: '#4338ca' },
    { id: 'blue', name: 'Blue', primary: '#3b82f6', light: '#dbeafe', dark: '#1d4ed8' },
    { id: 'cyan', name: 'Cyan', primary: '#06b6d4', light: '#cffafe', dark: '#0891b2' },
    { id: 'teal', name: 'Teal', primary: '#14b8a6', light: '#ccfbf1', dark: '#0d9488' },
    { id: 'green', name: 'Green', primary: '#22c55e', light: '#dcfce7', dark: '#16a34a' },
    { id: 'yellow', name: 'Yellow', primary: '#eab308', light: '#fef9c3', dark: '#ca8a04' },
    { id: 'orange', name: 'Orange', primary: '#f97316', light: '#ffedd5', dark: '#ea580c' },
    { id: 'red', name: 'Red', primary: '#ef4444', light: '#fee2e2', dark: '#dc2626' },
    { id: 'pink', name: 'Pink', primary: '#ec4899', light: '#fce7f3', dark: '#db2777' },
    { id: 'purple', name: 'Purple', primary: '#a855f7', light: '#f3e8ff', dark: '#9333ea' },
    { id: 'violet', name: 'Violet', primary: '#8b5cf6', light: '#ede9fe', dark: '#7c3aed' },
    { id: 'rose', name: 'Rose', primary: '#f43f5e', light: '#ffe4e6', dark: '#e11d48' },
] as const;

export type AccentColorId = typeof ACCENT_COLORS[number]['id'];
export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeSettings {
    mode: ThemeMode;
    accentColor: AccentColorId;
    customAccent?: string; // For custom color picker
}

// --- Theme Storage ---
const STORAGE_KEY = 'klondike-theme-settings';

let themeCache: ThemeSettings | null = null;
const themeListeners = new Set<() => void>();

function getDefaultTheme(): ThemeSettings {
    return {
        mode: 'system',
        accentColor: 'indigo',
    };
}

function loadTheme(): ThemeSettings {
    if (themeCache) return themeCache;

    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            themeCache = JSON.parse(stored);
            return themeCache!;
        }
    } catch (e) {
        console.warn('Failed to load theme:', e);
    }

    themeCache = getDefaultTheme();
    return themeCache;
}

function saveTheme(settings: ThemeSettings): void {
    themeCache = settings;
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) {
        console.warn('Failed to save theme:', e);
    }
    applyTheme(settings);
    themeListeners.forEach(listener => listener());
}

function subscribeTheme(listener: () => void): () => void {
    themeListeners.add(listener);
    return () => themeListeners.delete(listener);
}

function getThemeSnapshot(): ThemeSettings {
    return loadTheme();
}

// Apply theme to document
function applyTheme(settings: ThemeSettings): void {
    const root = document.documentElement;

    // Apply dark mode
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = settings.mode === 'dark' || (settings.mode === 'system' && prefersDark);

    console.log('Applying theme:', { mode: settings.mode, isDark, prefersDark });

    if (isDark) {
        root.classList.add('dark');
    } else {
        root.classList.remove('dark');
    }

    console.log('Document classes:', root.classList.toString());

    // Apply accent color CSS variables
    const accentConfig = ACCENT_COLORS.find(c => c.id === settings.accentColor);
    if (accentConfig) {
        root.style.setProperty('--accent-primary', accentConfig.primary);
        root.style.setProperty('--accent-light', accentConfig.light);
        root.style.setProperty('--accent-dark', accentConfig.dark);
    } else if (settings.customAccent) {
        root.style.setProperty('--accent-primary', settings.customAccent);
        // Generate light/dark variants (simplified)
        root.style.setProperty('--accent-light', settings.customAccent + '20');
        root.style.setProperty('--accent-dark', settings.customAccent);
    }
}

// Initialize theme on load
export function initializeTheme(): void {
    console.log('Initializing theme...');
    const settings = loadTheme();
    console.log('Loaded theme settings:', settings);
    applyTheme(settings);

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (loadTheme().mode === 'system') {
            applyTheme(loadTheme());
        }
    });
}

// Hook for theme management
export function useTheme() {
    const settings = useSyncExternalStore(subscribeTheme, getThemeSnapshot, getThemeSnapshot);

    const setMode = useCallback((mode: ThemeMode) => {
        saveTheme({ ...loadTheme(), mode });
    }, []);

    const setAccentColor = useCallback((accentColor: AccentColorId) => {
        saveTheme({ ...loadTheme(), accentColor, customAccent: undefined });
    }, []);

    const setCustomAccent = useCallback((color: string) => {
        saveTheme({ ...loadTheme(), customAccent: color });
    }, []);

    const resetToDefaults = useCallback(() => {
        saveTheme(getDefaultTheme());
    }, []);

    const isDark = settings.mode === 'dark' ||
        (settings.mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    return {
        settings,
        isDark,
        setMode,
        setAccentColor,
        setCustomAccent,
        resetToDefaults,
    };
}

// --- Theme Toggle Button ---
interface ThemeToggleProps {
    className?: string;
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
    const { isDark, setMode, settings } = useTheme();

    const toggleTheme = () => {
        if (settings.mode === 'system') {
            setMode(isDark ? 'light' : 'dark');
        } else if (settings.mode === 'dark') {
            setMode('light');
        } else {
            setMode('dark');
        }
    };

    return (
        <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${className}`}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
            {isDark ? (
                <SunIcon className="h-5 w-5 text-yellow-400" />
            ) : (
                <MoonIcon className="h-5 w-5 text-gray-600" />
            )}
        </button>
    );
}

// --- Theme Customization Panel ---
interface ThemeCustomizerProps {
    onClose: () => void;
}

export function ThemeCustomizer({ onClose }: ThemeCustomizerProps) {
    const { settings, setMode, setAccentColor, setCustomAccent, resetToDefaults } = useTheme();
    const [customColor, setCustomColor] = useState(settings.customAccent || '#6366f1');

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                        <SwatchIcon className="h-5 w-5 text-indigo-500" />
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Theme Settings
                        </h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                        <XMarkIcon className="h-5 w-5 text-gray-500" />
                    </button>
                </div>

                <div className="p-4 space-y-6">
                    {/* Color Mode */}
                    <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Color Mode
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                            {(['light', 'dark', 'system'] as ThemeMode[]).map(mode => (
                                <button
                                    key={mode}
                                    onClick={() => setMode(mode)}
                                    className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg border transition-colors ${settings.mode === mode
                                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                                        }`}
                                >
                                    {mode === 'light' && <SunIcon className="h-4 w-4" />}
                                    {mode === 'dark' && <MoonIcon className="h-4 w-4" />}
                                    <span className="capitalize text-sm">{mode}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Accent Color */}
                    <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Accent Color
                        </h4>
                        <div className="grid grid-cols-6 gap-2">
                            {ACCENT_COLORS.map(color => (
                                <button
                                    key={color.id}
                                    onClick={() => setAccentColor(color.id)}
                                    className={`relative w-10 h-10 rounded-lg transition-transform hover:scale-110 ${settings.accentColor === color.id && !settings.customAccent
                                        ? 'ring-2 ring-offset-2 ring-gray-400 dark:ring-gray-500'
                                        : ''
                                        }`}
                                    style={{ backgroundColor: color.primary }}
                                    title={color.name}
                                >
                                    {settings.accentColor === color.id && !settings.customAccent && (
                                        <CheckIcon className="absolute inset-0 m-auto h-5 w-5 text-white" />
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Custom Color Picker */}
                    <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Custom Color
                        </h4>
                        <div className="flex items-center gap-3">
                            <input
                                type="color"
                                value={customColor}
                                onChange={(e) => setCustomColor(e.target.value)}
                                className="w-12 h-12 rounded-lg border-none cursor-pointer"
                            />
                            <input
                                type="text"
                                value={customColor}
                                onChange={(e) => setCustomColor(e.target.value)}
                                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
                                placeholder="#6366f1"
                            />
                            <button
                                onClick={() => setCustomAccent(customColor)}
                                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm"
                            >
                                Apply
                            </button>
                        </div>
                        {settings.customAccent && (
                            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                Using custom color: {settings.customAccent}
                            </p>
                        )}
                    </div>

                    {/* Preview */}
                    <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Preview
                        </h4>
                        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg space-y-3">
                            <div className="flex gap-2">
                                <button
                                    className="px-4 py-2 rounded-lg text-white text-sm"
                                    style={{ backgroundColor: 'var(--accent-primary, #6366f1)' }}
                                >
                                    Primary Button
                                </button>
                                <button
                                    className="px-4 py-2 rounded-lg border text-sm"
                                    style={{
                                        borderColor: 'var(--accent-primary, #6366f1)',
                                        color: 'var(--accent-primary, #6366f1)'
                                    }}
                                >
                                    Secondary
                                </button>
                            </div>
                            <div
                                className="h-2 rounded-full"
                                style={{ backgroundColor: 'var(--accent-primary, #6366f1)' }}
                            />
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={resetToDefaults}
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

// --- Theme Customizer Button ---
interface ThemeCustomizerButtonProps {
    className?: string;
}

export function ThemeCustomizerButton({ className = '' }: ThemeCustomizerButtonProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <>
            <button
                onClick={() => setIsOpen(true)}
                className={`p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${className}`}
                title="Customize theme"
            >
                <SwatchIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>

            {isOpen && <ThemeCustomizer onClose={() => setIsOpen(false)} />}
        </>
    );
}
