import GameScene from './scenes/GameScene.js';
import ChatScene from './scenes/ChatScene.js';

// Game configuration
const config = {
    type: Phaser.AUTO,
    parent: 'game-container',
    width: 1024,
    height: 768,
    backgroundColor: '#4a8f43',
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 }, // No gravity for top-down movement
            debug: false
        }
    },
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    scene: [GameScene, ChatScene]
};

// Initialize the game
const game = new Phaser.Game(config); 