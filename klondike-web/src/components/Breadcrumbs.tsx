/**
 * Breadcrumb navigation showing current location hierarchy
 */

import { Link, useLocation, useParams } from 'react-router-dom';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';

interface BreadcrumbItem {
    label: string;
    href?: string;
    icon?: React.ComponentType<{ className?: string }>;
}

const routeLabels: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/specs': 'Spec Explorer',
    '/kanban': 'Kanban Board',
    '/activity': 'Activity Log',
    '/config': 'Configuration',
    '/task': 'Feature Details',
};

export function Breadcrumbs() {
    const location = useLocation();
    const params = useParams();
    
    const breadcrumbs: BreadcrumbItem[] = [
        { label: 'Home', href: '/dashboard', icon: HomeIcon },
    ];
    
    // Build breadcrumbs based on current path
    const pathname = location.pathname;
    
    // Handle /task/:featureId route
    if (pathname.startsWith('/task/') && params.featureId) {
        breadcrumbs.push({
            label: 'Spec Explorer',
            href: '/specs',
        });
        breadcrumbs.push({
            label: params.featureId,
        });
    } 
    // Handle other routes
    else if (pathname !== '/dashboard' && pathname !== '/') {
        const label = routeLabels[pathname] || pathname.slice(1);
        breadcrumbs.push({
            label: label.charAt(0).toUpperCase() + label.slice(1),
        });
    }
    
    // Don't show breadcrumbs on home page
    if (breadcrumbs.length <= 1) {
        return null;
    }
    
    return (
        <nav className="mb-4" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2 text-sm">
                {breadcrumbs.map((crumb, index) => {
                    const isLast = index === breadcrumbs.length - 1;
                    const Icon = crumb.icon;
                    
                    return (
                        <li key={index} className="flex items-center">
                            {index > 0 && (
                                <ChevronRightIcon 
                                    className="w-4 h-4 mx-2 text-gray-400 flex-shrink-0" 
                                    aria-hidden="true"
                                />
                            )}
                            
                            {isLast || !crumb.href ? (
                                <span 
                                    className="text-gray-500 dark:text-gray-400 flex items-center gap-1"
                                    aria-current={isLast ? 'page' : undefined}
                                >
                                    {Icon && <Icon className="w-4 h-4" aria-hidden="true" />}
                                    <span className={Icon ? 'sr-only sm:not-sr-only' : ''}>
                                        {crumb.label}
                                    </span>
                                </span>
                            ) : (
                                <Link
                                    to={crumb.href}
                                    className="text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 flex items-center gap-1 transition-colors"
                                >
                                    {Icon && <Icon className="w-4 h-4" aria-hidden="true" />}
                                    <span className={Icon ? 'sr-only sm:not-sr-only' : ''}>
                                        {crumb.label}
                                    </span>
                                </Link>
                            )}
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
}

// Compact breadcrumb for mobile
export function CompactBreadcrumbs() {
    const location = useLocation();
    const params = useParams();
    
    // Determine parent page
    let parentHref = '/dashboard';
    let parentLabel = 'Dashboard';
    let currentLabel = 'Home';
    
    const pathname = location.pathname;
    
    if (pathname.startsWith('/task/') && params.featureId) {
        parentHref = '/specs';
        parentLabel = 'Specs';
        currentLabel = params.featureId;
    } else if (pathname === '/specs') {
        currentLabel = 'Spec Explorer';
    } else if (pathname === '/kanban') {
        currentLabel = 'Kanban Board';
    } else if (pathname === '/activity') {
        currentLabel = 'Activity Log';
    } else if (pathname === '/config') {
        currentLabel = 'Configuration';
    }
    
    // Don't show on home
    if (pathname === '/dashboard' || pathname === '/') {
        return null;
    }
    
    return (
        <div className="flex items-center gap-2 mb-4 md:hidden">
            <Link
                to={parentHref}
                className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400"
            >
                <ChevronRightIcon className="w-4 h-4 rotate-180" aria-hidden="true" />
                <span>{parentLabel}</span>
            </Link>
            <span className="text-gray-400 dark:text-gray-600">/</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
                {currentLabel}
            </span>
        </div>
    );
}

// Page header with breadcrumbs
interface PageHeaderProps {
    title: string;
    description?: string;
    actions?: React.ReactNode;
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
    return (
        <div className="mb-6">
            <Breadcrumbs />
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        {title}
                    </h1>
                    {description && (
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            {description}
                        </p>
                    )}
                </div>
                {actions && (
                    <div className="flex items-center gap-2">
                        {actions}
                    </div>
                )}
            </div>
        </div>
    );
}
