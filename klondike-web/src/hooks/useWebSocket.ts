import { useEffect, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  payload: any
}

export function useWebSocket(url: string) {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  useEffect(() => {
    const websocket = new WebSocket(url)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        setLastMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [url])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (ws && isConnected) {
      ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [ws, isConnected])

  return {
    isConnected,
    lastMessage,
    sendMessage,
  }
}
