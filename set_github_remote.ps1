# PowerShell script to securely set up GitHub remote URL with token
# Run this script to set up your GitHub remote with the personal access token

# Store the token in a variable (not exposed in command history)
$token = "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"
$repo = "darshan161999/Intelligent-Character-Interaction-Engine.git"

# Set the remote URL with the token
git remote set-url origin "https://$token@github.com/$repo"

# Verify the remote (will show URL without token for security)
Write-Host "Remote URL set successfully. Verifying:"
git remote -v

# Instructions for pushing
Write-Host ""
Write-Host "Now run the following command to push your code:"
Write-Host "git push -u origin master"

# Clean up variable for security
$token = $null 