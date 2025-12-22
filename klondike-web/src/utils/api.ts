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
