# PowerShell script to push to GitHub repository
Write-Host "This script will help push your code to GitHub"
Write-Host "Repository: https://github.com/darshan161999/Intelligent-Character-Interaction-Engine.git"
Write-Host ""
Write-Host "When prompted, enter your GitHub username and Personal Access Token (not your password)"
Write-Host "If a browser opens for authentication, complete the process there"
Write-Host ""

# Make sure we're in the correct directory
$currentDir = Get-Location
Write-Host "Current directory: $currentDir"
Write-Host ""

# Check if Git is installed
try {
    git --version
    Write-Host "Git is installed and ready to use"
} catch {
    Write-Host "Git is not installed or not in PATH. Please install Git and try again."
    exit 1
}

# Check remote configuration
Write-Host "Checking remote configuration..."
git remote -v
Write-Host ""

# Instructions for creating a new token if needed
Write-Host "If you need a new Personal Access Token, go to:"
Write-Host "https://github.com/settings/tokens"
Write-Host "Click 'Generate new token' and ensure it has 'repo' scope"
Write-Host ""

# Attempt to push
Write-Host "Attempting to push to GitHub..."
Write-Host "Running: git push -u origin master"
Write-Host "If prompted, enter your GitHub credentials"
Write-Host ""

# The user will need to run this command themselves
Write-Host "To push your code, run:"
Write-Host "git push -u origin master"
Write-Host ""
Write-Host "Alternatively, you can use GitHub Desktop for a simpler experience:"
Write-Host "1. Download from https://desktop.github.com/"
Write-Host "2. Add this repository and push with a few clicks" 