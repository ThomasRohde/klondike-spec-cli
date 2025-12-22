import { useEffect, useState, useCallback, useRef } from "react";

export interface WebSocketMessage {
    type: string;
    payload: unknown;
}

export function useWebSocket(url: string) {
    const wsRef = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

    useEffect(() => {
        const websocket = new WebSocket(url);
        wsRef.current = websocket;

        websocket.onopen = () => {
            console.log("WebSocket connected");
            setIsConnected(true);
        };

        websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data) as WebSocketMessage;
                setLastMessage(message);
            } catch (error) {
                console.error("Failed to parse WebSocket message:", error);
            }
        };

        websocket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        websocket.onclose = () => {
            console.log("WebSocket disconnected");
            setIsConnected(false);
        };

        return () => {
            websocket.close();
        };
    }, [url]);

    const sendMessage = useCallback(
        (message: WebSocketMessage) => {
            const ws = wsRef.current;
            if (ws && isConnected) {
                ws.send(JSON.stringify(message));
            } else {
                console.warn("WebSocket is not connected");
            }
        },
        [isConnected]
    );

    return {
        isConnected,
        lastMessage,
        sendMessage,
    };
}
