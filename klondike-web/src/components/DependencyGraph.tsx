/**
 * Feature dependency graph visualization using @xyflow/react
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
    MarkerType,
    Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useNavigate } from 'react-router-dom';
import {
    CheckCircleIcon,
    PlayCircleIcon,
    NoSymbolIcon,
    ClockIcon,
    ArrowsPointingOutIcon,
    ArrowsPointingInIcon,
} from '@heroicons/react/24/outline';
import { getApiBaseUrl } from '../utils/api';
import { Skeleton } from './Skeleton';

interface FeatureData {
    id: string;
    description: string;
    status: 'not-started' | 'in-progress' | 'blocked' | 'verified';
    category: string;
    priority: number;
    dependencies?: string[];
    notes?: string;
}

// Parse dependencies from notes field
function parseDependencies(notes: string | undefined): string[] {
    if (!notes) return [];

    const deps: string[] = [];
    // Match patterns like "depends on F001", "F001, F002", "requires F003"
    const patterns = [
        /(?:depends on|requires|needs|blocked by)\s*(F\d{3}(?:\s*,\s*F\d{3})*)/gi,
        /(?:Dependencies?:?\s*)(F\d{3}(?:\s*,\s*F\d{3})*)/gi,
    ];

    for (const pattern of patterns) {
        let match;
        while ((match = pattern.exec(notes)) !== null) {
            const ids = match[1].split(/\s*,\s*/);
            for (const id of ids) {
                if (id.match(/^F\d{3}$/)) {
                    deps.push(id);
                }
            }
        }
    }

    return [...new Set(deps)];
}

// Node colors by status
const statusColors = {
    'verified': { bg: '#dcfce7', border: '#22c55e', text: '#15803d' },
    'in-progress': { bg: '#dbeafe', border: '#3b82f6', text: '#1d4ed8' },
    'blocked': { bg: '#fee2e2', border: '#ef4444', text: '#b91c1c' },
    'not-started': { bg: '#f3f4f6', border: '#9ca3af', text: '#4b5563' },
};

const statusIcons = {
    'verified': CheckCircleIcon,
    'in-progress': PlayCircleIcon,
    'blocked': NoSymbolIcon,
    'not-started': ClockIcon,
};

// Custom node component
interface FeatureNodeProps {
    data: {
        feature: FeatureData;
        onClick: () => void;
    };
    selected: boolean;
}

function FeatureNode({ data, selected }: FeatureNodeProps) {
    const { feature, onClick } = data;
    const colors = statusColors[feature.status];
    const StatusIcon = statusIcons[feature.status];

    return (
        <div
            onClick={onClick}
            className={`px-3 py-2 rounded-lg cursor-pointer transition-all hover:shadow-md ${selected ? 'ring-2 ring-indigo-500 ring-offset-2' : ''
                }`}
            style={{
                backgroundColor: colors.bg,
                border: `2px solid ${colors.border}`,
                minWidth: '150px',
                maxWidth: '200px',
            }}
        >
            <div className="flex items-center gap-2 mb-1">
                <StatusIcon className="w-4 h-4" style={{ color: colors.text }} />
                <span className="font-bold text-sm" style={{ color: colors.text }}>
                    {feature.id}
                </span>
            </div>
            <div
                className="text-xs line-clamp-2"
                style={{ color: colors.text }}
                title={feature.description}
            >
                {feature.description}
            </div>
        </div>
    );
}

// Register custom node types
const nodeTypes = {
    feature: FeatureNode,
};

// Layout algorithm - simple layered layout
function layoutNodes(
    features: FeatureData[],
    dependencyMap: Map<string, string[]>
): Node[] {
    // Calculate layers based on dependencies
    const layers = new Map<string, number>();
    const visited = new Set<string>();

    function getLayer(id: string, depth = 0): number {
        if (depth > 100) return 0; // Prevent infinite loops
        if (layers.has(id)) return layers.get(id)!;
        if (visited.has(id)) return 0; // Circular dependency

        visited.add(id);
        const deps = dependencyMap.get(id) || [];
        const depLayers = deps.map(d => getLayer(d, depth + 1));
        const layer = deps.length === 0 ? 0 : Math.max(...depLayers) + 1;
        layers.set(id, layer);

        return layer;
    }

    // Calculate layers for all features
    for (const feature of features) {
        getLayer(feature.id);
    }

    // Group features by layer
    const layerGroups = new Map<number, FeatureData[]>();
    for (const feature of features) {
        const layer = layers.get(feature.id) || 0;
        if (!layerGroups.has(layer)) {
            layerGroups.set(layer, []);
        }
        layerGroups.get(layer)!.push(feature);
    }

    // Position nodes
    const nodes: Node[] = [];
    const layerKeys = [...layerGroups.keys()].sort((a, b) => a - b);
    const xSpacing = 280;
    const ySpacing = 120;

    for (const layer of layerKeys) {
        const layerFeatures = layerGroups.get(layer)!;
        const yOffset = -(layerFeatures.length - 1) * ySpacing / 2;

        for (let i = 0; i < layerFeatures.length; i++) {
            const feature = layerFeatures[i];
            nodes.push({
                id: feature.id,
                type: 'feature',
                position: { x: layer * xSpacing, y: yOffset + i * ySpacing },
                sourcePosition: Position.Right,
                targetPosition: Position.Left,
                data: { feature, onClick: () => { } },
            });
        }
    }

    return nodes;
}

// Create edges from dependencies
function createEdges(dependencyMap: Map<string, string[]>): Edge[] {
    const edges: Edge[] = [];

    for (const [featureId, deps] of dependencyMap) {
        for (const depId of deps) {
            edges.push({
                id: `${depId}-${featureId}`,
                source: depId,
                target: featureId,
                type: 'smoothstep',
                animated: false,
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    width: 15,
                    height: 15,
                },
                style: { stroke: '#9ca3af', strokeWidth: 2 },
            });
        }
    }

    return edges;
}

// Legend component
function GraphLegend() {
    return (
        <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 z-10">
            <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Legend</div>
            <div className="space-y-1">
                {Object.entries(statusColors).map(([status, colors]) => {
                    const Icon = statusIcons[status as keyof typeof statusIcons];
                    return (
                        <div key={status} className="flex items-center gap-2">
                            <div
                                className="w-4 h-4 rounded flex items-center justify-center"
                                style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}` }}
                            >
                                <Icon className="w-3 h-3" style={{ color: colors.text }} />
                            </div>
                            <span className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                                {status.replace('-', ' ')}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// Filter controls
interface GraphFiltersProps {
    showOnlyWithDeps: boolean;
    onToggleDeps: () => void;
    selectedCategory: string;
    categories: string[];
    onCategoryChange: (cat: string) => void;
}

function GraphFilters({
    showOnlyWithDeps,
    onToggleDeps,
    selectedCategory,
    categories,
    onCategoryChange,
}: GraphFiltersProps) {
    return (
        <div className="absolute top-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 z-10">
            <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-xs text-gray-700 dark:text-gray-300">
                    <input
                        type="checkbox"
                        checked={showOnlyWithDeps}
                        onChange={onToggleDeps}
                        className="rounded border-gray-300"
                    />
                    Only with dependencies
                </label>

                <select
                    value={selectedCategory}
                    onChange={(e) => onCategoryChange(e.target.value)}
                    className="text-xs px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                    <option value="all">All Categories</option>
                    {categories.map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                    ))}
                </select>
            </div>
        </div>
    );
}

// Main component
export function DependencyGraph() {
    const navigate = useNavigate();
    const [features, setFeatures] = useState<FeatureData[]>([]);
    const [loading, setLoading] = useState(true);
    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
    const [showOnlyWithDeps, setShowOnlyWithDeps] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [isFullscreen, setIsFullscreen] = useState(false);

    const categories = useMemo(() =>
        [...new Set(features.map(f => f.category))].sort(),
        [features]
    );

    useEffect(() => {
        fetchFeatures();
    }, []);

    async function fetchFeatures() {
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/features`);
            const data = await response.json();
            setFeatures(data.features);
        } catch (error) {
            console.error('Failed to fetch features:', error);
        } finally {
            setLoading(false);
        }
    }

    // Build dependency map and layout
    useEffect(() => {
        if (features.length === 0) return;

        // Parse dependencies from notes
        const dependencyMap = new Map<string, string[]>();
        for (const feature of features) {
            const deps = [
                ...(feature.dependencies || []),
                ...parseDependencies(feature.notes),
            ];
            // Only include valid feature IDs
            const validDeps = deps.filter(d => features.some(f => f.id === d));
            if (validDeps.length > 0) {
                dependencyMap.set(feature.id, validDeps);
            }
        }

        // Filter features
        let filteredFeatures = features;

        if (showOnlyWithDeps) {
            const featuresWithDeps = new Set<string>();
            for (const [id, deps] of dependencyMap) {
                featuresWithDeps.add(id);
                for (const dep of deps) {
                    featuresWithDeps.add(dep);
                }
            }
            filteredFeatures = features.filter(f => featuresWithDeps.has(f.id));
        }

        if (selectedCategory !== 'all') {
            filteredFeatures = filteredFeatures.filter(f => f.category === selectedCategory);
        }

        // Layout nodes
        const layoutedNodes = layoutNodes(filteredFeatures, dependencyMap);

        // Add click handlers
        const nodesWithHandlers = layoutedNodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                onClick: () => navigate(`/task/${node.id}`),
            },
        }));

        setNodes(nodesWithHandlers);
        setEdges(createEdges(dependencyMap));
    }, [features, showOnlyWithDeps, selectedCategory, setNodes, setEdges, navigate]);

    const toggleFullscreen = useCallback(() => {
        setIsFullscreen(!isFullscreen);
    }, [isFullscreen]);

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <Skeleton width={250} height={32} />
                </div>
                <Skeleton height={500} />
            </div>
        );
    }

    return (
        <div className={isFullscreen ? 'fixed inset-0 z-50 bg-white dark:bg-gray-900' : ''}>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                    Dependency Graph
                </h2>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                        {nodes.length} nodes • {edges.length} edges
                    </span>
                    <button
                        onClick={toggleFullscreen}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
                        title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                    >
                        {isFullscreen ? (
                            <ArrowsPointingInIcon className="w-5 h-5" />
                        ) : (
                            <ArrowsPointingOutIcon className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>

            <div className={`relative ${isFullscreen ? 'h-[calc(100vh-80px)]' : 'h-[calc(100vh-12rem)]'} bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden`}>
                <GraphFilters
                    showOnlyWithDeps={showOnlyWithDeps}
                    onToggleDeps={() => setShowOnlyWithDeps(!showOnlyWithDeps)}
                    selectedCategory={selectedCategory}
                    categories={categories}
                    onCategoryChange={setSelectedCategory}
                />
                <GraphLegend />

                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    fitView
                    minZoom={0.1}
                    maxZoom={2}
                    defaultEdgeOptions={{
                        type: 'smoothstep',
                    }}
                >
                    <Background />
                    <Controls />
                    <MiniMap
                        nodeColor={(node) => {
                            const feature = (node.data as { feature: FeatureData }).feature;
                            return statusColors[feature.status].border;
                        }}
                        className="!bg-white dark:!bg-gray-800"
                    />
                </ReactFlow>
            </div>
        </div>
    );
}
