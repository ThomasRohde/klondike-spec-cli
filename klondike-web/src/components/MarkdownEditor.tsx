import { useState, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface MarkdownEditorProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    minHeight?: string;
}

/**
 * Markdown editor with live preview and formatting toolbar.
 * Supports GFM (tables, strikethrough, task lists) and code syntax highlighting.
 */
export function MarkdownEditor({
    value,
    onChange,
    placeholder = 'Write markdown here...',
    className = '',
    minHeight = '200px',
}: MarkdownEditorProps) {
    const [showPreview, setShowPreview] = useState(false);
    const [splitView, setSplitView] = useState(false);

    // Debounced value for preview to avoid performance issues
    const previewValue = useMemo(() => value, [value]);

    const insertText = useCallback((before: string, after: string = '') => {
        const textarea = document.querySelector('[data-markdown-editor]') as HTMLTextAreaElement;
        if (!textarea) return;

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = value.substring(start, end);
        const newText = value.substring(0, start) + before + selectedText + after + value.substring(end);

        onChange(newText);

        // Restore cursor position
        setTimeout(() => {
            textarea.focus();
            const newCursorPos = start + before.length + selectedText.length + after.length;
            textarea.setSelectionRange(newCursorPos, newCursorPos);
        }, 0);
    }, [value, onChange]);

    const handleBold = useCallback(() => insertText('**', '**'), [insertText]);
    const handleItalic = useCallback(() => insertText('_', '_'), [insertText]);
    const handleCode = useCallback(() => insertText('`', '`'), [insertText]);
    const handleCodeBlock = useCallback(() => insertText('\n```\n', '\n```\n'), [insertText]);
    const handleLink = useCallback(() => insertText('[', '](url)'), [insertText]);
    const handleList = useCallback(() => insertText('\n- ', ''), [insertText]);
    const handleNumberedList = useCallback(() => insertText('\n1. ', ''), [insertText]);
    const handleTaskList = useCallback(() => insertText('\n- [ ] ', ''), [insertText]);
    const handleHeading = useCallback(() => insertText('## ', ''), [insertText]);
    const handleQuote = useCallback(() => insertText('\n> ', ''), [insertText]);
    const handleHr = useCallback(() => insertText('\n---\n', ''), [insertText]);

    const toolbarButtons = [
        { icon: 'B', title: 'Bold (Ctrl+B)', onClick: handleBold, className: 'font-bold' },
        { icon: 'I', title: 'Italic (Ctrl+I)', onClick: handleItalic, className: 'italic' },
        { icon: '</>', title: 'Inline Code', onClick: handleCode, className: 'font-mono text-xs' },
        { icon: '{ }', title: 'Code Block', onClick: handleCodeBlock, className: 'font-mono text-xs' },
        { icon: '🔗', title: 'Link', onClick: handleLink },
        { icon: '•', title: 'Bullet List', onClick: handleList },
        { icon: '1.', title: 'Numbered List', onClick: handleNumberedList },
        { icon: '☐', title: 'Task List', onClick: handleTaskList },
        { icon: 'H', title: 'Heading', onClick: handleHeading, className: 'font-bold' },
        { icon: '"', title: 'Quote', onClick: handleQuote },
        { icon: '—', title: 'Horizontal Rule', onClick: handleHr },
    ];

    return (
        <div className={`markdown-editor border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
            {/* Toolbar */}
            <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-0.5">
                    {toolbarButtons.map((btn, i) => (
                        <button
                            key={i}
                            type="button"
                            title={btn.title}
                            onClick={btn.onClick}
                            className={`px-2 py-1 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors ${btn.className || ''}`}
                        >
                            {btn.icon}
                        </button>
                    ))}
                </div>
                <div className="flex-1" />
                <div className="flex items-center gap-1 border-l border-gray-300 dark:border-gray-600 pl-2">
                    <button
                        type="button"
                        title="Toggle Split View"
                        onClick={() => { setSplitView(!splitView); setShowPreview(false); }}
                        className={`px-2 py-1 text-sm rounded transition-colors ${splitView
                            ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300'
                            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                            }`}
                    >
                        ⧉
                    </button>
                    <button
                        type="button"
                        title="Toggle Preview"
                        onClick={() => { setShowPreview(!showPreview); setSplitView(false); }}
                        className={`px-2 py-1 text-sm rounded transition-colors ${showPreview
                            ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300'
                            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                            }`}
                    >
                        👁
                    </button>
                </div>
            </div>

            {/* Editor/Preview Area */}
            <div className={`${splitView ? 'flex' : ''}`} style={{ minHeight }}>
                {/* Editor */}
                {!showPreview && (
                    <textarea
                        data-markdown-editor
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={placeholder}
                        className={`${splitView ? 'w-1/2' : 'w-full'} h-full p-3 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500`}
                        style={{ minHeight }}
                    />
                )}

                {/* Divider for split view */}
                {splitView && (
                    <div className="w-px bg-gray-200 dark:bg-gray-700" />
                )}

                {/* Preview */}
                {(showPreview || splitView) && (
                    <div
                        className={`${splitView ? 'w-1/2' : 'w-full'} p-3 bg-gray-50 dark:bg-gray-800 overflow-auto`}
                        style={{ minHeight }}
                    >
                        {previewValue ? (
                            <MarkdownPreview content={previewValue} />
                        ) : (
                            <p className="text-gray-400 dark:text-gray-500 italic">
                                Nothing to preview
                            </p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

interface MarkdownPreviewProps {
    content: string;
    className?: string;
}

/**
 * Standalone markdown preview component.
 * Renders markdown with GFM support and syntax highlighting.
 */
export function MarkdownPreview({ content, className = '' }: MarkdownPreviewProps) {
    return (
        <div className={`prose prose-sm dark:prose-invert max-w-none text-gray-900 dark:text-gray-100 ${className}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                    // Custom link handling
                    a: ({ children, href, ...props }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 dark:text-indigo-400 hover:underline"
                            {...props}
                        >
                            {children}
                        </a>
                    ),
                    // Custom code block styling
                    code: ({ children, className, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                            <code
                                className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono text-pink-600 dark:text-pink-400"
                                {...props}
                            >
                                {children}
                            </code>
                        ) : (
                            <code className={className} {...props}>
                                {children}
                            </code>
                        );
                    },
                    // Task list items
                    input: (props) => (
                        <input
                            type="checkbox"
                            disabled
                            className="mr-2 accent-indigo-600"
                            {...props}
                        />
                    ),
                    // Tables
                    table: ({ children, ...props }) => (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" {...props}>
                                {children}
                            </table>
                        </div>
                    ),
                    th: ({ children, ...props }) => (
                        <th
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider bg-gray-50 dark:bg-gray-800"
                            {...props}
                        >
                            {children}
                        </th>
                    ),
                    td: ({ children, ...props }) => (
                        <td
                            className="px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
                            {...props}
                        >
                            {children}
                        </td>
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
