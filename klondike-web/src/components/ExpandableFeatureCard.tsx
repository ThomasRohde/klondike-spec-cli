import { useState, useCallback } from 'react';
import { 
    ChevronDownIcon, 
    ChevronUpIcon,
    PlayIcon,
    StopIcon,
    CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { MarkdownPreview } from './MarkdownEditor';

interface Feature {
    id: string;
    description: string;
    category: string;
    priority: number;
    status: 'not-started' | 'in-progress' | 'blocked' | 'verified';
    passes: boolean;
    acceptanceCriteria: string[];
    notes: string | null;
    blockedBy: string | null;
    verifiedBy: string | null;
    verifiedAt: string | null;
    evidenceLinks: string[];
}

interface ExpandableFeatureCardProps {
    feature: Feature;
    onStart?: () => void;
    onBlock?: () => void;
    onVerify?: (checkedCriteria: number[]) => void;
    onNavigate?: () => void;
    isLoading?: boolean;
}

const statusColors = {
    'verified': 'border-l-green-500 bg-green-50 dark:bg-green-900/20',
    'in-progress': 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20',
    'blocked': 'border-l-red-500 bg-red-50 dark:bg-red-900/20',
    'not-started': 'border-l-gray-300 bg-white dark:bg-gray-800',
};

const statusBadges = {
    'verified': 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
    'in-progress': 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
    'blocked': 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
    'not-started': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

const priorityColors = {
    1: 'text-red-700 bg-red-50 dark:bg-red-900/30 dark:text-red-300',
    2: 'text-orange-700 bg-orange-50 dark:bg-orange-900/30 dark:text-orange-300',
    3: 'text-yellow-700 bg-yellow-50 dark:bg-yellow-900/30 dark:text-yellow-300',
    4: 'text-blue-700 bg-blue-50 dark:bg-blue-900/30 dark:text-blue-300',
    5: 'text-gray-700 bg-gray-50 dark:bg-gray-700 dark:text-gray-300',
};

/**
 * Expandable feature card with inline details and acceptance criteria checklist.
 * Click to expand, showing full details with interactive checkboxes.
 */
export function ExpandableFeatureCard({
    feature,
    onStart,
    onBlock,
    onVerify,
    onNavigate,
    isLoading = false,
}: ExpandableFeatureCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [checkedCriteria, setCheckedCriteria] = useState<Set<number>>(() => {
        // If already verified, check all criteria
        if (feature.status === 'verified') {
            return new Set(feature.acceptanceCriteria.map((_, i) => i));
        }
        return new Set();
    });

    const toggleExpanded = useCallback(() => {
        setIsExpanded(prev => !prev);
    }, []);

    const toggleCriterion = useCallback((index: number) => {
        setCheckedCriteria(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    }, []);

    const handleVerify = useCallback(() => {
        if (onVerify) {
            onVerify(Array.from(checkedCriteria));
        }
    }, [onVerify, checkedCriteria]);

    const allCriteriaChecked = feature.acceptanceCriteria.length > 0 && 
        checkedCriteria.size === feature.acceptanceCriteria.length;

    return (
        <div 
            className={`
                border-l-4 rounded-lg shadow-sm overflow-hidden transition-all duration-200
                ${statusColors[feature.status]}
                ${isExpanded ? 'ring-2 ring-indigo-500/30' : 'hover:shadow-md'}
            `}
        >
            {/* Header - always visible */}
            <div 
                className="flex items-center justify-between p-4 cursor-pointer"
                onClick={toggleExpanded}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggleExpanded();
                    }
                }}
                role="button"
                tabIndex={0}
                aria-expanded={isExpanded}
            >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="font-mono text-sm font-semibold text-gray-600 dark:text-gray-400">
                        {feature.id}
                    </span>
                    <span className="text-gray-900 dark:text-gray-100 truncate">
                        {feature.description}
                    </span>
                </div>
                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${priorityColors[feature.priority as keyof typeof priorityColors]}`}>
                        P{feature.priority}
                    </span>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${statusBadges[feature.status]}`}>
                        {feature.status}
                    </span>
                    {isExpanded ? (
                        <ChevronUpIcon className="w-5 h-5 text-gray-400" />
                    ) : (
                        <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                    )}
                </div>
            </div>

            {/* Expanded content */}
            <div 
                className={`
                    transition-all duration-200 ease-in-out overflow-hidden
                    ${isExpanded ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'}
                `}
            >
                <div className="px-4 pb-4 pt-0 border-t border-gray-200 dark:border-gray-700">
                    {/* Category */}
                    <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                        <span className="font-medium">Category:</span> {feature.category}
                    </div>

                    {/* Acceptance Criteria Checklist */}
                    {feature.acceptanceCriteria.length > 0 && (
                        <div className="mt-4">
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                                Acceptance Criteria
                                <span className="ml-2 text-xs font-normal text-gray-500">
                                    ({checkedCriteria.size}/{feature.acceptanceCriteria.length})
                                </span>
                            </h4>
                            <ul className="space-y-2">
                                {feature.acceptanceCriteria.map((criterion, index) => (
                                    <li key={index} className="flex items-start gap-3">
                                        <input
                                            type="checkbox"
                                            id={`${feature.id}-criterion-${index}`}
                                            checked={checkedCriteria.has(index)}
                                            onChange={() => toggleCriterion(index)}
                                            disabled={feature.status === 'verified'}
                                            className="mt-1 w-4 h-4 text-indigo-600 border-gray-300 dark:border-gray-600 rounded focus:ring-indigo-500 disabled:opacity-60"
                                        />
                                        <label 
                                            htmlFor={`${feature.id}-criterion-${index}`}
                                            className={`text-sm cursor-pointer ${
                                                checkedCriteria.has(index)
                                                    ? 'text-gray-500 dark:text-gray-400 line-through'
                                                    : 'text-gray-700 dark:text-gray-300'
                                            }`}
                                        >
                                            {criterion}
                                        </label>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Notes */}
                    {feature.notes && (
                        <div className="mt-4">
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                                Notes
                            </h4>
                            <div className="text-sm bg-gray-50 dark:bg-gray-800 rounded p-3">
                                <MarkdownPreview content={feature.notes} />
                            </div>
                        </div>
                    )}

                    {/* Blocked reason */}
                    {feature.blockedBy && (
                        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                            <h4 className="text-sm font-semibold text-red-800 dark:text-red-300 mb-1">
                                Blocked
                            </h4>
                            <p className="text-sm text-red-700 dark:text-red-400">
                                {feature.blockedBy}
                            </p>
                        </div>
                    )}

                    {/* Verification info */}
                    {feature.verifiedAt && (
                        <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                            <h4 className="text-sm font-semibold text-green-800 dark:text-green-300 mb-1">
                                Verified {feature.verifiedBy && `by ${feature.verifiedBy}`}
                            </h4>
                            <p className="text-xs text-green-600 dark:text-green-400">
                                {new Date(feature.verifiedAt).toLocaleString()}
                            </p>
                            {feature.evidenceLinks.length > 0 && (
                                <ul className="mt-2 list-disc list-inside text-sm text-green-700 dark:text-green-400">
                                    {feature.evidenceLinks.map((link, i) => (
                                        <li key={i}>{link}</li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}

                    {/* Action buttons */}
                    <div className="mt-4 flex gap-2 flex-wrap">
                        {onNavigate && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onNavigate(); }}
                                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                            >
                                View Details
                            </button>
                        )}
                        {feature.status !== 'in-progress' && feature.status !== 'verified' && onStart && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onStart(); }}
                                disabled={isLoading}
                                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
                            >
                                <PlayIcon className="w-4 h-4" />
                                Start
                            </button>
                        )}
                        {feature.status !== 'blocked' && feature.status !== 'verified' && onBlock && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onBlock(); }}
                                disabled={isLoading}
                                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors disabled:opacity-50"
                            >
                                <StopIcon className="w-4 h-4" />
                                Block
                            </button>
                        )}
                        {feature.status !== 'verified' && onVerify && (
                            <button
                                onClick={(e) => { e.stopPropagation(); handleVerify(); }}
                                disabled={isLoading || !allCriteriaChecked}
                                title={allCriteriaChecked ? 'Verify feature' : 'Check all criteria first'}
                                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <CheckCircleIcon className="w-4 h-4" />
                                Verify
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
