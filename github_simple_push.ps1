# Simple GitHub Push Script

# 1. Clean up the remote URL (remove token)
Write-Host "Step 1: Cleaning up remote URL..." -ForegroundColor Cyan
git remote set-url origin https://github.com/darshan161999/Intelligent-Character-Interaction-Engine.git

# 2. Verify the remote
Write-Host "`nStep 2: Verifying remote URL..." -ForegroundColor Cyan
git remote -v

# 3. Configure credential helper
Write-Host "`nStep 3: Setting up credential helper..." -ForegroundColor Cyan
git config --global credential.helper manager

# 4. Push to GitHub
Write-Host "`nStep 4: Ready to push! Run this command:" -ForegroundColor Green
Write-Host "git push -u origin master" -ForegroundColor Yellow
Write-Host "You'll be prompted to authenticate in a browser window" -ForegroundColor Yellow

# 5. Alternative method
Write-Host "`nAlternative: Using GitHub Desktop" -ForegroundColor Cyan
Write-Host "1. Download & install: https://desktop.github.com/" -ForegroundColor Yellow
Write-Host "2. Add local repository: C:\Users\darsh_g\OneDrive - Northeastern University\Personal_Projects\Hero_Agent" -ForegroundColor Yellow
Write-Host "3. Publish to GitHub as 'Intelligent-Character-Interaction-Engine'" -ForegroundColor Yellow

Write-Host "`nPress Enter to exit..."
Read-Host 