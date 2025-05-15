# GitHub Push Solution
# This script offers multiple methods to push your Avengers RPG game to GitHub

function Show-Menu {
    Clear-Host
    Write-Host "===== GitHub Push Solution ====="
    Write-Host "1. Use GitHub CLI (recommended)"
    Write-Host "2. Generate credential helper command"
    Write-Host "3. Clean up remote and use HTTPS"
    Write-Host "4. Show manual steps for GitHub Desktop"
    Write-Host "Q. Quit"
    Write-Host "================================="
}

function Use-GitHubCLI {
    # Check if GitHub CLI is installed
    $ghInstalled = $null
    try {
        $ghInstalled = Get-Command gh -ErrorAction SilentlyContinue
    } catch {}

    if (-not $ghInstalled) {
        Write-Host "GitHub CLI not found. Would you like to install it? (y/n)" -ForegroundColor Yellow
        $install = Read-Host
        if ($install -eq "y") {
            Write-Host "Installing GitHub CLI..." -ForegroundColor Cyan
            winget install --id GitHub.cli
            Write-Host "Please restart this script after installation completes" -ForegroundColor Green
            return
        } else {
            return
        }
    }

    # GitHub CLI is installed, use it for authentication
    Write-Host "Authenticating with GitHub CLI..." -ForegroundColor Cyan
    gh auth login

    # Push the repository
    Write-Host "Checking if repository exists on GitHub..." -ForegroundColor Cyan
    $repoExists = gh repo view darshan161999/Intelligent-Character-Interaction-Engine -ErrorAction SilentlyContinue
    
    if ($repoExists) {
        Write-Host "Repository exists. Pushing to existing repository..." -ForegroundColor Green
        # Set the remote without token
        git remote set-url origin https://github.com/darshan161999/Intelligent-Character-Interaction-Engine.git
        # Push using gh (handles auth automatically)
        gh repo sync
    } else {
        Write-Host "Repository not found. Creating and pushing..." -ForegroundColor Yellow
        gh repo create darshan161999/Intelligent-Character-Interaction-Engine --source=. --private --push
    }
}

function Generate-CredentialHelper {
    Write-Host "Setting up Git credential helper..." -ForegroundColor Cyan
    
    # Use Git credential manager
    git config --global credential.helper manager
    
    # Clean up remote (remove token from URL)
    git remote set-url origin https://github.com/darshan161999/Intelligent-Character-Interaction-Engine.git
    
    Write-Host "Credential helper configured. Run the following command to push:" -ForegroundColor Green
    Write-Host "git push -u origin master" -ForegroundColor Yellow
    Write-Host "You'll be prompted to log in through a browser window" -ForegroundColor Yellow
}

function Clean-Remote {
    # Remove token from remote URL
    git remote set-url origin https://github.com/darshan161999/Intelligent-Character-Interaction-Engine.git
    
    Write-Host "Remote URL updated to standard HTTPS format:" -ForegroundColor Green
    git remote -v
    
    Write-Host "Now run: git push -u origin master" -ForegroundColor Yellow
    Write-Host "When prompted, enter your GitHub username and password/PAT" -ForegroundColor Yellow
}

function Show-GitHubDesktop {
    Write-Host "== Using GitHub Desktop ==" -ForegroundColor Cyan
    Write-Host "1. Download & install GitHub Desktop: https://desktop.github.com/" -ForegroundColor Yellow
    Write-Host "2. Sign in with your GitHub account" -ForegroundColor Yellow
    Write-Host "3. Add local repository:" -ForegroundColor Yellow
    Write-Host "   - File > Add local repository" -ForegroundColor Yellow
    Write-Host "   - Browse to: C:\Users\darsh_g\OneDrive - Northeastern University\Personal_Projects\Hero_Agent" -ForegroundColor Yellow
    Write-Host "4. Publish repository to GitHub" -ForegroundColor Yellow
    Write-Host "   - Set name: Intelligent-Character-Interaction-Engine" -ForegroundColor Yellow
    Write-Host "   - Choose visibility (public/private)" -ForegroundColor Yellow
    Write-Host "5. Click Publish repository" -ForegroundColor Yellow
}

# Main program loop
do {
    Show-Menu
    $selection = Read-Host "Please make a selection"
    
    switch ($selection) {
        '1' { Use-GitHubCLI }
        '2' { Generate-CredentialHelper }
        '3' { Clean-Remote }
        '4' { Show-GitHubDesktop }
        'q' { return }
    }
    
    if ($selection -ne 'q') {
        Write-Host ""
        Write-Host "Press any key to return to menu..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} while ($selection -ne 'q') 