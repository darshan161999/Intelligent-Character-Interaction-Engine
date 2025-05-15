import Character from './Character.js';

/**
 * Thor character class
 */
export default class Thor extends Character {
    constructor(scene, x, y) {
        super(scene, x, y, 'thor', 'Thor', 180);
        
        // Add any Thor specific properties or methods
        this.hasMjolnir = true;
    }
    
    // Override update method to add custom behavior
    update() {
        super.update();
        // Any Thor specific update logic can go here
    }
} 