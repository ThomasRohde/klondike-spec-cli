interface SkeletonProps {
    className?: string;
    width?: string | number;
    height?: string | number;
    rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';
}

/**
 * Skeleton loading placeholder with shimmer animation.
 * Respects prefers-reduced-motion.
 */
export function Skeleton({
    className = '',
    width,
    height,
    rounded = 'md',
}: SkeletonProps) {
    const roundedClass = {
        none: '',
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        full: 'rounded-full',
    }[rounded];

    return (
        <div
            className={`bg-gray-200 dark:bg-gray-700 animate-pulse ${roundedClass} ${className}`}
            style={{
                width: typeof width === 'number' ? `${width}px` : width,
                height: typeof height === 'number' ? `${height}px` : height,
            }}
            aria-hidden="true"
        />
    );
}

/**
 * Skeleton for a feature card.
 */
export function FeatureCardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-3">
            <div className="flex items-center gap-2">
                <Skeleton width={60} height={20} rounded="sm" />
                <Skeleton width={80} height={20} rounded="full" />
            </div>
            <Skeleton height={16} className="w-3/4" />
            <Skeleton height={16} className="w-1/2" />
            <div className="flex gap-2 pt-2">
                <Skeleton width={60} height={24} rounded="sm" />
                <Skeleton width={60} height={24} rounded="sm" />
            </div>
        </div>
    );
}

/**
 * Skeleton for a list of feature cards.
 */
export function FeatureListSkeleton({ count = 3 }: { count?: number }) {
    return (
        <div className="space-y-4">
            {Array.from({ length: count }).map((_, i) => (
                <FeatureCardSkeleton key={i} />
            ))}
        </div>
    );
}

/**
 * Skeleton for the dashboard status cards.
 */
export function DashboardStatsSkeleton() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                    <Skeleton height={20} className="w-1/2 mb-2" />
                    <Skeleton height={40} className="w-1/3" />
                </div>
            ))}
        </div>
    );
}

/**
 * Skeleton for the progress ring section.
 */
export function ProgressRingSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex items-center justify-center gap-8">
            <Skeleton width={160} height={160} rounded="full" />
            <div className="space-y-3">
                <Skeleton height={24} className="w-40" />
                <Skeleton height={16} className="w-32" />
                <div className="flex gap-4 mt-2">
                    <Skeleton width={80} height={16} />
                    <Skeleton width={80} height={16} />
                    <Skeleton width={80} height={16} />
                </div>
            </div>
        </div>
    );
}

/**
 * Full-page loading spinner with optional message.
 */
export function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
    return (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
            <div className="w-10 h-10 border-4 border-indigo-200 dark:border-indigo-900 border-t-indigo-600 dark:border-t-indigo-400 rounded-full animate-spin" />
            <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
        </div>
    );
}

/**
 * Inline loading indicator for buttons.
 */
export function ButtonSpinner({ className = '' }: { className?: string }) {
    return (
        <svg
            className={`animate-spin h-4 w-4 ${className}`}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
        >
            <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
            />
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
        </svg>
    );
}
