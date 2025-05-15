/**
 * Input Controller to handle keyboard inputs for character movement
 */
export default class InputController {
    constructor(scene) {
        this.scene = scene;
        this.cursors = scene.input.keyboard.createCursorKeys();
        
        // Add WASD keys as alternative movement controls
        this.wKey = scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W);
        this.aKey = scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
        this.sKey = scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S);
        this.dKey = scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);
        
        // Add E key for interactions
        this.eKey = scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);
        
        // Add key press listeners for interaction key
        this.eKey.on('down', this.handleInteractionKeyDown, this);
        
        // Track interaction cooldown
        this.interactionCooldown = false;
        
        // Configure keyboard capture to only capture the keys we need
        // This prevents Phaser from capturing all keyboard events
        scene.input.keyboard.enableGlobalCapture();
        scene.input.keyboard.clearCaptures();
        
        // Only capture the keys we need for the game
        scene.input.keyboard.addCapture([
            Phaser.Input.Keyboard.KeyCodes.UP,
            Phaser.Input.Keyboard.KeyCodes.DOWN,
            Phaser.Input.Keyboard.KeyCodes.LEFT,
            Phaser.Input.Keyboard.KeyCodes.RIGHT,
            Phaser.Input.Keyboard.KeyCodes.W,
            Phaser.Input.Keyboard.KeyCodes.A,
            Phaser.Input.Keyboard.KeyCodes.S,
            Phaser.Input.Keyboard.KeyCodes.D,
            Phaser.Input.Keyboard.KeyCodes.E,
            Phaser.Input.Keyboard.KeyCodes.ESC
        ]);
    }
    
    handleInteractionKeyDown() {
        // Set a cooldown to prevent rapid interactions
        if (!this.interactionCooldown) {
            this.interactionCooldown = true;
            
            // Reset cooldown after 500ms
            this.scene.time.delayedCall(500, () => {
                this.interactionCooldown = false;
            });
        }
    }
    
    update(user) {
        // Control user character with arrow keys or WASD
        if (this.cursors.left.isDown || this.aKey.isDown) {
            user.move('left');
        } else if (this.cursors.right.isDown || this.dKey.isDown) {
            user.move('right');
        } else {
            // Stop horizontal movement if no left/right keys are pressed
            user.sprite.setVelocityX(0);
        }
        
        if (this.cursors.up.isDown || this.wKey.isDown) {
            user.move('up');
        } else if (this.cursors.down.isDown || this.sKey.isDown) {
            user.move('down');
        } else {
            // Stop vertical movement if no up/down keys are pressed
            user.sprite.setVelocityY(0);
        }
    }
} 