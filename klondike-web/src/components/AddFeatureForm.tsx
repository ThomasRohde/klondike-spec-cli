import { useState, type FormEvent } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'

interface AddFeatureFormProps {
    isOpen: boolean
    onClose: () => void
    onSuccess: (featureId: string) => void
}

interface FormData {
    description: string
    category: string
    priority: number
    acceptanceCriteria: string
    notes: string
}

export function AddFeatureForm({ isOpen, onClose, onSuccess }: AddFeatureFormProps) {
    const [formData, setFormData] = useState<FormData>({
        description: '',
        category: 'core',
        priority: 2,
        acceptanceCriteria: '',
        notes: ''
    })
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault()
        setError(null)

        // Validate description
        if (!formData.description.trim()) {
            setError('Description is required')
            return
        }

        setSubmitting(true)

        try {
            // Parse acceptance criteria - split by newlines or commas
            const criteria = formData.acceptanceCriteria
                .split(/[\n,]+/)
                .map(c => c.trim())
                .filter(c => c.length > 0)

            // Prepare request body
            const body = {
                description: formData.description.trim(),
                category: formData.category || undefined,
                priority: formData.priority,
                acceptance_criteria: criteria.length > 0 ? criteria : undefined,
                notes: formData.notes.trim() || undefined
            }

            const response = await fetch('/api/features', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body)
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.error || 'Failed to create feature')
            }

            // Success!
            onSuccess(data.id)

            // Reset form
            setFormData({
                description: '',
                category: 'core',
                priority: 2,
                acceptanceCriteria: '',
                notes: ''
            })
            onClose()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setSubmitting(false)
        }
    }

    const handleClose = () => {
        if (!submitting) {
            setError(null)
            onClose()
        }
    }

    if (!isOpen) {
        return null
    }

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 z-40"
                onClick={handleClose}
            />

            {/* Modal */}
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
                <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-200">
                        <h3 className="text-2xl font-bold text-gray-900">Add New Feature</h3>
                        <button
                            onClick={handleClose}
                            disabled={submitting}
                            className="text-gray-400 hover:text-gray-600 transition-colors"
                            aria-label="Close"
                        >
                            <XMarkIcon className="w-6 h-6" />
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-6 space-y-4">
                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                                {error}
                            </div>
                        )}

                        {/* Description (Required) */}
                        <div>
                            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                                Description <span className="text-red-500">*</span>
                            </label>
                            <input
                                id="description"
                                type="text"
                                required
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Brief description of the feature"
                                disabled={submitting}
                            />
                        </div>

                        {/* Category */}
                        <div>
                            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                                Category
                            </label>
                            <select
                                id="category"
                                value={formData.category}
                                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={submitting}
                            >
                                <option value="core">Core</option>
                                <option value="ui">UI</option>
                                <option value="api">API</option>
                                <option value="infrastructure">Infrastructure</option>
                                <option value="testing">Testing</option>
                                <option value="docs">Documentation</option>
                                <option value="security">Security</option>
                                <option value="performance">Performance</option>
                            </select>
                        </div>

                        {/* Priority */}
                        <div>
                            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
                                Priority
                            </label>
                            <select
                                id="priority"
                                value={formData.priority}
                                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={submitting}
                            >
                                <option value="1">P1 - Critical</option>
                                <option value="2">P2 - High</option>
                                <option value="3">P3 - Medium</option>
                                <option value="4">P4 - Low</option>
                                <option value="5">P5 - Optional</option>
                            </select>
                        </div>

                        {/* Acceptance Criteria */}
                        <div>
                            <label htmlFor="criteria" className="block text-sm font-medium text-gray-700 mb-1">
                                Acceptance Criteria
                            </label>
                            <textarea
                                id="criteria"
                                value={formData.acceptanceCriteria}
                                onChange={(e) => setFormData({ ...formData, acceptanceCriteria: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                rows={4}
                                placeholder="Enter each criterion on a new line or separated by commas"
                                disabled={submitting}
                            />
                            <p className="mt-1 text-sm text-gray-500">
                                Optional. Separate criteria with new lines or commas.
                            </p>
                        </div>

                        {/* Notes */}
                        <div>
                            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
                                Notes
                            </label>
                            <textarea
                                id="notes"
                                value={formData.notes}
                                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                rows={3}
                                placeholder="Additional notes, implementation details, dependencies, etc."
                                disabled={submitting}
                            />
                            <p className="mt-1 text-sm text-gray-500">
                                Optional. Add context for future implementation.
                            </p>
                        </div>

                        {/* Actions */}
                        <div className="flex justify-end gap-3 pt-4">
                            <button
                                type="button"
                                onClick={handleClose}
                                disabled={submitting}
                                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={submitting}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {submitting ? 'Creating...' : 'Create Feature'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    )
}
