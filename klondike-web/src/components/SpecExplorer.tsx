import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircleIcon, XCircleIcon, ClockIcon, ArrowPathIcon, PlusIcon, PlayIcon, NoSymbolIcon, TableCellsIcon, Squares2X2Icon, ArrowsUpDownIcon } from '@heroicons/react/24/outline'
import { AddFeatureForm } from './AddFeatureForm'
import { ExpandableFeatureCard } from './ExpandableFeatureCard'
import { getApiBaseUrl, apiCall } from '../utils/api'
import { FeatureListSkeleton, Skeleton } from './Skeleton'
import { EmptyFeaturesState, EmptySearchState } from './EmptyStates'
import { BulkActionsToolbar, SelectAllCheckbox, SelectionCheckbox, clearSelection, useSelection } from './BulkActions'
import { FeatureDndContext, SortableItem, SaveStatus, useFeatureOrdering } from './DragDropFeatures'
import { PrintButton } from './PrintView'

interface Feature {
    id: string
    description: string
    category: string
    priority: number
    status: 'not-started' | 'in-progress' | 'blocked' | 'verified'
    passes: boolean
    acceptanceCriteria: string[]
    notes: string | null
    blockedBy: string | null
    verifiedBy: string | null
    verifiedAt: string | null
    evidenceLinks: string[]
}

interface FeaturesResponse {
    features: Feature[]
    total: number
}

const statusConfig = {
    'verified': { icon: CheckCircleIcon, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/50', label: 'Verified' },
    'in-progress': { icon: ArrowPathIcon, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/50', label: 'In Progress' },
    'blocked': { icon: XCircleIcon, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/50', label: 'Blocked' },
    'not-started': { icon: ClockIcon, color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-50 dark:bg-gray-700', label: 'Not Started' }
}

const priorityColors = {
    1: 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/50',
    2: 'text-orange-700 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/50',
    3: 'text-yellow-700 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/50',
    4: 'text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/50',
    5: 'text-gray-700 dark:text-gray-400 bg-gray-50 dark:bg-gray-700'
}

export function SpecExplorer() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const [features, setFeatures] = useState<Feature[]>([])
    const [filteredFeatures, setFilteredFeatures] = useState<Feature[]>([])
    const [loading, setLoading] = useState(true)
    const [searchText, setSearchText] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'all')

    useEffect(() => {
        // Update status filter when query params change
        const status = searchParams.get('status')
        if (status) {
            setStatusFilter(status)
        }
    }, [searchParams])
    const [categoryFilter, setCategoryFilter] = useState<string>('all')
    const [isAddFormOpen, setIsAddFormOpen] = useState(false)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')
    const [reorderMode, setReorderMode] = useState(false)

    // Track selection
    const selectedIds = useSelection()
    const filteredIds = filteredFeatures.map(f => f.id)

    // Drag and drop ordering
    const { orderedFeatures, isSaving, handleReorder } = useFeatureOrdering(
        filteredFeatures.map(f => ({
            id: f.id,
            description: f.description,
            priority: f.priority,
            status: f.status,
        })),
        { onRefresh: fetchFeatures }
    )

    // Extract unique categories from features
    const categories = Array.from(new Set(features.map(f => f.category))).sort()

    useEffect(() => {
        fetchFeatures()
    }, [])

    useEffect(() => {
        // Apply filters
        let filtered = features

        if (statusFilter !== 'all') {
            filtered = filtered.filter(f => f.status === statusFilter)
        }

        if (categoryFilter !== 'all') {
            filtered = filtered.filter(f => f.category === categoryFilter)
        }

        if (searchText) {
            const search = searchText.toLowerCase()
            filtered = filtered.filter(f =>
                f.id.toLowerCase().includes(search) ||
                f.description.toLowerCase().includes(search) ||
                (f.notes && f.notes.toLowerCase().includes(search))
            )
        }

        setFilteredFeatures(filtered)
        // Clear selection when filters change
        clearSelection()
    }, [features, statusFilter, categoryFilter, searchText])

    async function fetchFeatures() {
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/features`)
            const data: FeaturesResponse = await response.json()
            setFeatures(data.features)
            setFilteredFeatures(data.features)
        } catch (error) {
            console.error('Failed to fetch features:', error)
        } finally {
            setLoading(false)
        }
    }

    function handleFeatureAdded(featureId: string) {
        setSuccessMessage(`Feature ${featureId} created successfully!`)
        fetchFeatures() // Refresh the list
        setTimeout(() => setSuccessMessage(null), 5000) // Clear message after 5 seconds
    }

    async function handleQuickStart(e: React.MouseEvent, featureId: string) {
        e.stopPropagation() // Prevent row click navigation
        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/features/${featureId}/start`, { method: 'POST' }),
                { successMessage: `${featureId} started!`, errorMessage: `Failed to start ${featureId}` }
            )
            fetchFeatures()
        } catch {
            // Error already toasted by apiCall
        }
    }

    async function handleQuickVerify(e: React.MouseEvent, featureId: string) {
        e.stopPropagation()
        const evidence = window.prompt('Enter verification evidence:')
        if (!evidence) return
        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/features/${featureId}/verify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ evidence })
                }),
                { successMessage: `${featureId} verified!`, errorMessage: `Failed to verify ${featureId}` }
            )
            fetchFeatures()
        } catch {
            // Error already toasted by apiCall
        }
    }

    async function handleQuickBlock(e: React.MouseEvent, featureId: string) {
        e.stopPropagation()
        const reason = window.prompt('Enter block reason:')
        if (!reason) return
        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/features/${featureId}/block`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason })
                }),
                { successMessage: `${featureId} blocked`, errorMessage: `Failed to block ${featureId}` }
            )
            fetchFeatures()
        } catch {
            // Error already toasted by apiCall
        }
    }

    // Card view action handlers
    async function handleCardStart(featureId: string) {
        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/features/${featureId}/start`, { method: 'POST' }),
                { successMessage: `${featureId} started!`, errorMessage: `Failed to start ${featureId}` }
            )
            fetchFeatures()
        } catch {
            // Error already toasted by apiCall
        }
    }

    async function handleCardBlock(featureId: string) {
        const reason = window.prompt('Enter block reason:')
        if (!reason) return
        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/features/${featureId}/block`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason })
                }),
                { successMessage: `${featureId} blocked`, errorMessage: `Failed to block ${featureId}` }
            )
            fetchFeatures()
        } catch {
            // Error already toasted by apiCall
        }
    }

    async function handleCardVerify(featureId: string, checkedCriteria: number[]) {
        const feature = features.find(f => f.id === featureId)
        if (!feature) return

        // Build evidence from checked criteria
        const evidence = checkedCriteria.map(i =>
            `✓ ${feature.acceptanceCriteria[i]}`
        ).join('\n')

        try {
            await apiCall(
                fetch(`${getApiBaseUrl()}/api/features/${featureId}/verify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ evidence: evidence || 'All criteria met' })
                }),
                { successMessage: `${featureId} verified!`, errorMessage: `Failed to verify ${featureId}` }
            )
            fetchFeatures()
        } catch {
            // Error already toasted by apiCall
        }
    }

    function StatusBadge({ status }: { status: Feature['status'] }) {
        const config = statusConfig[status]
        const Icon = config.icon
        return (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
                <Icon className="w-4 h-4" />
                {config.label}
            </span>
        )
    }

    function PriorityBadge({ priority }: { priority: number }) {
        return (
            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${priorityColors[priority as keyof typeof priorityColors]}`}>
                P{priority}
            </span>
        )
    }

    if (loading) {
        return (
            <div className="space-y-6">
                {/* Header skeleton */}
                <div className="flex justify-between items-center">
                    <Skeleton height={32} className="w-48" />
                    <Skeleton width={140} height={40} rounded="lg" />
                </div>

                {/* Filter bar skeleton */}
                <div className="flex gap-4">
                    <Skeleton className="flex-1" height={40} />
                    <Skeleton width={120} height={40} />
                    <Skeleton width={120} height={40} />
                </div>

                {/* Feature list skeleton */}
                <FeatureListSkeleton count={5} />
            </div>
        )
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Spec Explorer</h2>
                <div className="flex items-center gap-2">
                    {/* Reorder toggle */}
                    <button
                        onClick={() => setReorderMode(!reorderMode)}
                        className={`p-2 rounded-md border transition-colors ${reorderMode
                            ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 border-indigo-300 dark:border-indigo-700'
                            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                            }`}
                        title={reorderMode ? 'Exit reorder mode' : 'Enable drag to reorder'}
                    >
                        <ArrowsUpDownIcon className="w-5 h-5" />
                    </button>

                    {/* View toggle */}
                    <div className="flex rounded-md border border-gray-300 dark:border-gray-600 overflow-hidden">
                        <button
                            onClick={() => setViewMode('table')}
                            className={`p-2 ${viewMode === 'table'
                                ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300'
                                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                            title="Table view"
                        >
                            <TableCellsIcon className="w-5 h-5" />
                        </button>
                        <button
                            onClick={() => setViewMode('cards')}
                            className={`p-2 ${viewMode === 'cards'
                                ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300'
                                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                            title="Card view"
                        >
                            <Squares2X2Icon className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Print button */}
                    <PrintButton />

                    <button
                        onClick={() => setIsAddFormOpen(true)}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                        <PlusIcon className="w-5 h-5" />
                        Add Feature
                    </button>
                </div>
            </div>

            {/* Success Message */}
            {successMessage && (
                <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded mb-6">
                    {successMessage}
                </div>
            )}

            {/* Filters */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6 p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Search */}
                    <div>
                        <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Search
                        </label>
                        <input
                            id="search"
                            type="text"
                            placeholder="Search features..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                    </div>

                    {/* Status Filter */}
                    <div>
                        <label htmlFor="status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Status
                        </label>
                        <select
                            id="status"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                            <option value="all">All Statuses</option>
                            <option value="not-started">Not Started</option>
                            <option value="in-progress">In Progress</option>
                            <option value="blocked">Blocked</option>
                            <option value="verified">Verified</option>
                        </select>
                    </div>

                    {/* Category Filter */}
                    <div>
                        <label htmlFor="category" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Category
                        </label>
                        <select
                            id="category"
                            value={categoryFilter}
                            onChange={(e) => setCategoryFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                            <option value="all">All Categories</option>
                            {categories.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                    Showing {filteredFeatures.length} of {features.length} features
                    {selectedIds.size > 0 && ` (${selectedIds.size} selected)`}
                </div>
            </div>

            {/* Bulk Actions Toolbar */}
            <BulkActionsToolbar allIds={filteredIds} onRefresh={fetchFeatures} />

            {/* Features - Table View */}
            {viewMode === 'table' && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-900">
                                <tr>
                                    <th className="px-4 py-3 text-left">
                                        <SelectAllCheckbox allIds={filteredIds} />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        ID
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Description
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Category
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Priority
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {filteredFeatures.map((feature) => (
                                    <tr
                                        key={feature.id}
                                        onClick={() => navigate(`/task/${feature.id}`)}
                                        className="group hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                                    >
                                        <td className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
                                            <SelectionCheckbox id={feature.id} />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                                            {feature.id}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-200">
                                            <div className="max-w-md truncate" title={feature.description}>
                                                {feature.description}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                            {feature.category}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <PriorityBadge priority={feature.priority} />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <StatusBadge status={feature.status} />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                            <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                {/* Show Start button for not-started features */}
                                                {feature.status === 'not-started' && (
                                                    <button
                                                        onClick={(e) => handleQuickStart(e, feature.id)}
                                                        className="p-1.5 rounded-md bg-blue-50 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors btn-press"
                                                        title="Start feature"
                                                    >
                                                        <PlayIcon className="w-4 h-4" />
                                                    </button>
                                                )}
                                                {/* Show Verify button for in-progress features */}
                                                {feature.status === 'in-progress' && (
                                                    <button
                                                        onClick={(e) => handleQuickVerify(e, feature.id)}
                                                        className="p-1.5 rounded-md bg-green-50 dark:bg-green-900/50 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900 transition-colors btn-press"
                                                        title="Verify feature"
                                                    >
                                                        <CheckCircleIcon className="w-4 h-4" />
                                                    </button>
                                                )}
                                                {/* Show Block button for not-started and in-progress features */}
                                                {(feature.status === 'not-started' || feature.status === 'in-progress') && (
                                                    <button
                                                        onClick={(e) => handleQuickBlock(e, feature.id)}
                                                        className="p-1.5 rounded-md bg-red-50 dark:bg-red-900/50 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 transition-colors btn-press"
                                                        title="Block feature"
                                                    >
                                                        <NoSymbolIcon className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {filteredFeatures.length === 0 && features.length === 0 && (
                        <EmptyFeaturesState onAdd={() => setIsAddFormOpen(true)} />
                    )}

                    {filteredFeatures.length === 0 && features.length > 0 && (
                        <EmptySearchState query={searchText || statusFilter || categoryFilter || 'filters'} />
                    )}
                </div>
            )}

            {/* Features - Card View */}
            {viewMode === 'cards' && (
                <FeatureDndContext
                    features={orderedFeatures}
                    onReorder={handleReorder}
                    disabled={!reorderMode}
                >
                    <div className={`space-y-3 ${reorderMode ? 'pl-8' : ''}`}>
                        {orderedFeatures.map((orderedFeature) => {
                            const feature = filteredFeatures.find(f => f.id === orderedFeature.id);
                            if (!feature) return null;
                            return (
                                <SortableItem key={feature.id} id={feature.id} disabled={!reorderMode}>
                                    <ExpandableFeatureCard
                                        feature={feature}
                                        onStart={() => handleCardStart(feature.id)}
                                        onBlock={() => handleCardBlock(feature.id)}
                                        onVerify={(checkedCriteria) => handleCardVerify(feature.id, checkedCriteria)}
                                        onNavigate={() => navigate(`/task/${feature.id}`)}
                                    />
                                </SortableItem>
                            );
                        })}
                        {filteredFeatures.length === 0 && features.length === 0 && (
                            <EmptyFeaturesState onAdd={() => setIsAddFormOpen(true)} />
                        )}

                        {filteredFeatures.length === 0 && features.length > 0 && (
                            <EmptySearchState query={searchText || statusFilter || categoryFilter || 'filters'} />
                        )}
                    </div>
                </FeatureDndContext>
            )}

            {/* Save status indicator */}
            <SaveStatus isSaving={isSaving} />

            {/* Add Feature Modal */}
            <AddFeatureForm
                isOpen={isAddFormOpen}
                onClose={() => setIsAddFormOpen(false)}
                onSuccess={handleFeatureAdded}
            />
        </div>
    )
}
