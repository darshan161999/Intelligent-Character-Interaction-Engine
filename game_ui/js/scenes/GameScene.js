import IronMan from '../components/IronMan.js';
import Thor from '../components/Thor.js';
import User from '../components/User.js';
import InputController from '../components/InputController.js';
import WebSocketService from '../services/WebSocketService.js';

// Create a singleton WebSocket service
const webSocketService = new WebSocketService();

export default class GameScene extends Phaser.Scene {
    constructor() {
        super('GameScene');
        this.ironMan = null;
        this.thor = null;
        this.user = null;
        this.inputController = null;
        this.webSocketService = webSocketService; // Use the singleton service
        
        // Larger city dimensions
        this.cityWidth = 3200;
        this.cityHeight = 2400;
    }
    
    preload() {
        // Load tileset and map assets
        this.load.image('tiles', 'js/assets/tilesets/avengers_tileset.png');
        this.load.image('buildings', 'js/assets/tilesets/avengers_buildings.png');
        this.load.image('objects', 'js/assets/tilesets/avengers_objects.png');
        
        // Load character sprites - using the actual image files
        this.load.image('ironman', 'js/assets/characters/ironman_2_2_31_45.jpg');
        this.load.image('thor', 'js/assets/characters/thor_1_2_23_25.jpg');
        
        // Load user character
        this.load.image('user', 'js/assets/characters/black_widow_1_2_19_24.jpg');
        
        // Add loading progress bar
        const progressBar = this.add.graphics();
        const progressBox = this.add.graphics();
        progressBox.fillStyle(0x222222, 0.8);
        progressBox.fillRect(240, 270, 320, 50);
        
        const width = this.cameras.main.width;
        const height = this.cameras.main.height;
        const loadingText = this.make.text({
            x: width / 2,
            y: height / 2 - 50,
            text: 'Loading...',
            style: {
                font: '20px monospace',
                fill: '#ffffff'
            }
        });
        loadingText.setOrigin(0.5, 0.5);
        
        this.load.on('progress', function (value) {
            progressBar.clear();
            progressBar.fillStyle(0xffffff, 1);
            progressBar.fillRect(250, 280, 300 * value, 30);
        });
        
        this.load.on('fileprogress', function (file) {
            loadingText.setText('Loading: ' + file.key);
        });
        
        this.load.on('complete', function () {
            progressBar.destroy();
            progressBox.destroy();
            loadingText.destroy();
        });
    }
    
    create() {
        // Create a custom render pipeline for transparency
        this.createAlphaPipeline();
        
        // Create the game world
        this.createTileMap();
        
        // Create characters
        this.createCharacters();
        
        // Set up world bounds for the larger city
        this.physics.world.setBounds(0, 0, this.cityWidth, this.cityHeight);
        
        // Set up camera to follow player (user)
        this.cameras.main.setBounds(0, 0, this.cityWidth, this.cityHeight);
        this.cameras.main.startFollow(this.user.sprite, true, 0.1, 0.1);
        
        // Set up input controller
        this.inputController = new InputController(this);
        
        // Add collision between characters
        this.physics.add.collider(this.user.sprite, this.ironMan.sprite);
        this.physics.add.collider(this.user.sprite, this.thor.sprite);
        this.physics.add.collider(this.ironMan.sprite, this.thor.sprite);
        
        // Add chat interaction zones
        this.createInteractionZones();
        
        // Add game instructions
        const instructions = this.add.text(400, 50, 'Move with Arrow Keys or WASD | Visit characters at Stark Tower and Asgardian Embassy | Press E to chat', {
            fontSize: '16px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 10, y: 5 }
        }).setOrigin(0.5);
        instructions.setScrollFactor(0);
        instructions.setDepth(10);
        
        // Character autonomous movement is disabled - they'll stay in place
        // Uncomment the line below to enable movement
        // this.enableAutonomousMovement();

        // Debug text to show game is loaded
        const debugText = this.add.text(400, 80, 'Game loaded successfully!', {
            fontSize: '16px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 10, y: 5 }
        }).setOrigin(0.5);
        debugText.setScrollFactor(0);
        debugText.setDepth(10);
        
        // Initialize WebSocket connection
        this.initializeWebSocket();
        
        // Set up WebSocket event handlers
        this.setupWebSocketHandlers();
    }
    
    // Create a custom render pipeline for transparency
    createAlphaPipeline() {
        // Only create the pipeline if it doesn't already exist
        if (!this.renderer.pipelines.get('AlphaPipeline')) {
            // Create a pipeline that ignores white backgrounds
            const pipelineConfig = {
                game: this.game,
                renderer: this.renderer,
                fragShader: `
                    precision mediump float;
                    uniform sampler2D uMainSampler;
                    varying vec2 outTexCoord;
                    void main(void) {
                        vec4 color = texture2D(uMainSampler, outTexCoord);
                        // Make white pixels (background) transparent
                        // Adjusted threshold to handle off-white pixels too
                        if(color.r > 0.85 && color.g > 0.85 && color.b > 0.85) {
                            gl_FragColor = vec4(color.rgb, 0.0);
                        } else {
                            gl_FragColor = color;
                        }
                    }
                `
            };
            try {
                this.renderer.pipelines.add('AlphaPipeline', new Phaser.Renderer.WebGL.Pipelines.TextureTintPipeline(pipelineConfig));
                console.log("AlphaPipeline created successfully");
            } catch (e) {
                console.error("Error creating AlphaPipeline:", e);
            }
        }
    }
    
    createTileMap() {
        // Create a visible map layer for ground
        const ground = this.add.graphics();
        
        // Fill the ground with a lighter green color
        ground.fillStyle(0x7abd6e, 1); // Light green grass
        ground.fillRect(0, 0, this.cityWidth, this.cityHeight);
        
        // Add sandy paths with better visibility
        ground.fillStyle(0xd9bc8a, 1); // Sandy color
        
        // Main horizontal path
        ground.fillRect(200, 600, this.cityWidth - 400, 200);
        
        // Main vertical path
        ground.fillRect(this.cityWidth / 2 - 100, 100, 200, this.cityHeight - 200);
        
        // Create buildings with better visibility
        this.createBuildingsLayer();
        this.createDecorationsLayer();
        this.addAvengersCompound();
        this.addCityElements();
    }
    
    createGroundLayer() {
        // Create a graphics object for the ground
        const ground = this.add.graphics();
        
        // Fill the ground with green grass and sandy paths
        ground.fillStyle(0x4a8f43, 1); // Green grass
        ground.fillRect(0, 0, this.cityWidth, this.cityHeight);
        
        // Add sandy paths (similar to the image but extended)
        ground.fillStyle(0xd9bc8a, 1); // Sandy color
        
        // Main horizontal path
        ground.fillRect(200, 600, this.cityWidth - 400, 200);
        
        // Main vertical path
        ground.fillRect(this.cityWidth / 2 - 100, 100, 200, this.cityHeight - 200);
    }
    
    createBuildingsLayer() {
        // Add Avengers-themed buildings spread across the larger city
        
        // Stark Tower (top left area)
        this.add.rectangle(250, 150, 400, 300, 0x444444).setOrigin(0);
        this.add.text(450, 300, 'Stark Tower', {
            fontSize: '20px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 5, y: 2 }
        }).setOrigin(0.5);
        
        // Thor's Asgardian Embassy (top right)
        this.add.rectangle(2500, 150, 400, 300, 0x8a6642).setOrigin(0);
        this.add.text(2700, 300, 'Asgardian Embassy', {
            fontSize: '20px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 5, y: 2 }
        }).setOrigin(0.5);
    }
    
    createDecorationsLayer() {
        // Add decorative elements spread across the larger city
        
        // Add trees (similar to the cherry blossoms in the image)
        for (let i = 0; i < 40; i++) {
            const x = Phaser.Math.Between(50, this.cityWidth - 50);
            const y = Phaser.Math.Between(50, this.cityHeight - 50);
            
            // Make sure trees don't overlap with paths and buildings
            if (this.isValidTreePosition(x, y)) {
                this.addTree(x, y);
            }
        }
    }
    
    isValidTreePosition(x, y) {
        // Check major paths
        const onMainHorizontalPath = y > 580 && y < 820;
        const onMainVerticalPath = x > (this.cityWidth / 2) - 120 && x < (this.cityWidth / 2) + 120;
        
        // Check major buildings
        const inStarkTower = x < 670 && y < 470;
        const inAsgardianEmbassy = x > 2480 && y < 470;
        const inAvengersCompound = x > 1300 && x < 1800 && y > 1800 && y < 2200;
        
        return !(onMainHorizontalPath || onMainVerticalPath || 
                 inStarkTower || inAsgardianEmbassy || inAvengersCompound);
    }
    
    addTree(x, y) {
        // Create a tree similar to the image
        const trunk = this.add.rectangle(x, y, 20, 30, 0x5c4033).setOrigin(0.5, 1);
        
        // Tree top (randomize between green and pink for variety)
        const treeColor = Math.random() > 0.5 ? 0xff9dbb : 0x2e8b57;
        const treeTop = this.add.circle(x, y - 40, 40, treeColor);
    }
    
    addAvengersCompound() {
        // Add the Avengers compound in the center-bottom of the map
        const compound = this.add.rectangle(1300, 1800, 500, 400, 0x555555).setOrigin(0);
        
        // Add "Avengers Compound" sign
        this.add.text(1550, 2000, 'Avengers Compound', {
            fontSize: '24px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 10, y: 5 }
        }).setOrigin(0.5);
    }
    
    addCityElements() {
        // Central Park
        const park = this.add.graphics();
        park.fillStyle(0x2e8b57, 1); // Darker green for park
        park.fillRect(1200, 1000, 600, 400);
        this.add.text(1500, 1200, 'Central Park', {
            fontSize: '20px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 5, y: 2 }
        }).setOrigin(0.5);
    }
    
    createPlaceholderMap() {
        // Create a simple background when assets aren't available for the larger city
        const background = this.add.graphics();
        background.fillStyle(0x4a8f43, 1); // Green background (grass)
        background.fillRect(0, 0, this.cityWidth, this.cityHeight);
        
        // Add sandy paths
        background.fillStyle(0xd9bc8a, 1); // Sandy color
        background.fillRect(200, 600, this.cityWidth - 400, 200); // Main horizontal path
        background.fillRect(this.cityWidth / 2 - 100, 100, 200, this.cityHeight - 200); // Main vertical path
        
        // Add some placeholder buildings
        background.fillStyle(0x555555, 1); // Gray buildings
        background.fillRect(250, 150, 400, 300); // Stark Tower
        background.fillRect(2500, 150, 400, 300); // Asgardian Embassy
        background.fillRect(1300, 1800, 500, 400); // Avengers Compound
    }
    
    createPlaceholderAssets() {
        // Create placeholder textures for characters
        this.createPlaceholderTexture('ironman', 0xda0000, 40, 60);
        this.createPlaceholderTexture('thor', 0x004ecb, 40, 60);
        this.createPlaceholderTexture('user', 0x00ffff, 40, 60);
    }
    
    createCharacters() {
        // Create main user character (player)
        this.user = new User(this, 1550, 2000);
        
        // Create Avengers characters at fixed, important locations
        // Iron Man at Stark Tower
        this.ironMan = new IronMan(this, 450, 300);
        
        // Thor at Asgardian Embassy
        this.thor = new Thor(this, 2700, 300);
        
        // Add visual markers to show these are interaction points
        this.addInteractionMarker(this.ironMan.sprite.x, this.ironMan.sprite.y + 30);
        this.addInteractionMarker(this.thor.sprite.x, this.thor.sprite.y + 30);
    }
    
    // Add a visual marker to indicate interaction points
    addInteractionMarker(x, y) {
        // Create a pulsing circle to draw attention
        const marker = this.add.circle(x, y, 20, 0xffff00, 0.5);
        marker.setDepth(3); // Below character but above ground
        
        // Add pulsing animation
        this.tweens.add({
            targets: marker,
            scale: 1.5,
            alpha: 0.2,
            duration: 1000,
            yoyo: true,
            repeat: -1
        });
    }
    
    createInteractionZones() {
        // Add interaction zones for Avengers characters
        const interactionZones = this.physics.add.group();
        
        // Create interaction zones for Avengers characters
        const ironManZone = this.createInteractionZone(this.ironMan);
        const thorZone = this.createInteractionZone(this.thor);
        
        // Store the zones with their associated characters
        this.ironMan.chatZone = ironManZone;
        this.thor.chatZone = thorZone;
        
        // Add these zones to the group
        interactionZones.add(ironManZone);
        interactionZones.add(thorZone);
        
        // Add overlap detection with player (user) character
        this.physics.add.overlap(this.user.sprite, interactionZones, this.handleInteraction, null, this);
    }
    
    createInteractionZone(character) {
        // Create an invisible interaction zone around a character
        const x = character.sprite.x;
        const y = character.sprite.y;
        const zone = this.physics.add.sprite(x, y, null).setScale(2);
        zone.body.setSize(60, 80);
        
        // Store character reference and ID in the zone
        zone.character = character;
        zone.characterName = character.name;
        zone.characterId = character.character_id;
        
        // Add visual indicator for interaction
        const indicator = this.add.text(x, y - 50, 'Press E to talk', {
            fontSize: '10px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 5, y: 2 }
        }).setOrigin(0.5);
        indicator.setVisible(false);
        
        zone.indicator = indicator;
        
        return zone;
    }
    
    handleInteraction(player, zone) {
        // Show interaction indicator when player is close to an Avenger
        zone.indicator.setVisible(true);
        
        // If player presses E, initiate chat
        if (this.inputController.eKey.isDown && !this.inputController.interactionCooldown) {
            console.log(`Chat with ${zone.characterName} (ID: ${zone.characterId})`);
            
            // Ensure we have the character data
            if (!zone.characterId) {
                console.error("Character ID is missing!");
                return;
            }
            
            // Create character data object
            const characterData = {
                name: zone.characterName,
                character_id: zone.characterId
            };
            
            console.log("Launching chat scene with:", characterData);
            
            // Pause this scene and launch chat scene
            this.scene.pause();
            this.scene.launch('ChatScene', { 
                character: characterData,
                user: this.user
            });
            
            // Set interaction cooldown
            this.inputController.interactionCooldown = true;
            this.time.delayedCall(500, () => {
                this.inputController.interactionCooldown = false;
            });
        }
    }
    
    // Helper method to create placeholder textures for characters
    createPlaceholderTexture(key, color, width, height) {
        const graphics = this.add.graphics();
        graphics.fillStyle(color, 1);
        graphics.fillRect(0, 0, width, height);
        
        // Create a texture from the graphics object
        graphics.generateTexture(key, width, height);
        graphics.destroy();
    }
    
    // Enable autonomous movement for Avengers characters
    // This is now disabled to keep characters in one place
    enableAutonomousMovement() {
        // Characters will stay in place - autonomous movement disabled
        console.log("Autonomous movement disabled - characters will stay in place");
        // this.ironMan.enableAutonomousMovement();
        // this.thor.enableAutonomousMovement();
    }
    
    // Update interaction zones to follow characters
    updateInteractionZones() {
        if (this.ironMan.chatZone) {
            this.ironMan.chatZone.setPosition(this.ironMan.sprite.x, this.ironMan.sprite.y);
            this.ironMan.chatZone.indicator.setPosition(this.ironMan.sprite.x, this.ironMan.sprite.y - 50);
        }
        
        if (this.thor.chatZone) {
            this.thor.chatZone.setPosition(this.thor.sprite.x, this.thor.sprite.y);
            this.thor.chatZone.indicator.setPosition(this.thor.sprite.x, this.thor.sprite.y - 50);
        }
        
        // Hide indicators if player is not close
        const playerCharacter = this.user;
        if (playerCharacter) {
            // For Iron Man
            if (this.ironMan.chatZone && this.ironMan.chatZone.indicator) {
                const distanceToIronMan = Phaser.Math.Distance.Between(
                    playerCharacter.sprite.x, playerCharacter.sprite.y,
                    this.ironMan.sprite.x, this.ironMan.sprite.y
                );
                this.ironMan.chatZone.indicator.setVisible(distanceToIronMan < 100);
            }
            
            // For Thor
            if (this.thor.chatZone && this.thor.chatZone.indicator) {
                const distanceToThor = Phaser.Math.Distance.Between(
                    playerCharacter.sprite.x, playerCharacter.sprite.y,
                    this.thor.sprite.x, this.thor.sprite.y
                );
                this.thor.chatZone.indicator.setVisible(distanceToThor < 100);
            }
        }
    }
    
    // Initialize WebSocket connection
    initializeWebSocket() {
        this.webSocketService.connect({
            user_id: 'player_1',
            client_id: 'game_client_' + Date.now()
        }).then(() => {
            console.log('WebSocket connected successfully!');
            
            // Send location update for the player
            this.sendLocationUpdate();
        }).catch(error => {
            console.error('WebSocket connection error:', error);
        });
    }
    
    // Set up WebSocket event handlers
    setupWebSocketHandlers() {
        // Handle location updates from other characters or the server
        this.webSocketService.on('location_update', (data) => {
            this.handleLocationUpdate(data);
        });
        
        // Handle proximity events (when characters come close to each other)
        this.webSocketService.on('proximity', (data) => {
            this.handleProximityEvent(data);
        });
        
        // Handle game state updates
        this.webSocketService.on('game_state', (data) => {
            this.handleGameStateUpdate(data);
        });
    }
    
    // Send player location updates to the server
    sendLocationUpdate() {
        if (!this.user || !this.webSocketService) return;
        
        const locationData = {
            event_type: "location_update",
            data: {
                position: {
                    x: this.user.sprite.x,
                    y: this.user.sprite.y
                },
                direction: this.user.currentDirection || 'idle',
                area: "main_city"
            },
            sender_id: "player_1"
        };
        
        this.webSocketService.send(locationData);
    }
    
    // Handle location updates from other entities
    handleLocationUpdate(data) {
        console.log('Location update received:', data);
        // Implementation will depend on game requirements
    }
    
    // Handle proximity events
    handleProximityEvent(data) {
        console.log('Proximity event received:', data);
        // Implementation will depend on game requirements
    }
    
    // Handle game state updates
    handleGameStateUpdate(data) {
        console.log('Game state update received:', data);
        // Implementation will depend on game requirements
    }
    
    update() {
        // Update characters
        this.ironMan.update();
        this.thor.update();
        this.user.update();
        
        // Update interaction zones to follow characters
        this.updateInteractionZones();
        
        // Update input controller for user only (Avengers move autonomously)
        this.inputController.update(this.user);
        
        // Periodically send location updates (every 2 seconds)
        if (this.user && this.webSocketService && this.time.now % 2000 < 20) {
            this.sendLocationUpdate();
        }
    }
} 