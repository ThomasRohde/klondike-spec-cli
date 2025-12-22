import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircleIcon, XCircleIcon, ClockIcon, ArrowPathIcon, PlusIcon } from '@heroicons/react/24/outline'
import { AddFeatureForm } from './AddFeatureForm'
import { getApiBaseUrl } from '../utils/api'

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
    'verified': { icon: CheckCircleIcon, color: 'text-green-600', bg: 'bg-green-50', label: 'Verified' },
    'in-progress': { icon: ArrowPathIcon, color: 'text-blue-600', bg: 'bg-blue-50', label: 'In Progress' },
    'blocked': { icon: XCircleIcon, color: 'text-red-600', bg: 'bg-red-50', label: 'Blocked' },
    'not-started': { icon: ClockIcon, color: 'text-gray-600', bg: 'bg-gray-50', label: 'Not Started' }
}

const priorityColors = {
    1: 'text-red-700 bg-red-50',
    2: 'text-orange-700 bg-orange-50',
    3: 'text-yellow-700 bg-yellow-50',
    4: 'text-blue-700 bg-blue-50',
    5: 'text-gray-700 bg-gray-50'
}

export function SpecExplorer() {
    const navigate = useNavigate()
    const [features, setFeatures] = useState<Feature[]>([])
    const [filteredFeatures, setFilteredFeatures] = useState<Feature[]>([])
    const [loading, setLoading] = useState(true)
    const [searchText, setSearchText] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [categoryFilter, setCategoryFilter] = useState<string>('all')
    const [isAddFormOpen, setIsAddFormOpen] = useState(false)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)

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
            <div className="flex items-center justify-center h-64">
                <div className="text-gray-500">Loading features...</div>
            </div>
        )
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900">Spec Explorer</h2>
                <button
                    onClick={() => setIsAddFormOpen(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    <PlusIcon className="w-5 h-5" />
                    Add Feature
                </button>
            </div>

            {/* Success Message */}
            {successMessage && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
                    {successMessage}
                </div>
            )}

            {/* Filters */}
            <div className="bg-white rounded-lg shadow mb-6 p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Search */}
                    <div>
                        <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                            Search
                        </label>
                        <input
                            id="search"
                            type="text"
                            placeholder="Search features..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Status Filter */}
                    <div>
                        <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                            Status
                        </label>
                        <select
                            id="status"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                        <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                            Category
                        </label>
                        <select
                            id="category"
                            value={categoryFilter}
                            onChange={(e) => setCategoryFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">All Categories</option>
                            {categories.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="mt-3 text-sm text-gray-600">
                    Showing {filteredFeatures.length} of {features.length} features
                </div>
            </div>

            {/* Features Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    ID
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Description
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Category
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Priority
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredFeatures.map((feature) => (
                                <tr
                                    key={feature.id}
                                    onClick={() => navigate(`/task/${feature.id}`)}
                                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                                >
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {feature.id}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900">
                                        <div className="max-w-md truncate" title={feature.description}>
                                            {feature.description}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {feature.category}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <PriorityBadge priority={feature.priority} />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <StatusBadge status={feature.status} />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {filteredFeatures.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                        No features match your filters
                    </div>
                )}
            </div>

            {/* Add Feature Modal */}
            <AddFeatureForm
                isOpen={isAddFormOpen}
                onClose={() => setIsAddFormOpen(false)}
                onSuccess={handleFeatureAdded}
            />
        </div>
    )
}
