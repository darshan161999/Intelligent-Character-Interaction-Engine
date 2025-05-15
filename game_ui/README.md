# Avengers Game

A simple 2D Phaser game featuring Iron Man and Thor characters that can move around the screen.

## Features

- Two playable Avengers characters: Iron Man and Thor
- Four-directional movement for each character
- Component-based architecture for easy code management
- Space-themed background (representing an Avengers scene)

## Controls

- **Iron Man**: Control with Arrow Keys (↑, ↓, ←, →)
- **Thor**: Control with WASD Keys (W, A, S, D)

## Setup

1. Make sure you have Node.js installed
2. Install dependencies: `npm install`
3. Start the server: `npm start`
4. Open your browser and go to `http://localhost:8080`

## Project Structure

- `index.html` - Main HTML file
- `js/` - JavaScript files
  - `main.js` - Main game initialization
  - `components/` - Game components
    - `Character.js` - Base character class
    - `IronMan.js` - Iron Man character class
    - `Thor.js` - Thor character class
    - `InputController.js` - Input handling component
  - `scenes/` - Game scenes
    - `GameScene.js` - Main game scene

## Technical Details

- Built with Phaser 3.55.2
- Uses ES6 modules
- Component-based architecture for easy extension 