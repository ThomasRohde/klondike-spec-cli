import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { apiCall, getApiBaseUrl } from '../utils/api'
import { MarkdownEditor, MarkdownPreview } from './MarkdownEditor'
import { Breadcrumbs } from './Breadcrumbs'
import {
    CheckCircleIcon,
    XCircleIcon,
    ClockIcon,
    ArrowPathIcon,
    PlayIcon,
    StopIcon,
    PencilIcon,
    CheckIcon,
    XMarkIcon
} from '@heroicons/react/24/outline'

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
    lastWorkedOn: string | null
}

const statusConfig = {
    'verified': {
        icon: CheckCircleIcon,
        color: 'text-green-600 dark:text-green-400',
        bg: 'bg-green-50 dark:bg-green-900/40',
        border: 'border-green-200 dark:border-green-800',
        label: 'Verified'
    },
    'in-progress': {
        icon: ArrowPathIcon,
        color: 'text-blue-600 dark:text-blue-400',
        bg: 'bg-blue-50 dark:bg-blue-900/40',
        border: 'border-blue-200 dark:border-blue-800',
        label: 'In Progress'
    },
    'blocked': {
        icon: XCircleIcon,
        color: 'text-red-600 dark:text-red-400',
        bg: 'bg-red-50 dark:bg-red-900/40',
        border: 'border-red-200 dark:border-red-800',
        label: 'Blocked'
    },
    'not-started': {
        icon: ClockIcon,
        color: 'text-gray-600 dark:text-gray-300',
        bg: 'bg-gray-50 dark:bg-gray-800',
        border: 'border-gray-200 dark:border-gray-700',
        label: 'Not Started'
    }
}

const priorityColors = {
    1: 'text-red-700 bg-red-50 border-red-200 dark:text-red-300 dark:bg-red-900/40 dark:border-red-800',
    2: 'text-orange-700 bg-orange-50 border-orange-200 dark:text-orange-300 dark:bg-orange-900/40 dark:border-orange-800',
    3: 'text-yellow-700 bg-yellow-50 border-yellow-200 dark:text-yellow-300 dark:bg-yellow-900/30 dark:border-yellow-800',
    4: 'text-blue-700 bg-blue-50 border-blue-200 dark:text-blue-300 dark:bg-blue-900/30 dark:border-blue-800',
    5: 'text-gray-700 bg-gray-50 border-gray-200 dark:text-gray-300 dark:bg-gray-800 dark:border-gray-700'
}

export function TaskViewer() {
    const { featureId } = useParams<{ featureId: string }>()
    const navigate = useNavigate()
    const [feature, setFeature] = useState<Feature | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isEditing, setIsEditing] = useState(false)
    const [showBlockModal, setShowBlockModal] = useState(false)
    const [showVerifyModal, setShowVerifyModal] = useState(false)
    const [blockReason, setBlockReason] = useState('')
    const [evidence, setEvidence] = useState('')
    const [actionLoading, setActionLoading] = useState(false)

    // Editable fields
    const [editDescription, setEditDescription] = useState('')
    const [editNotes, setEditNotes] = useState('')
    const [editCategory, setEditCategory] = useState('')
    const [editPriority, setEditPriority] = useState(2)

    useEffect(() => {
        if (featureId) {
            fetchFeature(featureId)
        }
    }, [featureId])

    useEffect(() => {
        if (feature && isEditing) {
            setEditDescription(feature.description)
            setEditNotes(feature.notes || '')
            setEditCategory(feature.category)
            setEditPriority(feature.priority)
        }
    }, [isEditing, feature])

    async function fetchFeature(id: string) {
        try {
            setLoading(true)
            setError(null)
            const response = await fetch(`${getApiBaseUrl()}/api/features/${id}`)
            if (!response.ok) {
                throw new Error('Feature not found')
            }
            const data = await response.json()
            setFeature(data)
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load feature'
            setError(message)
            toast.error(message)
        } finally {
            setLoading(false)
        }
    }

    async function handleStart() {
        if (!feature) return
        try {
            setActionLoading(true)
            const result = await apiCall<{ feature: Feature; warning?: string }>(
                fetch(`${getApiBaseUrl()}/api/features/${feature.id}/start`, {
                    method: 'POST',
                }),
                {
                    loadingMessage: `Starting ${feature.id}...`,
                    successMessage: `${feature.id} started`,
                    errorMessage: 'Failed to start feature'
                }
            )
            if (result.warning) {
                toast(result.warning, { icon: '⚠️' })
            }
            setFeature(result.feature)
        } catch (err) {
            // Error already toasted by apiCall
        } finally {
            setActionLoading(false)
        }
    }

    async function handleBlock() {
        if (!feature || !blockReason.trim()) {
            toast.error('Please provide a reason for blocking')
            return
        }
        try {
            setActionLoading(true)
            const result = await apiCall<{ feature: Feature }>(
                fetch(`${getApiBaseUrl()}/api/features/${feature.id}/block`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason: blockReason })
                }),
                {
                    loadingMessage: `Blocking ${feature.id}...`,
                    successMessage: `${feature.id} marked as blocked`,
                    errorMessage: 'Failed to block feature'
                }
            )
            setFeature(result.feature)
            setShowBlockModal(false)
            setBlockReason('')
        } catch (err) {
            // Error already toasted by apiCall
        } finally {
            setActionLoading(false)
        }
    }

    async function handleVerify() {
        if (!feature || !evidence.trim()) {
            toast.error('Please provide evidence for verification')
            return
        }
        try {
            setActionLoading(true)
            const result = await apiCall<{ feature: Feature }>(
                fetch(`${getApiBaseUrl()}/api/features/${feature.id}/verify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ evidence })
                }),
                {
                    loadingMessage: `Verifying ${feature.id}...`,
                    successMessage: `✅ ${feature.id} verified!`,
                    errorMessage: 'Failed to verify feature'
                }
            )
            setFeature(result.feature)
            setShowVerifyModal(false)
            setEvidence('')
        } catch (err) {
            // Error already toasted by apiCall
        } finally {
            setActionLoading(false)
        }
    }

    async function handleSaveEdit() {
        if (!feature) return
        try {
            setActionLoading(true)
            const result = await apiCall<{ feature: Feature }>(
                fetch(`${getApiBaseUrl()}/api/features/${feature.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        description: editDescription,
                        notes: editNotes || null,
                        category: editCategory,
                        priority: editPriority
                    })
                }),
                {
                    loadingMessage: 'Updating feature...',
                    successMessage: `${feature.id} updated`,
                    errorMessage: 'Failed to update feature'
                }
            )
            setFeature(result.feature)
            setIsEditing(false)
        } catch (err) {
            // Error already toasted by apiCall
        } finally {
            setActionLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
            </div>
        )
    }

    if (error || !feature) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <p className="text-red-800 dark:text-red-300">{error || 'Feature not found'}</p>
                    <button
                        onClick={() => navigate('/specs')}
                        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                    >
                        Back to Specs
                    </button>
                </div>
            </div>
        )
    }

    const StatusIcon = statusConfig[feature.status].icon

    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            {/* Breadcrumbs */}
            <Breadcrumbs />

            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{feature.id}</h1>
                        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${statusConfig[feature.status].bg} ${statusConfig[feature.status].color} ${statusConfig[feature.status].border}`}>
                            <StatusIcon className="w-4 h-4" />
                            {statusConfig[feature.status].label}
                        </div>
                    </div>
                    {isEditing ? (
                        <input
                            type="text"
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    ) : (
                        <p className="text-lg text-gray-700 dark:text-gray-300">{feature.description}</p>
                    )}
                </div>
                <div className="flex gap-2 ml-4">
                    {!isEditing ? (
                        <button
                            onClick={() => setIsEditing(true)}
                            className="p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                            title="Edit feature"
                        >
                            <PencilIcon className="w-5 h-5" />
                        </button>
                    ) : (
                        <>
                            <button
                                onClick={handleSaveEdit}
                                disabled={actionLoading}
                                className="p-2 text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-md transition-colors disabled:opacity-50"
                                title="Save changes"
                            >
                                <CheckIcon className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setIsEditing(false)}
                                disabled={actionLoading}
                                className="p-2 text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md transition-colors disabled:opacity-50"
                                title="Cancel editing"
                            >
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Metadata */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Details</h2>
                <div className="grid grid-cols-3 gap-6">
                    <div>
                        <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Category</label>
                        {isEditing ? (
                            <input
                                type="text"
                                value={editCategory}
                                onChange={(e) => setEditCategory(e.target.value)}
                                className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        ) : (
                            <div className="mt-1 text-gray-900 dark:text-gray-100">{feature.category}</div>
                        )}
                    </div>
                    <div>
                        <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Priority</label>
                        {isEditing ? (
                            <select
                                value={editPriority}
                                onChange={(e) => setEditPriority(parseInt(e.target.value))}
                                className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                <option value={1}>P1 (Critical)</option>
                                <option value={2}>P2 (High)</option>
                                <option value={3}>P3 (Medium)</option>
                                <option value={4}>P4 (Low)</option>
                                <option value={5}>P5 (Nice to have)</option>
                            </select>
                        ) : (
                            <div className="mt-1">
                                <span className={`inline-block px-2 py-1 rounded text-sm font-medium border ${priorityColors[feature.priority as keyof typeof priorityColors]}`}>
                                    P{feature.priority}
                                </span>
                            </div>
                        )}
                    </div>
                    <div>
                        <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Passes Tests</label>
                        <div className="mt-1">
                            <span
                                className={`inline-block px-2 py-1 rounded text-sm font-medium ${feature.passes
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                                }`}
                            >
                                {feature.passes ? 'Yes' : 'No'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Acceptance Criteria */}
            {feature.acceptanceCriteria.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Acceptance Criteria</h2>
                    <ul className="space-y-2">
                        {feature.acceptanceCriteria.map((criteria, idx) => (
                            <li key={idx} className="flex items-start gap-3">
                                <input
                                    type="checkbox"
                                    checked={feature.passes}
                                    readOnly
                                    className="mt-1 w-4 h-4 text-blue-600 dark:text-blue-400 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                                />
                                <span className="text-gray-700 dark:text-gray-300">{criteria}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Notes */}
            {(feature.notes || isEditing) && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notes</h2>
                    {isEditing ? (
                        <MarkdownEditor
                            value={editNotes}
                            onChange={setEditNotes}
                            placeholder="Add implementation notes, dependencies, or gotchas... (Markdown supported)"
                            minHeight="200px"
                        />
                    ) : (
                        <MarkdownPreview content={feature.notes || ''} />
                    )}
                </div>
            )}

            {/* Blocked Reason */}
            {feature.blockedBy && (
                <div className={`rounded-lg p-6 mb-6 border-2 ${statusConfig.blocked.bg} ${statusConfig.blocked.border}`}>
                    <div className="flex items-start gap-3">
                        <XCircleIcon className={`w-6 h-6 ${statusConfig.blocked.color} flex-shrink-0`} />
                        <div>
                            <h2 className={`text-lg font-semibold mb-2 ${statusConfig.blocked.color}`}>Blocked</h2>
                            <p className="text-gray-700 dark:text-gray-200">{feature.blockedBy}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Verification Evidence */}
            {feature.verifiedBy && (
                <div className={`rounded-lg p-6 mb-6 border-2 ${statusConfig.verified.bg} ${statusConfig.verified.border}`}>
                    <div className="flex items-start gap-3">
                        <CheckCircleIcon className={`w-6 h-6 ${statusConfig.verified.color} flex-shrink-0`} />
                        <div className="flex-1">
                            <h2 className={`text-lg font-semibold mb-2 ${statusConfig.verified.color}`}>
                                Verified by {feature.verifiedBy}
                            </h2>
                            {feature.verifiedAt && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                    {new Date(feature.verifiedAt).toLocaleString()}
                                </p>
                            )}
                            {feature.evidenceLinks.length > 0 && (
                                <div>
                                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Evidence:</p>
                                    <ul className="list-disc list-inside space-y-1">
                                        {feature.evidenceLinks.map((evidence, idx) => (
                                            <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">{evidence}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            {!isEditing && (
                <div className="flex gap-3 mb-6">
                    {feature.status !== 'in-progress' && feature.status !== 'verified' && (
                        <button
                            onClick={handleStart}
                            disabled={actionLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                        >
                            <PlayIcon className="w-5 h-5" />
                            Start Feature
                        </button>
                    )}
                    {feature.status !== 'blocked' && feature.status !== 'verified' && (
                        <button
                            onClick={() => setShowBlockModal(true)}
                            disabled={actionLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                        >
                            <StopIcon className="w-5 h-5" />
                            Block Feature
                        </button>
                    )}
                    {feature.status !== 'verified' && (
                        <button
                            onClick={() => setShowVerifyModal(true)}
                            disabled={actionLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                        >
                            <CheckCircleIcon className="w-5 h-5" />
                            Verify Feature
                        </button>
                    )}
                </div>
            )}

            {/* Block Modal */}
            {showBlockModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Block Feature</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Provide a reason for blocking this feature. This will help track why progress was stopped.
                        </p>
                        <textarea
                            value={blockReason}
                            onChange={(e) => setBlockReason(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent mb-4"
                            placeholder="e.g., Waiting for API endpoint, blocked by upstream dependency..."
                        />
                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => {
                                    setShowBlockModal(false)
                                    setBlockReason('')
                                }}
                                disabled={actionLoading}
                                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleBlock}
                                disabled={actionLoading || !blockReason.trim()}
                                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                            >
                                {actionLoading ? 'Blocking...' : 'Block Feature'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Verify Modal */}
            {showVerifyModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Verify Feature</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Provide evidence of completion. This can include test results, screenshots, or descriptions of verification steps.
                        </p>
                        <textarea
                            value={evidence}
                            onChange={(e) => setEvidence(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent mb-4"
                            placeholder="e.g., Manual testing completed, All unit tests passing, Screenshot: /docs/feature-demo.png"
                        />
                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => {
                                    setShowVerifyModal(false)
                                    setEvidence('')
                                }}
                                disabled={actionLoading}
                                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleVerify}
                                disabled={actionLoading || !evidence.trim()}
                                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                            >
                                {actionLoading ? 'Verifying...' : 'Verify Feature'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Back Button */}
            <button
                onClick={() => navigate('/specs')}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
                ← Back to Specs
            </button>
        </div>
    )
}
