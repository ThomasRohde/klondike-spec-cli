import toast from 'react-hot-toast'

/**
 * API utility functions for constructing URLs based on current origin.
 * This ensures the frontend works whether accessed via localhost or 127.0.0.1.
 */

/**
 * Get the base URL for API requests.
 * Uses the current window location to construct the URL, avoiding CORS issues.
 */
export function getApiBaseUrl(): string {
    // In development with Vite, we might be on a different port
    // Check if we're in dev mode (Vite dev server typically runs on 5173)
    if (import.meta.env.DEV && window.location.port === "5173") {
        // Use localhost:8000 for dev server
        return `http://${window.location.hostname}:8000`;
    }
    // In production or when served from the same server, use relative path
    return "";
}

/**
 * Get the WebSocket URL for real-time updates.
 * Uses the current window location to construct the URL, avoiding CORS issues.
 */
export function getWebSocketUrl(path: string): string {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;

    // In development with Vite, we might be on a different port
    if (import.meta.env.DEV && window.location.port === "5173") {
        // Connect to the backend server on port 8000
        return `${protocol}//${window.location.hostname}:8000${path}`;
    }

    // In production, use the same host
    return `${protocol}//${host}${path}`;
}

/**
 * Wrapper for API calls that automatically shows toast notifications
 * for success and error states.
 */
export async function apiCall<T>(
    promise: Promise<Response>,
    options?: {
        successMessage?: string | ((data: T) => string)
        errorMessage?: string
        loadingMessage?: string
    }
): Promise<T> {
    const toastId = options?.loadingMessage
        ? toast.loading(options.loadingMessage)
        : undefined

    try {
        const response = await promise

        if (!response.ok) {
            const errorText = await response.text()
            let errorMessage = options?.errorMessage || 'Operation failed'
            
            try {
                const errorJson = JSON.parse(errorText)
                if (errorJson.detail) {
                    errorMessage = errorJson.detail
                }
            } catch {
                // Not JSON, use default message
            }

            if (toastId) toast.dismiss(toastId)
            toast.error(errorMessage)
            throw new Error(errorMessage)
        }

        const data = await response.json()

        if (toastId) {
            const message = typeof options?.successMessage === 'function'
                ? options.successMessage(data as T)
                : options?.successMessage || 'Success'
            toast.success(message, { id: toastId })
        } else if (options?.successMessage) {
            const message = typeof options.successMessage === 'function'
                ? options.successMessage(data as T)
                : options.successMessage
            toast.success(message)
        }

        return data as T
    } catch (error) {
        if (toastId) toast.dismiss(toastId)
        
        if (error instanceof Error) {
            if (!options?.errorMessage) {
                toast.error(error.message)
            }
            throw error
        }
        
        const message = options?.errorMessage || 'An unexpected error occurred'
        toast.error(message)
        throw new Error(message)
    }
}
