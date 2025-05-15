/**
 * Base Character class for all game characters
 */
export default class Character {
    constructor(scene, x, y, texture, name, speed = 200) {
        this.scene = scene;
        this.sprite = scene.physics.add.sprite(x, y, texture);
        this.name = name;
        this.speed = speed;
        
        // Add character_id for WebSocket communication
        this.character_id = 'character_' + name.toLowerCase().replace(' ', '_');
        
        // Configure character sprite
        this.sprite.setCollideWorldBounds(true);
        this.sprite.setBounce(0.1);
        this.sprite.setDepth(5); // Increase depth to ensure visibility
        
        // Use a smaller scale for better visibility
        this.sprite.setScale(0.07);
        
        // Set a proper hitbox size for physics interactions
        this.sprite.body.setSize(40, 40);
        this.sprite.body.offset.set(20, 20);
        
        // Make the background transparent
        this.sprite.setPipeline('AlphaPipeline');
        
        // Add name text above character with higher visibility
        this.nameText = scene.add.text(x, y - 30, name, {
            fontSize: '14px',
            fill: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 5, y: 2 }
        }).setOrigin(0.5);
        this.nameText.setDepth(6);
        
        // Autonomous movement variables
        this.isAutonomous = false;
        this.autonomousTimer = null;
        this.autonomousMoveDuration = 2000; // How long to move in one direction
        this.autonomousPauseDuration = 1000; // How long to pause between movements
        this.currentDirection = null;
    }
    
    update() {
        // Update name text position to follow character
        this.nameText.setPosition(this.sprite.x, this.sprite.y - 30);
        
        // Handle autonomous movement if enabled
        if (this.isAutonomous && !this.autonomousTimer) {
            this.startAutonomousMovement();
        }
    }
    
    move(direction) {
        switch(direction) {
            case 'left':
                this.sprite.setVelocityX(-this.speed);
                // Flip sprite horizontally for left movement
                this.sprite.flipX = true;
                break;
            case 'right':
                this.sprite.setVelocityX(this.speed);
                // Reset flip for right movement
                this.sprite.flipX = false;
                break;
            case 'up':
                this.sprite.setVelocityY(-this.speed);
                break;
            case 'down':
                this.sprite.setVelocityY(this.speed);
                break;
            default:
                // Stop if no direction
                this.sprite.setVelocity(0, 0);
        }
        
        // Update current direction
        this.currentDirection = direction;
    }
    
    stop() {
        this.sprite.setVelocity(0, 0);
        this.currentDirection = 'idle';
    }
    
    // Enable autonomous movement
    enableAutonomousMovement() {
        this.isAutonomous = true;
        this.startAutonomousMovement();
    }
    
    // Disable autonomous movement
    disableAutonomousMovement() {
        this.isAutonomous = false;
        if (this.autonomousTimer) {
            this.scene.time.removeEvent(this.autonomousTimer);
            this.autonomousTimer = null;
        }
        this.stop();
    }
    
    // Start autonomous movement pattern
    startAutonomousMovement() {
        // Choose a random direction
        const directions = ['left', 'right', 'up', 'down', 'stop'];
        const randomDirection = directions[Math.floor(Math.random() * directions.length)];
        
        // Move in that direction
        this.currentDirection = randomDirection;
        if (randomDirection === 'stop') {
            this.stop();
        } else {
            this.move(randomDirection);
        }
        
        // Schedule the next movement change
        this.autonomousTimer = this.scene.time.delayedCall(
            randomDirection === 'stop' ? this.autonomousPauseDuration : this.autonomousMoveDuration, 
            () => {
                this.autonomousTimer = null;
                // Ensure we're not going off the map
                if (this.sprite.x < 100) {
                    this.move('right');
                    this.currentDirection = 'right';
                    this.autonomousTimer = this.scene.time.delayedCall(1000, () => {
                        this.autonomousTimer = null;
                    });
                } else if (this.sprite.x > 1500) {
                    this.move('left');
                    this.currentDirection = 'left';
                    this.autonomousTimer = this.scene.time.delayedCall(1000, () => {
                        this.autonomousTimer = null;
                    });
                } else if (this.sprite.y < 100) {
                    this.move('down');
                    this.currentDirection = 'down';
                    this.autonomousTimer = this.scene.time.delayedCall(1000, () => {
                        this.autonomousTimer = null;
                    });
                } else if (this.sprite.y > 1100) {
                    this.move('up');
                    this.currentDirection = 'up';
                    this.autonomousTimer = this.scene.time.delayedCall(1000, () => {
                        this.autonomousTimer = null;
                    });
                }
            }
        );
    }
} 