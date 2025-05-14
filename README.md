# Hero Agent: Avengers RPG Game

An interactive web-based role-playing game featuring Avengers characters powered by AI character interactions.

## Project Overview

Hero Agent is an immersive gaming experience where players can explore an Avengers-themed world and interact with AI-powered characters including Iron Man and Thor. The game combines modern web technologies with artificial intelligence to create dynamic and contextually relevant character interactions.

## Features

- **Interactive Gameplay**: Navigate a 2D environment using arrow keys or WASD controls
- **Character Interactions**: Chat with Avengers characters through an intuitive dialogue system
- **AI-Powered Responses**: Characters respond intelligently based on context and conversation history
- **Offline Support**: Full game functionality even without backend server connectivity
- **Responsive Design**: Adapts to different screen sizes for optimal player experience

## Technology Stack

### Frontend
- JavaScript ES6/ES2015+
- Phaser.js game framework
- HTML5 & CSS3
- WebSocket for real-time communication

### Backend
- Python with FastAPI
- WebSocket API for real-time character interactions
- RAG (Retrieval-Augmented Generation) system for contextual responses
- MongoDB for conversation and knowledge storage

### AI & Machine Learning
- Sentence Transformers for text embeddings
- Vector-based knowledge retrieval
- Groq LLM API for natural language generation
- Custom character personality models

### Development Tools
- Git for version control
- Docker for containerization
- Prometheus for monitoring
- Jest for automated testing

## Getting Started

### Prerequisites
- Node.js 14+ for the game frontend
- Python 3.8+ for the backend server
- MongoDB instance (local or cloud)

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/hero-agent.git
cd hero-agent
```

2. Install frontend dependencies:
```
cd game_ui
npm install
```

3. Install backend dependencies:
```
cd ../hero_agent_backend
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the backend directory with the following:
```
GROQ_API_KEY=your_api_key
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB_NAME=hero_agent
```

### Running the Application

1. Start the backend server:
```
python main.py
```

2. In a separate terminal, start the frontend:
```
cd game_ui
python server.py
```

3. Open your browser and navigate to:
```
http://localhost:3000
```

## Gameplay Instructions

- Use **Arrow Keys** or **WASD** to move your character
- Visit characters at **Stark Tower** and **Asgardian Embassy**
- Press **E** to initiate conversation when near a character
- Type your message and press **Enter** or click **Send**
- Press **ESC** to exit conversations

## Offline Mode

The game supports offline mode by default. To connect to the backend server:
- Add `?mode=online` to the URL: `http://localhost:3000?mode=online`

## Project Structure

```
/
├── game_ui/                # Frontend game files
│   ├── js/                 # JavaScript source code
│   │   ├── assets/         # Game assets (sprites, images)
│   │   ├── components/     # Game components (characters, etc.)
│   │   ├── scenes/         # Game scenes
│   │   └── services/       # Service classes (WebSocket, etc.)
│   ├── index.html          # Main game HTML file
│   └── server.py           # Simple HTTP server for development
│
├── hero_agent_backend/     # Backend server
│   ├── app/                # Application code
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Backend services
│   │   └── schemas/        # Data schemas
│   └── requirements.txt    # Python dependencies
│
└── main.py                 # Main entry point for backend
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Character sprites based on [Avengers Pixel Art by Markiro](https://markiro.itch.io/avengers-pixel-art)
- Inspired by Marvel's Avengers franchise

---

*Note: This is a fan project and is not affiliated with Marvel or Disney.* 
