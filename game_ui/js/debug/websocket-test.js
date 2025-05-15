/**
 * WebSocket Test Script
 * This script can be used to test WebSocket connections to the backend
 * Updated to use port 8080
 */
import WebSocketService from '../services/WebSocketService.js';

// Create a test function
function testWebSocketConnection() {
    console.log('Starting WebSocket connection test on port 8080...');
    
    // Create a new WebSocket service
    const ws = new WebSocketService();
    
    // Set up event handlers
    ws.on('connection', (data) => {
        console.log('Connected to WebSocket server!', data);
        
        // Send a test message
        const testMessage = {
            event_type: "test",
            data: {
                message: "Hello from the game UI!",
                timestamp: Date.now()
            },
            sender_id: "test_client"
        };
        
        ws.send(testMessage);
        console.log('Test message sent:', testMessage);
    });
    
    ws.on('message', (data) => {
        console.log('Message received:', data);
    });
    
    ws.on('error', (data) => {
        console.error('WebSocket error:', data);
    });
    
    ws.on('disconnection', (data) => {
        console.log('WebSocket disconnected:', data);
    });
    
    // Connect to the server
    ws.connect({
        user_id: 'test_user',
        client_id: 'test_client'
    }).then(() => {
        console.log('WebSocket connection successful!');
        
        // Send a chat message after 2 seconds
        setTimeout(() => {
            const chatMessage = {
                event_type: "chat",
                data: {
                    message: {
                        role: "user",
                        content: "Hello, this is a test message!",
                        metadata: {
                            location: "Test Environment",
                            situation: "Testing"
                        }
                    },
                    conversation_id: 'test_conv_' + Date.now(),
                    character_id: "character_iron_man"
                },
                sender_id: "test_user",
                target_ids: ["character_iron_man"]
            };
            
            ws.send(chatMessage);
            console.log('Chat message sent:', chatMessage);
            
            // Disconnect after 5 seconds
            setTimeout(() => {
                ws.disconnect();
                console.log('Test completed and connection closed.');
            }, 5000);
        }, 2000);
    }).catch(error => {
        console.error('Failed to connect:', error);
    });
}

// Export the test function
export { testWebSocketConnection };

// Auto-run the test if this script is loaded directly
if (typeof window !== 'undefined' && window.location.pathname.includes('websocket-test')) {
    console.log('WebSocket test script loaded directly, running test...');
    testWebSocketConnection();
} 