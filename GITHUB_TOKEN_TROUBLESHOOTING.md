# GitHub Authentication Troubleshooting

We're encountering a 403 Forbidden error when trying to push to your repository. Here are detailed steps to resolve this:

## Verify Token Permissions

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Check if your token has the **repo** scope (full control of private repositories)
3. If your token has been revoked or expired, generate a new one

## Create a New Token (Recommended)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Give it a name like "Hero Agent Push Access"
4. Set expiration (30 days recommended)
5. Select "Only select repositories" and choose "Intelligent-Character-Interaction-Engine"
6. Under "Repository permissions":
   - Select "Contents: Read and write"
   - Select "Metadata: Read-only"
7. Click "Generate token"
8. **IMPORTANT**: Copy the new token immediately - you won't see it again!

## Use The New Token

```powershell
# Replace YOUR_NEW_TOKEN with the token you just generated
git remote set-url origin https://YOUR_NEW_TOKEN@github.com/darshan161999/Intelligent-Character-Interaction-Engine.git
git push -u origin master
```

## Alternative: GitHub CLI Authentication

If you have GitHub CLI installed:

```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli

# Authenticate
gh auth login

# Push using GitHub CLI
gh repo create darshan161999/Intelligent-Character-Interaction-Engine --source=. --private --push
```

## Alternative: GitHub Desktop

1. Download and install GitHub Desktop from https://desktop.github.com/
2. Sign in with your GitHub account
3. Add this local repository using File → Add local repository
4. Navigate to: C:\Users\darsh_g\OneDrive - Northeastern University\Personal_Projects\Hero_Agent
5. Click "Publish repository" to push your code
6. Ensure the repository name is "Intelligent-Character-Interaction-Engine"

## Check Repository Settings

1. Go to https://github.com/darshan161999/Intelligent-Character-Interaction-Engine
2. Navigate to Settings → Branches
3. Verify the default branch is set to "main" or "master"
4. Check if there are any branch protection rules that might be preventing pushes 