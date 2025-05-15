import Character from './Character.js';

/**
 * Hulk character class
 */
export default class Hulk extends Character {
    constructor(scene, x, y) {
        // Hulk is stronger and slower than other characters
        super(scene, x, y, 'hulk', 'Hulk', 180);
        
        // Add Hulk specific properties
        this.strength = 100;
        this.anger = 0;
        
        // Make Hulk slightly larger
        this.sprite.setScale(0.25);
    }
    
    // Override update method to add custom behavior
    update() {
        super.update();
        
        // Hulk specific update logic
        if (this.anger > 0) {
            this.anger -= 0.1;
        }
    }
    
    // Hulk specific method - gets stronger when angry
    increaseAnger() {
        this.anger += 10;
        this.speed = 180 + this.anger;
        this.strength = 100 + this.anger * 2;
    }
} 