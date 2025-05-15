/**
 * WebSocket Service for game communication
 * This service manages WebSocket connections to the backend
 */
export default class WebSocketService {
    constructor() {
        this.webSocket = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.connectionCallbacks = [];
        this.messageHandlers = new Map();
        this.retryCount = 0;
        this.maxRetries = 3;
        this.serverUrl = 'ws://localhost:8080/api/ws/connect';
        this.useOfflineMode = false; // Set to false by default since backend appears to be running
        
        // Check if offline mode is explicitly requested
        const mode = this.getUrlParameter('mode');
        if (mode === 'offline') {
            console.log('WebSocketService: Offline mode requested via URL parameter');
            this.useOfflineMode = true;
        }
        
        console.log('WebSocketService: Starting in ' + (this.useOfflineMode ? 'offline' : 'online') + ' mode');
    }
    
    /**
     * Connect to the WebSocket server
     * @param {Object} params - Connection parameters
     * @param {Function} callback - Callback function when connected
     * @returns {Promise} Promise that resolves when connected
     */
    connect(params = {}, callback = null) {
        // If offline mode is enabled, simulate connected state
        if (this.useOfflineMode) {
            console.log('WebSocketService: Using offline mode, simulating connection');
            this.isConnected = true;
            
            // Call the callback with null websocket
            if (callback) callback(null);
            
            // Fire the connection event to any listeners
            this.fireEvent('connection', { status: 'connected', offline: true });
            
            return Promise.resolve(null);
        }
        
        // If already connected, just return
        if (this.isConnected && this.webSocket) {
            if (callback) callback(this.webSocket);
            return Promise.resolve(this.webSocket);
        }
        
        // If currently connecting, add callback to queue
        if (this.isConnecting) {
            if (callback) this.connectionCallbacks.push(callback);
            return new Promise((resolve, reject) => {
                this.connectionCallbacks.push((socket) => resolve(socket));
            });
        }
        
        this.isConnecting = true;
        console.log('WebSocketService: Attempting connection to', this.serverUrl);
        
        // Build the connection URL with parameters
        let url = this.serverUrl;
        const queryParams = [];
        
        // Add default parameters
        if (!params.user_id) params.user_id = 'player_1';
        if (!params.client_id) params.client_id = 'game_ui_' + Date.now();
        
        // Add parameters to URL
        for (const [key, value] of Object.entries(params)) {
            queryParams.push(`${key}=${encodeURIComponent(value)}`);
        }
        
        if (queryParams.length > 0) {
            url += '?' + queryParams.join('&');
        }
        
        // Create new WebSocket connection
        try {
            this.webSocket = new WebSocket(url);
        } catch (error) {
            console.error('WebSocketService: Failed to create WebSocket:', error);
            this.isConnecting = false;
            this.enableOfflineMode();
            return Promise.reject(error);
        }
        
        // Return a promise that resolves when connected
        return new Promise((resolve, reject) => {
            // Add the promise handlers to callbacks
            this.connectionCallbacks.push((socket) => resolve(socket));
            
            // Add the provided callback
            if (callback) this.connectionCallbacks.push(callback);
            
            // Set up WebSocket event handlers
            this.webSocket.onopen = (event) => {
                console.log('WebSocketService: Connected successfully!', event);
                this.isConnected = true;
                this.isConnecting = false;
                this.retryCount = 0;
                
                // Execute all connection callbacks
                for (const cb of this.connectionCallbacks) {
                    cb(this.webSocket);
                }
                this.connectionCallbacks = [];
                
                // Fire the connection event to any listeners
                this.fireEvent('connection', { status: 'connected' });
            };
            
            this.webSocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocketService: Message received:', data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('WebSocketService: Error parsing message:', error);
                }
            };
            
            this.webSocket.onerror = (error) => {
                console.error('WebSocketService: Connection error:', error);
                this.isConnecting = false;
                
                // Fire the error event to any listeners
                this.fireEvent('error', { error });
                
                // Attempt to reconnect if under max retries
                if (this.retryCount < this.maxRetries) {
                    this.retryCount++;
                    console.log(`WebSocketService: Retry attempt ${this.retryCount}/${this.maxRetries}`);
                    setTimeout(() => {
                        this.connect(params);
                    }, 2000); // Retry after 2 seconds
                } else {
                    console.log('WebSocketService: Max retries reached, enabling offline mode');
                    this.enableOfflineMode();
                    // Reject the promise with the error
                    reject(error);
                }
            };
            
            this.webSocket.onclose = (event) => {
                console.log('WebSocketService: Connection closed:', event);
                this.isConnected = false;
                this.isConnecting = false;
                
                // Fire the disconnection event
                this.fireEvent('disconnection', { code: event.code, reason: event.reason });
                
                // Attempt to reconnect if closed unexpectedly
                if (event.code !== 1000) { // 1000 is normal closure
                    if (this.retryCount < this.maxRetries) {
                        this.retryCount++;
                        console.log(`WebSocketService: Reconnect attempt ${this.retryCount}/${this.maxRetries}`);
                        setTimeout(() => {
                            this.connect(params);
                        }, 2000); // Retry after 2 seconds
                    } else {
                        console.log('WebSocketService: Max reconnect attempts reached, enabling offline mode');
                        this.enableOfflineMode();
                    }
                }
            };
            
            // Add a timeout for the connection
            setTimeout(() => {
                if (this.isConnecting) {
                    console.log('WebSocketService: Connection timed out');
                    this.isConnecting = false;
                    this.webSocket.close();
                    this.enableOfflineMode();
                    reject(new Error('Connection timed out'));
                }
            }, 5000); // 5 second timeout
        });
    }
    
    /**
     * Switch to offline mode for fallback functionality
     */
    enableOfflineMode() {
        this.useOfflineMode = true;
        console.log('WebSocketService: Offline mode enabled');
        
        // Notify any listeners that we're in offline mode
        this.fireEvent('connection', { status: 'offline_mode' });
        
        // Run pending callbacks with null socket
        for (const cb of this.connectionCallbacks) {
            cb(null);
        }
        this.connectionCallbacks = [];
    }
    
    /**
     * Get URL parameter for configuration
     */
    getUrlParameter(name) {
        const url = window.location.search;
        const regex = new RegExp(`[?&]${name}(=([^&#]*)|&|#|$)`);
        const results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\+/g, ' '));
    }
    
    /**
     * Send a message through the WebSocket
     * @param {Object} data - The data to send
     * @returns {Boolean} Success status
     */
    send(data) {
        // In offline mode, simulate successful send
        if (this.useOfflineMode) {
            console.log('WebSocketService: Simulating send in offline mode:', data);
            
            // If it's a chat, simulate a response after a delay
            if (data.event_type === 'chat') {
                setTimeout(() => this.simulateResponse(data), 1000);
            }
            
            return true;
        }
        
        if (!this.isConnected || !this.webSocket) {
            console.error('WebSocketService: Cannot send message, not connected');
            return false;
        }
        
        try {
            this.webSocket.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('WebSocketService: Error sending message:', error);
            return false;
        }
    }
    
    /**
     * Simulate a response in offline mode
     */
    simulateResponse(request) {
        if (request.event_type === 'chat') {
            // Extract the character ID and message
            const characterId = request.data.character_id;
            const conversationId = request.data.conversation_id;
            const userMessage = request.data.message.content;
            
            // Generate a response based on the character
            let responseContent = "I'm here to help you. What would you like to know?";
            
            // Character-specific responses
            if (characterId === 'character_iron_man') {
                responseContent = this.getIronManResponse(userMessage);
            } else if (characterId === 'character_thor') {
                responseContent = this.getThorResponse(userMessage);
            }
            
            // Create response event
            const responseEvent = {
                event_type: 'chat',
                data: {
                    message: {
                        role: 'assistant',
                        content: responseContent
                    },
                    conversation_id: conversationId
                },
                sender_id: characterId,
                target_ids: [request.sender_id]
            };
            
            console.log('WebSocketService: Simulating response:', responseEvent);
            
            // Small delay to simulate typing
            setTimeout(() => {
                try {
                    this.handleMessage(responseEvent);
                } catch (e) {
                    console.error("Error handling simulated response:", e);
                }
            }, 1000);
        }
    }
    
    /**
     * Get a simulated response for Iron Man
     */
    getIronManResponse(message) {
        const responses = [
            "I am Iron Man. You know that, right?",
            "Sometimes you gotta run before you can walk.",
            "I'm a genius, billionaire, playboy, philanthropist.",
            "If you're nothing without the suit, then you shouldn't have it.",
            "It's not about me. It's not about you. It's not even about us. It's about legacy."
        ];
        
        // If the message contains specific keywords, return targeted responses
        const lowerMessage = message.toLowerCase();
        if (lowerMessage.includes('suit') || lowerMessage.includes('armor')) {
            return "The suit and I are one. Latest model has all kinds of new features - nanotech, energy redistribution, and a cappuccino maker. Okay, maybe not the last one.";
        } else if (lowerMessage.includes('jarvis') || lowerMessage.includes('friday')) {
            return "JARVIS was my original AI assistant. After Ultron, I developed FRIDAY. They're more than just programs - they're part of the team.";
        } else if (lowerMessage.includes('avenger')) {
            return "The Avengers... Earth's Mightiest Heroes. Not a perfect team, but we try to save what we can. Sometimes that doesn't mean everybody, but you do your best.";
        }
        
        // Otherwise return a random response
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    /**
     * Get a simulated response for Thor
     */
    getThorResponse(message) {
        const responses = [
            "I'm still worthy!",
            "You people are so petty... and tiny.",
            "I notice you've copied my beard.",
            "I went for the head.",
            "Bring me Thanos!"
        ];
        
        // If the message contains specific keywords, return targeted responses
        const lowerMessage = message.toLowerCase();
        if (lowerMessage.includes('mjolnir') || lowerMessage.includes('hammer')) {
            return "Ah, Mjolnir! Whosoever holds this hammer, if he be worthy, shall possess the power of Thor. It was forged in the heart of a dying star.";
        } else if (lowerMessage.includes('asgard')) {
            return "Asgard is not a place, it's a people. Though I do miss the golden halls and the incredible feasts we would have.";
        } else if (lowerMessage.includes('loki')) {
            return "My brother Loki... he's been the God of Mischief, but there's always been more to him. We've had our differences, but he's still my brother.";
        }
        
        // Otherwise return a random response
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    /**
     * Send a chat message
     * @param {String} characterId - The character ID to chat with
     * @param {String} message - The message content
     * @param {String} conversationId - Optional conversation ID
     * @returns {Boolean} Success status
     */
    sendChatMessage(characterId, message, conversationId = null) {
        const payload = {
            event_type: "chat",
            data: {
                message: {
                    role: "user",
                    content: message,
                    metadata: {
                        location: "Avengers Compound",
                        situation: "Game interaction"
                    }
                },
                conversation_id: conversationId || 'conv_' + Date.now(),
                character_id: characterId
            },
            sender_id: "player_1",
            target_ids: [characterId]
        };
        
        return this.send(payload);
    }
    
    /**
     * Add an event handler for specific event types
     * @param {String} eventType - The event type to listen for
     * @param {Function} handler - The handler function
     */
    on(eventType, handler) {
        if (!this.messageHandlers.has(eventType)) {
            this.messageHandlers.set(eventType, []);
        }
        
        this.messageHandlers.get(eventType).push(handler);
    }
    
    /**
     * Remove an event handler
     * @param {String} eventType - The event type
     * @param {Function} handler - The handler to remove
     */
    off(eventType, handler) {
        if (!this.messageHandlers.has(eventType)) return;
        
        const handlers = this.messageHandlers.get(eventType);
        const index = handlers.indexOf(handler);
        
        if (index !== -1) {
            handlers.splice(index, 1);
        }
    }
    
    /**
     * Handle incoming messages
     * @param {Object} data - The message data
     */
    handleMessage(data) {
        const eventType = data.event_type || 'unknown';
        
        // Fire event to specific event handlers
        this.fireEvent(eventType, data);
        
        // Also fire to general message handlers
        this.fireEvent('message', data);
    }
    
    /**
     * Fire an event to all registered handlers
     * @param {String} eventType - The event type
     * @param {Object} data - The event data
     */
    fireEvent(eventType, data) {
        if (this.messageHandlers.has(eventType)) {
            for (const handler of this.messageHandlers.get(eventType)) {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${eventType} handler:`, error);
                }
            }
        }
    }
    
    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.webSocket) {
            this.webSocket.close();
            this.webSocket = null;
        }
        
        this.isConnected = false;
        this.isConnecting = false;
    }
    
    /**
     * Get the connection status
     * @returns {Object} Connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            retryCount: this.retryCount
        };
    }
} 