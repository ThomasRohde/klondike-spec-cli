import { useState, useEffect, useRef } from 'react';
import {
    PrinterIcon,
    XMarkIcon,
    DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { getApiBaseUrl } from '../utils/api';

interface Feature {
    id: string;
    description: string;
    status: string;
    priority: number;
    category: string;
    acceptance_criteria?: string[];
    evidence?: string[];
    notes?: string;
}

interface ProjectStatus {
    project_name: string;
    project_version: string;
    completion_percentage: number;
    feature_counts: {
        total: number;
        verified: number;
        in_progress: number;
        blocked: number;
        not_started: number;
    };
}

interface PrintViewProps {
    onClose: () => void;
}

export function PrintView({ onClose }: PrintViewProps) {
    const [features, setFeatures] = useState<Feature[]>([]);
    const [status, setStatus] = useState<ProjectStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [includeEvidence, setIncludeEvidence] = useState(true);
    const [includeNotes, setIncludeNotes] = useState(true);
    const [includeCriteria, setIncludeCriteria] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const printRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        Promise.all([
            fetch(`${getApiBaseUrl()}/api/features`).then(r => r.json()),
            fetch(`${getApiBaseUrl()}/api/status`).then(r => r.json()),
        ]).then(([featuresData, statusData]) => {
            setFeatures(featuresData.features || featuresData);
            setStatus(statusData);
            setLoading(false);
        }).catch(err => {
            console.error('Failed to load data:', err);
            setLoading(false);
        });
    }, []);

    const handlePrint = () => {
        window.print();
    };

    const filteredFeatures = features.filter(f => 
        statusFilter === 'all' || f.status === statusFilter
    );

    const groupedFeatures = filteredFeatures.reduce((acc, feature) => {
        const key = feature.category || 'Uncategorized';
        if (!acc[key]) acc[key] = [];
        acc[key].push(feature);
        return acc;
    }, {} as Record<string, Feature[]>);

    const statusColors: Record<string, string> = {
        'verified': 'text-green-700 bg-green-100',
        'in-progress': 'text-yellow-700 bg-yellow-100',
        'blocked': 'text-red-700 bg-red-100',
        'not-started': 'text-gray-700 bg-gray-100',
    };

    const today = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });

    if (loading) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                <div className="bg-white rounded-lg p-8">
                    <p>Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 bg-white dark:bg-gray-900 overflow-auto">
            {/* Print-only styles */}
            <style>{`
                @media print {
                    .no-print { display: none !important; }
                    .print-only { display: block !important; }
                    body { background: white !important; }
                    .print-content { 
                        padding: 0 !important; 
                        margin: 0 !important;
                    }
                    @page {
                        margin: 1in;
                        size: letter;
                    }
                }
                @media screen {
                    .print-only { display: none; }
                }
            `}</style>

            {/* Controls (hidden when printing) */}
            <div className="no-print sticky top-0 z-10 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg"
                        >
                            <XMarkIcon className="h-5 w-5" />
                        </button>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Print Preview
                        </h2>
                    </div>
                    
                    <div className="flex items-center gap-4">
                        {/* Filter */}
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
                        >
                            <option value="all">All Statuses</option>
                            <option value="verified">Verified Only</option>
                            <option value="in-progress">In Progress Only</option>
                            <option value="blocked">Blocked Only</option>
                            <option value="not-started">Not Started Only</option>
                        </select>

                        {/* Options */}
                        <div className="flex items-center gap-3">
                            <label className="flex items-center gap-1 text-sm">
                                <input
                                    type="checkbox"
                                    checked={includeCriteria}
                                    onChange={(e) => setIncludeCriteria(e.target.checked)}
                                    className="rounded"
                                />
                                Criteria
                            </label>
                            <label className="flex items-center gap-1 text-sm">
                                <input
                                    type="checkbox"
                                    checked={includeEvidence}
                                    onChange={(e) => setIncludeEvidence(e.target.checked)}
                                    className="rounded"
                                />
                                Evidence
                            </label>
                            <label className="flex items-center gap-1 text-sm">
                                <input
                                    type="checkbox"
                                    checked={includeNotes}
                                    onChange={(e) => setIncludeNotes(e.target.checked)}
                                    className="rounded"
                                />
                                Notes
                            </label>
                        </div>

                        <button
                            onClick={handlePrint}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                        >
                            <PrinterIcon className="h-5 w-5" />
                            Print
                        </button>
                    </div>
                </div>
            </div>

            {/* Print Content */}
            <div ref={printRef} className="print-content max-w-4xl mx-auto p-8 bg-white">
                {/* Header */}
                <header className="mb-8 pb-6 border-b-2 border-gray-900">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">
                                {status?.project_name || 'Project'} Feature Report
                            </h1>
                            <p className="text-gray-600 mt-1">Version {status?.project_version}</p>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-gray-500">Generated</p>
                            <p className="font-medium">{today}</p>
                        </div>
                    </div>
                </header>

                {/* Summary */}
                <section className="mb-8">
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <DocumentTextIcon className="h-5 w-5" />
                        Summary
                    </h2>
                    <div className="grid grid-cols-5 gap-4 mb-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                            <p className="text-2xl font-bold text-gray-900">{status?.feature_counts.total}</p>
                            <p className="text-sm text-gray-600">Total</p>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                            <p className="text-2xl font-bold text-green-700">{status?.feature_counts.verified}</p>
                            <p className="text-sm text-green-600">Verified</p>
                        </div>
                        <div className="text-center p-4 bg-yellow-50 rounded-lg">
                            <p className="text-2xl font-bold text-yellow-700">{status?.feature_counts.in_progress}</p>
                            <p className="text-sm text-yellow-600">In Progress</p>
                        </div>
                        <div className="text-center p-4 bg-red-50 rounded-lg">
                            <p className="text-2xl font-bold text-red-700">{status?.feature_counts.blocked}</p>
                            <p className="text-sm text-red-600">Blocked</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                            <p className="text-2xl font-bold text-gray-700">{status?.feature_counts.not_started}</p>
                            <p className="text-sm text-gray-600">Not Started</p>
                        </div>
                    </div>
                    <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                            className="h-full bg-green-500 transition-all"
                            style={{ width: `${status?.completion_percentage || 0}%` }}
                        />
                    </div>
                    <p className="text-center mt-2 text-sm text-gray-600">
                        {status?.completion_percentage?.toFixed(1)}% Complete
                    </p>
                </section>

                {/* Features by Category */}
                {Object.entries(groupedFeatures).map(([category, categoryFeatures]) => (
                    <section key={category} className="mb-8">
                        <h2 className="text-xl font-bold text-gray-900 mb-4 pb-2 border-b border-gray-300">
                            {category}
                            <span className="text-sm font-normal text-gray-500 ml-2">
                                ({categoryFeatures.length} features)
                            </span>
                        </h2>
                        <div className="space-y-4">
                            {categoryFeatures.map(feature => (
                                <div key={feature.id} className="border-l-4 border-gray-300 pl-4 py-2">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-mono font-bold text-gray-900">
                                            {feature.id}
                                        </span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${statusColors[feature.status] || 'bg-gray-100'}`}>
                                            {feature.status}
                                        </span>
                                        <span className="text-xs text-gray-500">P{feature.priority}</span>
                                    </div>
                                    <p className="text-gray-800 mb-2">{feature.description}</p>
                                    
                                    {includeCriteria && feature.acceptance_criteria && feature.acceptance_criteria.length > 0 && (
                                        <div className="mt-2">
                                            <p className="text-xs font-semibold text-gray-600 uppercase">Acceptance Criteria:</p>
                                            <ul className="list-disc list-inside text-sm text-gray-700 ml-2">
                                                {feature.acceptance_criteria.map((c, i) => (
                                                    <li key={i}>{c}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    
                                    {includeEvidence && feature.evidence && feature.evidence.length > 0 && (
                                        <div className="mt-2">
                                            <p className="text-xs font-semibold text-gray-600 uppercase">Evidence:</p>
                                            <ul className="list-disc list-inside text-sm text-gray-700 ml-2">
                                                {feature.evidence.map((e, i) => (
                                                    <li key={i}>{e}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    
                                    {includeNotes && feature.notes && (
                                        <div className="mt-2">
                                            <p className="text-xs font-semibold text-gray-600 uppercase">Notes:</p>
                                            <p className="text-sm text-gray-700 ml-2">{feature.notes}</p>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </section>
                ))}

                {/* Footer */}
                <footer className="mt-12 pt-4 border-t border-gray-300 text-center text-sm text-gray-500 print-only">
                    <p>Generated by Klondike Spec CLI • {today}</p>
                </footer>
            </div>
        </div>
    );
}

// Button to trigger print view
interface PrintButtonProps {
    className?: string;
}

export function PrintButton({ className = '' }: PrintButtonProps) {
    const [showPrintView, setShowPrintView] = useState(false);

    return (
        <>
            <button
                onClick={() => setShowPrintView(true)}
                className={`flex items-center gap-2 px-3 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors ${className}`}
                title="Print feature report"
            >
                <PrinterIcon className="h-5 w-5" />
                <span className="hidden sm:inline">Print</span>
            </button>
            
            {showPrintView && <PrintView onClose={() => setShowPrintView(false)} />}
        </>
    );
}
