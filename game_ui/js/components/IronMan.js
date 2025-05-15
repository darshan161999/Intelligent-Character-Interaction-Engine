import Character from './Character.js';

/**
 * Iron Man character class
 */
export default class IronMan extends Character {
    constructor(scene, x, y) {
        super(scene, x, y, 'ironman', 'Iron Man', 220);
        
        // Add any Iron Man specific properties or methods
        this.hasRepulsors = true;
    }
    
    // Override update method to add custom behavior
    update() {
        super.update();
        // Any Iron Man specific update logic can go here
    }
} 