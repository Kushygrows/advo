param(
    [Parameter(Position = 0)]
    [string]$Message
)

$repoPath = "C:\Users\young\Desktop\digitalwar\ARCCE\advo-repo"
Set-Location $repoPath

# Recovery: if .git ever goes missing again (e.g. after re-extracting a
# delivered zip over this folder), reinitialize instead of failing.
$needsForce = $false
if (-not (Test-Path ".git")) {
    Write-Host "No .git folder found -- reinitializing..." -ForegroundColor Yellow
    git init
    git branch -M main
    git remote add origin https://github.com/Kushygrows/advo.git
    $needsForce = $true
}

git add -A

# Show what actually changed before committing, so you can eyeball it.
Write-Host ""
Write-Host "Changes to be committed:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Bail out cleanly if there's nothing staged -- avoids an empty commit.
$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "Nothing to commit -- working tree matches the last commit." -ForegroundColor Yellow
    exit 0
}

# Use the message passed in; otherwise ask for one interactively.
if (-not $Message) {
    $Message = Read-Host "Commit message (describe what changed)"
}
if (-not $Message) {
    Write-Host "No commit message provided -- aborting." -ForegroundColor Red
    exit 1
}

git commit -m "$Message"

if ($needsForce) {
    Write-Host "Repo was just reinitialized -- force-pushing (safe: private repo, solo pusher)." -ForegroundColor Yellow
    git push -u origin main --force
} else {
    git push
}

Write-Host ""
Write-Host "Done. Latest commit:" -ForegroundColor Green
git log -1 --oneline