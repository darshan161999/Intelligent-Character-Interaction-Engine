import Character from './Character.js';

/**
 * User character class - this will be the main character controlled by the player
 */
export default class User extends Character {
    constructor(scene, x, y) {
        super(scene, x, y, 'user', 'You', 240);
        
        // Flag to indicate this is the player character
        this.isPlayerCharacter = true;
        
        // Make the User character stand out with a custom tint
        this.sprite.setTint(0x00ffff);
        
        // Resize the hitbox for better player controls
        this.sprite.body.setSize(40, 40);
        this.sprite.body.offset.set(20, 20);
        
        // Add a special visual indicator for the player
        this.indicator = scene.add.circle(x, y - 40, 8, 0x00ffff);
        this.indicator.setDepth(10);
    }
    
    // Override update method to add custom behavior
    update() {
        super.update();
        
        // Update the indicator position
        this.indicator.setPosition(this.sprite.x, this.sprite.y - 40);
    }
    
    // Method to initiate a chat with another character
    initiateChat(targetCharacter) {
        console.log(`Initiating chat with ${targetCharacter.name}`);
        
        // This will be handled by the chat system
        return {
            initiator: this.name,
            target: targetCharacter.name,
            character_id: 'character_' + targetCharacter.name.toLowerCase().replace(' ', '_')
        };
    }
} 