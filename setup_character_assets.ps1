# Setup Character Assets Script
# This script helps you copy your downloaded character images to the correct locations

# Create the characters directory if it doesn't exist
if (!(Test-Path -Path "game_ui\js\assets\characters")) {
    New-Item -ItemType Directory -Force -Path "game_ui\js\assets\characters"
    Write-Host "Created characters directory" -ForegroundColor Green
}

# Function to copy an image file to the destination with a new name
function Copy-CharacterImage {
    param (
        [string]$SourcePath,
        [string]$DestinationFileName
    )
    
    $destinationPath = "game_ui\js\assets\characters\$DestinationFileName"
    
    if (Test-Path -Path $SourcePath) {
        Copy-Item -Path $SourcePath -Destination $destinationPath -Force
        Write-Host "Successfully copied $SourcePath to $destinationPath" -ForegroundColor Green
    } else {
        Write-Host "Source file $SourcePath not found" -ForegroundColor Red
    }
}

Write-Host "===== Avengers Character Image Setup =====" -ForegroundColor Cyan
Write-Host "This script will help you set up your character images for the game." -ForegroundColor Cyan
Write-Host "For each character, you'll be asked to enter the path to the image you downloaded." -ForegroundColor Cyan
Write-Host "The image will be copied to the correct location with the proper name." -ForegroundColor Cyan
Write-Host ""

# Iron Man
Write-Host "IRON MAN" -ForegroundColor Yellow
$ironManPath = Read-Host "Enter the path to your Iron Man image (e.g., C:\Downloads\ironman.png)"
if ($ironManPath) {
    Copy-CharacterImage -SourcePath $ironManPath -DestinationFileName "ironman_sprite.png"
}

# Thor
Write-Host ""
Write-Host "THOR" -ForegroundColor Yellow
$thorPath = Read-Host "Enter the path to your Thor image (e.g., C:\Downloads\thor.png)"
if ($thorPath) {
    Copy-CharacterImage -SourcePath $thorPath -DestinationFileName "thor_sprite.png"
}

# Captain America
Write-Host ""
Write-Host "CAPTAIN AMERICA" -ForegroundColor Yellow
$captainPath = Read-Host "Enter the path to your Captain America image (e.g., C:\Downloads\captain.png)"
if ($captainPath) {
    Copy-CharacterImage -SourcePath $captainPath -DestinationFileName "captain_sprite.png"
}

# Black Widow
Write-Host ""
Write-Host "BLACK WIDOW" -ForegroundColor Yellow
$blackWidowPath = Read-Host "Enter the path to your Black Widow image (e.g., C:\Downloads\blackwidow.png)"
if ($blackWidowPath) {
    Copy-CharacterImage -SourcePath $blackWidowPath -DestinationFileName "black_widow_sprite.png"
}

Write-Host ""
Write-Host "Character setup complete!" -ForegroundColor Green
Write-Host "All character images should now be in the correct location: game_ui\js\assets\characters\" -ForegroundColor Cyan
Write-Host "You can run the download_assets.ps1 script to download the tileset assets if you haven't already." -ForegroundColor Cyan 