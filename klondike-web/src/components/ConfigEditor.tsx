import { useState, useEffect } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

interface Config {
    default_category: string
    default_priority: number
    verified_by: string
    progress_output_path: string
    auto_regenerate_progress: boolean
    prd_source: string | null
    klondike_version: string | null
    configured_agents: string[]
}

const COMMON_CATEGORIES = [
    'core',
    'ui',
    'api',
    'testing',
    'infrastructure',
    'docs',
    'security',
    'performance',
    'setup',
    'assets',
]

export function ConfigEditor() {
    const [config, setConfig] = useState<Config | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
    const [formData, setFormData] = useState<Partial<Config>>({})

    const { lastMessage } = useWebSocket('ws://localhost:8765/ws')

    // Load config on mount
    useEffect(() => {
        loadConfig()
    }, [])

    // Listen for WebSocket updates
    useEffect(() => {
        if (lastMessage?.type === 'configChanged') {
            loadConfig()
        }
    }, [lastMessage])

    const loadConfig = async () => {
        try {
            const response = await fetch('/api/config')
            const data = await response.json()
            
            if (data.error) {
                setMessage({ type: 'error', text: data.error })
            } else {
                setConfig(data)
                setFormData(data)
            }
        } catch (error) {
            setMessage({ type: 'error', text: `Failed to load config: ${error}` })
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        setMessage(null)

        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            })

            const result = await response.json()

            if (response.ok && result.success) {
                setConfig(result.config)
                setFormData(result.config)
                setMessage({ type: 'success', text: result.message || 'Configuration saved successfully!' })
            } else {
                setMessage({ type: 'error', text: result.detail || result.error || 'Failed to save configuration' })
            }
        } catch (error) {
            setMessage({ type: 'error', text: `Save failed: ${error}` })
        } finally {
            setSaving(false)
        }
    }

    const handleChange = (field: keyof Config, value: string | number | boolean | string[] | null) => {
        setFormData((prev) => ({ ...prev, [field]: value }))
    }

    const handleAgentsChange = (value: string) => {
        const agents = value.split(',').map((a) => a.trim()).filter((a) => a)
        handleChange('configured_agents', agents)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        )
    }

    if (!config) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-600">Failed to load configuration</p>
            </div>
        )
    }

    return (
        <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Configuration</h2>
            
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 space-y-6">
                    {/* Message Banner */}
                    {message && (
                        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                            <p className="text-sm font-medium">{message.text}</p>
                        </div>
                    )}

                    {/* Feature Defaults Section */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Defaults</h3>
                        <div className="space-y-4">
                            {/* Default Category */}
                            <div>
                                <label htmlFor="default_category" className="block text-sm font-medium text-gray-700 mb-1">
                                    Default Category
                                </label>
                                <select
                                    id="default_category"
                                    value={formData.default_category || ''}
                                    onChange={(e) => handleChange('default_category', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {COMMON_CATEGORIES.map((cat) => (
                                        <option key={cat} value={cat}>
                                            {cat}
                                        </option>
                                    ))}
                                </select>
                                <p className="mt-1 text-sm text-gray-500">
                                    Default category for new features
                                </p>
                            </div>

                            {/* Default Priority */}
                            <div>
                                <label htmlFor="default_priority" className="block text-sm font-medium text-gray-700 mb-1">
                                    Default Priority
                                </label>
                                <input
                                    type="number"
                                    id="default_priority"
                                    min="1"
                                    max="5"
                                    value={formData.default_priority || 2}
                                    onChange={(e) => handleChange('default_priority', parseInt(e.target.value))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="mt-1 text-sm text-gray-500">
                                    Default priority (1=critical, 5=nice-to-have)
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Agent Configuration Section */}
                    <div className="border-t pt-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Configuration</h3>
                        <div className="space-y-4">
                            {/* Verified By */}
                            <div>
                                <label htmlFor="verified_by" className="block text-sm font-medium text-gray-700 mb-1">
                                    Verified By
                                </label>
                                <input
                                    type="text"
                                    id="verified_by"
                                    value={formData.verified_by || ''}
                                    onChange={(e) => handleChange('verified_by', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="mt-1 text-sm text-gray-500">
                                    Identifier for agent verification field
                                </p>
                            </div>

                            {/* Configured Agents */}
                            <div>
                                <label htmlFor="configured_agents" className="block text-sm font-medium text-gray-700 mb-1">
                                    Configured Agents
                                </label>
                                <input
                                    type="text"
                                    id="configured_agents"
                                    value={formData.configured_agents?.join(', ') || ''}
                                    onChange={(e) => handleAgentsChange(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="mt-1 text-sm text-gray-500">
                                    Comma-separated list of AI agents (e.g., copilot, claude)
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Progress Generation Section */}
                    <div className="border-t pt-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Progress Generation</h3>
                        <div className="space-y-4">
                            {/* Progress Output Path */}
                            <div>
                                <label htmlFor="progress_output_path" className="block text-sm font-medium text-gray-700 mb-1">
                                    Progress Output Path
                                </label>
                                <input
                                    type="text"
                                    id="progress_output_path"
                                    value={formData.progress_output_path || ''}
                                    onChange={(e) => handleChange('progress_output_path', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="mt-1 text-sm text-gray-500">
                                    Path where agent progress file is generated
                                </p>
                            </div>

                            {/* Auto Regenerate Progress */}
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    id="auto_regenerate_progress"
                                    checked={formData.auto_regenerate_progress ?? true}
                                    onChange={(e) => handleChange('auto_regenerate_progress', e.target.checked)}
                                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                />
                                <label htmlFor="auto_regenerate_progress" className="ml-2 block text-sm text-gray-700">
                                    Auto-regenerate progress file
                                </label>
                            </div>
                            <p className="text-sm text-gray-500 ml-6">
                                Automatically update progress file when features or sessions change
                            </p>
                        </div>
                    </div>

                    {/* Documentation Section */}
                    <div className="border-t pt-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Documentation</h3>
                        <div className="space-y-4">
                            {/* PRD Source */}
                            <div>
                                <label htmlFor="prd_source" className="block text-sm font-medium text-gray-700 mb-1">
                                    PRD Source
                                </label>
                                <input
                                    type="text"
                                    id="prd_source"
                                    value={formData.prd_source || ''}
                                    onChange={(e) => handleChange('prd_source', e.target.value || null)}
                                    placeholder="https://example.com/prd.md"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="mt-1 text-sm text-gray-500">
                                    Optional link to PRD document for agent context
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Version Info (Read-only) */}
                    {config.klondike_version && (
                        <div className="border-t pt-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
                            <div className="bg-gray-50 rounded-lg p-4">
                                <p className="text-sm text-gray-600">
                                    <span className="font-medium">Klondike Version:</span> {config.klondike_version}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Save Button */}
                    <div className="border-t pt-6 flex justify-end">
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                                saving
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                        >
                            {saving ? 'Saving...' : 'Save Configuration'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
