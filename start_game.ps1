# Start the Avengers RPG Game
# This script launches both the backend server and the game UI HTTP server

Write-Host "Starting Avengers RPG Game..." -ForegroundColor Green

# Set the backend port to 8080
$env:PORT = 8080

# Start the backend server in a new window
Start-Process powershell -ArgumentList "-Command `"cd '$PWD'; `$env:PORT=8080; python main.py; Read-Host 'Press Enter to close'`""

# Wait a bit for the backend to start
Start-Sleep -Seconds 2

# Start the frontend HTTP server in a new window
Start-Process powershell -ArgumentList "-Command `"cd '$PWD/game_ui'; python server.py; Read-Host 'Press Enter to close'`""

# Open the game in the default browser
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000/index.html"

Write-Host "Game servers started!" -ForegroundColor Green
Write-Host "Backend running at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Game UI running at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the servers" -ForegroundColor Yellow 