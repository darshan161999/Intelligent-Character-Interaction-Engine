# PowerShell script to download game assets

# Create directories if they don't exist
if (!(Test-Path -Path "game_ui\js\assets\characters")) {
    New-Item -ItemType Directory -Force -Path "game_ui\js\assets\characters"
}

if (!(Test-Path -Path "game_ui\js\assets\tilesets")) {
    New-Item -ItemType Directory -Force -Path "game_ui\js\assets\tilesets"
}

# Character images have been manually downloaded by the user
Write-Host "Using character images that you've already downloaded" -ForegroundColor Green

# Download tileset assets - these seemed to work fine in the previous run
try {
    # Grass tileset (from OpenGameArt)
    $tilesetSourceUrl = "https://opengameart.org/sites/default/files/grass_14.png"
    Invoke-WebRequest -Uri $tilesetSourceUrl -OutFile "game_ui\js\assets\tilesets\avengers_tileset.png"
    Write-Host "Downloaded avengers_tileset.png" -ForegroundColor Green

    # Buildings tileset (from OpenGameArt)
    $buildingsSourceUrl = "https://opengameart.org/sites/default/files/preview_198.png"
    Invoke-WebRequest -Uri $buildingsSourceUrl -OutFile "game_ui\js\assets\tilesets\avengers_buildings.png"
    Write-Host "Downloaded avengers_buildings.png" -ForegroundColor Green

    # Objects tileset (from OpenGameArt)
    $objectsSourceUrl = "https://opengameart.org/sites/default/files/preview_928.png"
    Invoke-WebRequest -Uri $objectsSourceUrl -OutFile "game_ui\js\assets\tilesets\avengers_objects.png" 
    Write-Host "Downloaded avengers_objects.png" -ForegroundColor Green
}
catch {
    Write-Host "Error downloading tileset assets: $_" -ForegroundColor Red
    
    # Create simple placeholder text files for tilesets if download fails
    "This is a placeholder for avengers_tileset.png" | Out-File -FilePath "game_ui\js\assets\tilesets\avengers_tileset.png"
    "This is a placeholder for avengers_buildings.png" | Out-File -FilePath "game_ui\js\assets\tilesets\avengers_buildings.png"
    "This is a placeholder for avengers_objects.png" | Out-File -FilePath "game_ui\js\assets\tilesets\avengers_objects.png"
    Write-Host "Created tileset placeholders as fallback" -ForegroundColor Yellow
}

Write-Host "Asset setup complete. Check the game_ui\js\assets directory." -ForegroundColor Cyan
Write-Host "IMPORTANT: Make sure your downloaded character images are named exactly:" -ForegroundColor Yellow
Write-Host "ironman_sprite.png, thor_sprite.png, captain_sprite.png, black_widow_sprite.png" -ForegroundColor Yellow
Write-Host "and placed in the game_ui\js\assets\characters\ directory" -ForegroundColor Yellow