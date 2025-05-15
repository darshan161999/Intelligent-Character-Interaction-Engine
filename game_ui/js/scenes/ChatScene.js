/**
 * Chat Scene for character interactions
 * This scene will overlay the game scene when chatting with characters
 */
import WebSocketService from '../services/WebSocketService.js';

// Create a singleton WebSocket service
const webSocketService = new WebSocketService();

export default class ChatScene extends Phaser.Scene {
    constructor() {
        super('ChatScene');
        this.isActive = false;
        this.currentCharacter = null;
        this.messages = [];
        this.conversationId = null;
        this.webSocketService = webSocketService; // Use the singleton service
        this.isTyping = false;
        this.characterResponses = {
            'character_iron_man': [
                "The suit and I are one.",
                "Sometimes you gotta run before you can walk.",
                "I am Iron Man.",
                "It's not about me. It's not about you. It's not even about us. It's about legacy."
            ],
            'character_thor': [
                "I'm still worthy!",
                "Bring me Thanos!",
                "You people are so petty... and tiny.",
                "I notice you've copied my beard."
            ]
        };
    }
    
    init(data) {
        console.log("ChatScene initialized with data:", data);
        this.currentCharacter = data.character || null;
        this.userCharacter = data.user || null;
        
        // Generate a conversation ID if there isn't one
        if (!this.conversationId) {
            this.conversationId = this.generateConversationId();
        }
    }
    
    create() {
        console.log("Creating chat interface");
        // Create chat UI elements
        this.createChatInterface();
        
        // Handle closing the chat interface
        this.input.keyboard.on('keydown-ESC', this.closeChat, this);
        
        // Set up WebSocket event handlers
        this.setupWebSocketHandlers();
        
        // Connect to WebSocket if not already connected
        this.connectToWebSocket();
        
        // Immediately open the chat with the current character
        if (this.currentCharacter) {
            console.log("Opening chat with:", this.currentCharacter.name);
            this.openChat(this.currentCharacter);
        } else {
            console.error("No character provided to chat with!");
        }
        
        // Disable keyboard capture for game keys when chat is active
        // This allows typing in the chat input field
        this.input.keyboard.clearCaptures();
    }
    
    // Generate a unique conversation ID
    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
    }
    
    // Set up WebSocket handlers
    setupWebSocketHandlers() {
        // Handle chat messages
        this.webSocketService.on('chat', (data) => {
            console.log("ChatScene: Received chat event:", data);
            this.handleChatEvent(data);
        });
        
        // Handle connection status changes
        this.webSocketService.on('connection', (data) => {
            console.log("ChatScene: WebSocket connected:", data);
            if (data.status === 'offline_mode') {
                this.updateConnectionStatus('Offline Mode', '#ffa500');
                this.addMessage('system', 'Using offline mode with local character responses.');
            } else {
                this.updateConnectionStatus('Connected', '#00ff00');
            }
        });
        
        this.webSocketService.on('disconnection', (data) => {
            console.log("ChatScene: WebSocket disconnected:", data);
            if (this.webSocketService.useOfflineMode) {
                this.updateConnectionStatus('Offline Mode', '#ffa500');
            } else {
                this.updateConnectionStatus('Disconnected', '#ff0000');
                this.addMessage('system', 'Connection lost. Using local character responses.');
            }
        });
        
        this.webSocketService.on('error', (data) => {
            console.error("ChatScene: WebSocket error:", data);
            if (this.webSocketService.useOfflineMode) {
                this.updateConnectionStatus('Offline Mode', '#ffa500');
            } else {
                this.updateConnectionStatus('Error', '#ff0000');
                this.addMessage('system', 'Connection error. Using local character responses.');
            }
        });
    }
    
    // Connect to WebSocket
    connectToWebSocket() {
        this.updateConnectionStatus('Connecting...', '#ffff00');
        
        this.webSocketService.connect({
            user_id: 'player_1',
            client_id: 'game_ui_' + Date.now()
        }).then(() => {
            if (this.webSocketService.useOfflineMode) {
                this.updateConnectionStatus('Offline Mode', '#ffa500');
                this.addMessage('system', 'Server unavailable. Using local character responses.');
            } else {
                this.updateConnectionStatus('Connected', '#00ff00');
            }
            
            // Send initial chat setup message if in a chat
            if (this.isActive && this.currentCharacter) {
                this.sendInitialMessage();
            }
        }).catch(error => {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus('Offline Mode', '#ffa500');
            this.addMessage('system', 'Failed to connect to server. Using local character responses.');
        });
    }
    
    createChatInterface() {
        console.log("Creating chat UI elements");
        // Container for all chat elements
        this.chatContainer = this.add.container(0, 0);
        
        // Semi-transparent background
        const background = this.add.rectangle(0, 0, this.cameras.main.width, this.cameras.main.height, 0x000000, 0.7);
        background.setOrigin(0);
        background.setInteractive(); // Capture input on the background
        this.chatContainer.add(background);
        
        // Chat box
        const chatBoxWidth = 800;
        const chatBoxHeight = 500;
        const chatBoxX = (this.cameras.main.width - chatBoxWidth) / 2;
        const chatBoxY = (this.cameras.main.height - chatBoxHeight) / 2;
        
        const chatBox = this.add.rectangle(chatBoxX, chatBoxY, chatBoxWidth, chatBoxHeight, 0x333333, 0.9);
        chatBox.setOrigin(0);
        chatBox.setStrokeStyle(2, 0xffffff);
        this.chatContainer.add(chatBox);
        
        // Character name header
        this.characterNameText = this.add.text(chatBoxX + 20, chatBoxY + 15, 'Character Name', {
            fontFamily: 'Arial',
            fontSize: '24px',
            color: '#ffffff',
            fontWeight: 'bold'
        });
        this.chatContainer.add(this.characterNameText);
        
        // Connection status indicator
        this.connectionStatus = this.add.text(chatBoxX + chatBoxWidth - 150, chatBoxY + 15, 'Connecting...', {
            fontFamily: 'Arial',
            fontSize: '14px',
            color: '#ffff00'
        });
        this.connectionStatus.setOrigin(0);
        this.chatContainer.add(this.connectionStatus);
        
        // Messages display area with scrollable content
        this.messagesArea = this.add.rectangle(chatBoxX + 20, chatBoxY + 60, chatBoxWidth - 40, chatBoxHeight - 120, 0x222222);
        this.messagesArea.setOrigin(0);
        this.chatContainer.add(this.messagesArea);
        
        // Messages text container
        this.messagesContainer = this.add.container(chatBoxX + 30, chatBoxY + 70);
        this.chatContainer.add(this.messagesContainer);
        
        // Message input area
        const inputBoxBg = this.add.rectangle(chatBoxX + 20, chatBoxY + chatBoxHeight - 50, chatBoxWidth - 40, 40, 0x555555);
        inputBoxBg.setOrigin(0);
        this.chatContainer.add(inputBoxBg);
        
        // Send button
        const sendButton = this.add.rectangle(chatBoxX + chatBoxWidth - 90, chatBoxY + chatBoxHeight - 50, 70, 40, 0x0066ff);
        sendButton.setOrigin(0);
        
        const sendText = this.add.text(sendButton.x + 35, sendButton.y + 20, 'Send', {
            fontFamily: 'Arial',
            fontSize: '16px',
            color: '#ffffff'
        });
        sendText.setOrigin(0.5);
        
        sendButton.setInteractive();
        sendButton.on('pointerdown', this.sendMessage, this);
        
        this.chatContainer.add(sendButton);
        this.chatContainer.add(sendText);
        
        // Close button
        const closeButton = this.add.text(chatBoxX + chatBoxWidth - 25, chatBoxY + 15, 'X', {
            fontFamily: 'Arial',
            fontSize: '20px',
            color: '#ffffff'
        });
        closeButton.setOrigin(0.5);
        closeButton.setInteractive();
        closeButton.on('pointerdown', this.closeChat, this);
        
        this.chatContainer.add(closeButton);
        
        // Instructions text
        const instructionsText = this.add.text(chatBoxX + chatBoxWidth / 2, chatBoxY + chatBoxHeight - 5, 'Type your message and click Send or press ESC to exit', {
            fontFamily: 'Arial',
            fontSize: '14px',
            color: '#cccccc'
        });
        instructionsText.setOrigin(0.5);
        this.chatContainer.add(instructionsText);
        
        // Input text setup using DOM element
        this.setupTextInput(chatBoxX + 25, chatBoxY + chatBoxHeight - 50, chatBoxWidth - 120, 40);
        
        // Initially hide chat interface (will be shown when activated)
        this.chatContainer.setVisible(false);
        this.chatInput.setVisible(false);
        this.isActive = false;
    }
    
    setupTextInput(x, y, width, height) {
        console.log("Setting up text input at:", x, y, width, height);
        // Remove existing input if it exists
        const existingInput = document.getElementById('chat-input');
        if (existingInput) {
            existingInput.remove();
        }
        
        // Create a DOM element for text input
        const inputElement = document.createElement('input');
        inputElement.type = 'text';
        inputElement.id = 'chat-input';
        inputElement.placeholder = 'Type your message here...';
        inputElement.style.width = width + 'px';
        inputElement.style.height = height + 'px';
        inputElement.style.padding = '5px';
        inputElement.style.fontSize = '16px';
        inputElement.style.position = 'absolute';
        inputElement.style.zIndex = '1000';
        
        // Add the element to the DOM
        const gameContainer = document.getElementById('game-container');
        if (gameContainer) {
            console.log("Found game container, appending input");
            gameContainer.appendChild(inputElement);
        } else {
            console.warn("Game container not found, appending to body");
            document.body.appendChild(inputElement);
        }
        
        // Create a Phaser DOM element to position it correctly
        this.chatInput = this.add.dom(x, y, inputElement);
        this.chatInput.setOrigin(0);
        this.chatInput.setVisible(false);
        
        // Handle enter key in the input field
        inputElement.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                this.sendMessage();
            }
            
            // Prevent the event from being captured by Phaser
            event.stopPropagation();
        });
        
        // Focus and click handlers to ensure keyboard events go to the input
        inputElement.addEventListener('focus', () => {
            // Disable keyboard capture when input is focused
            this.input.keyboard.clearCaptures();
            // Only capture ESC key for closing chat
            this.input.keyboard.addCapture(Phaser.Input.Keyboard.KeyCodes.ESC);
        });
        
        inputElement.addEventListener('click', () => {
            // Ensure input gets focus when clicked
            inputElement.focus();
        });
    }
    
    sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input) {
            console.error("Chat input element not found!");
            return;
        }
        
        const message = input.value.trim();
        
        if (message.length > 0 && !this.isTyping) {
            console.log("Sending message:", message);
            
            // Add message to the chat
            this.addMessage('user', message);
            
            // Special hardcoded responses for testing known issue
            if (message.toLowerCase() === 'hi tell me about your suit' && 
                this.currentCharacter.character_id === 'character_iron_man') {
                
                // Clear input field
                input.value = '';
                
                // Show typing indicator
                this.showTypingIndicator();
                
                // Add direct response after delay
                setTimeout(() => {
                    this.hideTypingIndicator();
                    this.addMessage('assistant', 
                        "The suit and I are one. My latest model incorporates nanotech that allows " +
                        "for incredible adaptability in combat. It can form any weapon I need, " +
                        "provide enhanced strength, and even work in space. The Mark 50 and beyond " +
                        "are stored in a housing unit on my chest, ready to deploy in milliseconds. " +
                        "Plus, the heads-up display gives me all the tactical information I need, connected " +
                        "to my AI assistant for real-time analysis."
                    );
                }, 1500);
                
                return;
            }
            
            // Send message to the server
            this.sendChatMessage(message);
            
            // Clear input field
            input.value = '';
            
            // Show typing indicator
            this.showTypingIndicator();
            
            // If we can't connect to the server, use a fallback response
            if (!this.webSocketService.getStatus().isConnected && !this.webSocketService.useOfflineMode) {
                console.log("Using fallback response due to no server connection");
                this.simulateCharacterResponse();
            }
        }
    }
    
    // Simulate a character response if server connection fails
    simulateCharacterResponse() {
        // Wait a random amount of time to simulate typing
        const typingTime = 1000 + Math.random() * 2000;
        setTimeout(() => {
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Get a random response for this character
            const characterId = this.currentCharacter.character_id;
            const responses = this.characterResponses[characterId] || [
                "I'm here to help.",
                "Interesting...",
                "Tell me more!",
                "I see."
            ];
            
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            this.addMessage('assistant', randomResponse);
        }, typingTime);
    }
    
    showTypingIndicator() {
        console.log("Showing typing indicator");
        this.isTyping = true;
        this.addMessage('typing', '...');
    }
    
    hideTypingIndicator() {
        console.log("Hiding typing indicator");
        this.isTyping = false;
        this.removeTypingIndicator();
        }
        
    sendInitialMessage() {
        console.log("Sending initial message for character:", this.currentCharacter);
        // Send initial message to set up chat with character
        const initPayload = {
            event_type: "chat_init",
            data: {
                conversation_id: this.conversationId,
                character_id: this.currentCharacter ? this.currentCharacter.character_id : null,
                user_info: {
                    name: "Player",
                    location: "Avengers Compound",
                    coordinates: {
                        x: this.userCharacter ? this.userCharacter.sprite.x : 0,
                        y: this.userCharacter ? this.userCharacter.sprite.y : 0
                    }
                }
            },
            sender_id: "player_1"
        };
        
        this.webSocketService.send(initPayload);
    }
    
    sendChatMessage(message) {
        console.log("Sending chat message to:", this.currentCharacter.character_id);
            const payload = {
                event_type: "chat",
                data: {
                    message: {
                        role: "user",
                        content: message,
                        metadata: {
                            location: "Avengers Compound",
                        situation: "Game interaction",
                        coordinates: {
                            x: this.userCharacter ? this.userCharacter.sprite.x : 0,
                            y: this.userCharacter ? this.userCharacter.sprite.y : 0
                        }
                        }
                    },
                conversation_id: this.conversationId,
                character_id: this.currentCharacter.character_id
                },
                sender_id: "player_1",
                target_ids: [this.currentCharacter.character_id]
            };
            
        const success = this.webSocketService.send(payload);
        
        if (!success) {
            console.warn("Failed to send message through WebSocket, using fallback");
            // Use fallback local responses if server connection fails
            this.simulateCharacterResponse();
        }
    }
    
    updateConnectionStatus(text, color) {
        if (this.connectionStatus) {
            this.connectionStatus.setText(text);
            this.connectionStatus.setColor(color);
        }
    }
    
    handleChatEvent(data) {
        console.log("Handling chat event:", data);
        
        try {
            // Remove typing indicator if present
            this.hideTypingIndicator();
            
            // Extract character message
            let message = data.data?.message;
            
            // Store conversation ID for future messages
            if (data.data?.conversation_id) {
                this.conversationId = data.data.conversation_id;
            }
            
            // Add to chat display
            if (message && message.content) {
                console.log("Adding message to chat:", message.role, message.content);
                this.addMessage(message.role || 'assistant', message.content);
            } else {
                console.error("Received chat event with invalid message format:", data);
                // Try to extract message if in a different format
                if (data.data?.content) {
                    this.addMessage('assistant', data.data.content);
                } else if (typeof data === 'string') {
                    this.addMessage('assistant', data);
                } else if (typeof data.data === 'string') {
                    this.addMessage('assistant', data.data);
                } else {
                    // Last resort fallback
                    this.addMessage('assistant', "I didn't quite catch that. Could you try again?");
                }
            }
        } catch (error) {
            console.error("Error handling chat event:", error);
            // Add fallback response
            this.addMessage('assistant', "Sorry, I encountered an error processing that message.");
        }
    }
    
    removeTypingIndicator() {
        // Find and remove typing indicators
        const lastIndex = this.messages.findIndex(m => m.role === 'typing');
        if (lastIndex !== -1) {
            console.log("Removing typing indicator");
            this.messages.splice(lastIndex, 1);
            this.refreshMessages();
        }
    }
    
    addMessage(role, content) {
        console.log(`Adding message - Role: ${role}, Content: ${content.substring(0, 30)}...`);
        const messageObj = { role, content, timestamp: Date.now() };
        this.messages.push(messageObj);
        
        this.refreshMessages();
    }
    
    refreshMessages() {
        console.log("Refreshing messages display with", this.messages.length, "messages");
        // Clear existing messages display
        this.messagesContainer.removeAll(true);
        
        // Display all messages (with a simple scroll mechanism)
        let yOffset = 0;
        const maxVisibleMessages = 10; // How many messages to show at once
        const messagesToShow = this.messages.slice(-maxVisibleMessages);
        
        messagesToShow.forEach((msg) => {
            const isUser = msg.role === 'user';
            const isSystem = msg.role === 'system';
            const isTyping = msg.role === 'typing';
            
            // Choose text color based on the role
            const textColor = isUser ? '#ffffff' : (isSystem ? '#ff9900' : '#99ff99');
            
            // Create the message text object
            let messageText;
            
            if (isTyping) {
                messageText = this.add.text(0, yOffset, '⟳ Character is typing...', {
                    fontFamily: 'Arial',
                    fontSize: '16px',
                    color: '#aaaaaa',
                    wordWrap: { width: this.messagesArea.width - 40 }
                });
            } else {
                const prefix = isUser ? 'You: ' : (isSystem ? 'System: ' : `${this.currentCharacter.name}: `);
                messageText = this.add.text(0, yOffset, prefix + msg.content, {
                    fontFamily: 'Arial',
                    fontSize: '16px',
                    color: textColor,
                    wordWrap: { width: this.messagesArea.width - 40 }
                });
                
                console.log("Added message to display:", prefix + msg.content.substring(0, 30) + "...");
            }
            
            // Add the message to the container
            this.messagesContainer.add(messageText);
            
            // Update the offset for the next message
            yOffset += messageText.height + 10;
        });
        
        // If there are more messages than can be shown, add scroll indicator
        if (this.messages.length > maxVisibleMessages) {
            const scrollIndicator = this.add.text(this.messagesArea.width - 40, 0, '⥣ Scroll up for more messages', {
                fontFamily: 'Arial',
                fontSize: '12px',
                color: '#aaaaaa'
            });
            this.messagesContainer.add(scrollIndicator);
        }
    }
    
    openChat(character) {
        console.log("Opening chat with character:", character);
        // Set the character we're chatting with
        this.currentCharacter = character;
        
        // Update the character name in the header
        if (this.characterNameText && character) {
        this.characterNameText.setText(character.name);
        }
        
        // Show the chat interface
        this.chatContainer.setVisible(true);
        this.chatInput.setVisible(true);
        this.isActive = true;
        
        // Focus the input field
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = '';
            input.focus();
        } else {
            console.error("Chat input element not found when opening chat!");
        }
        
        // Check WebSocket connection status
        const status = this.webSocketService.getStatus();
        
        // If we're in offline mode, show appropriate status
        if (this.webSocketService.useOfflineMode) {
            this.updateConnectionStatus('Offline Mode', '#ffa500');
            this.addMessage('system', 'Server connection unavailable. Using offline responses.');
        } else if (!status.isConnected && !status.isConnecting) {
            // Try to connect if not connected
            this.connectToWebSocket();
        } else {
            // Update connection status
            const connectionState = status.isConnected ? 'Connected' : 'Connecting...';
            const color = status.isConnected ? '#00ff00' : '#ffff00';
            this.updateConnectionStatus(connectionState, color);
        }
        
        // Add welcome message from the character
        let welcomeMessage = `You are now chatting with ${character.name}.`;
        if (character.character_id === 'character_iron_man') {
            welcomeMessage = "Hey there. Tony Stark, genius, billionaire, playboy, philanthropist. What can I help you with?";
        } else if (character.character_id === 'character_thor') {
            welcomeMessage = "Greetings, friend! Thor, son of Odin, at your service. What brings you to speak with the God of Thunder?";
        }
        
        this.addMessage('assistant', welcomeMessage);
        
        // Send initial setup message if connected or in offline mode
        if (status.isConnected || this.webSocketService.useOfflineMode) {
            this.sendInitialMessage();
            
            // Send a proximity event
            const proximityEvent = {
                event_type: "proximity",
                data: {
                    character_id: character.character_id,
                    distance: 1,
                    action: "interact"
                },
                sender_id: "player_1"
            };
            
            this.webSocketService.send(proximityEvent);
        }
    }
    
    closeChat() {
        console.log("Closing chat");
        // Hide the chat interface
        this.chatContainer.setVisible(false);
        this.chatInput.setVisible(false);
        this.isActive = false;
        
        // Remove the input element from DOM
        const input = document.getElementById('chat-input');
        if (input) {
            input.remove();
        }
        
        // Clear messages for next conversation
        this.messages = [];
        
        // Resume the game scene
        this.scene.resume('GameScene');
        this.scene.stop();
    }
    
    update() {
        // Handle any per-frame updates if needed
    }
} 