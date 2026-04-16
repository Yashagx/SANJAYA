# ──────────────────────────────────────────────────────────────────
# SANJAYA EC2 Deployment Script (PowerShell)
# ──────────────────────────────────────────────────────────────────
# Purpose: Deploy SANJAYA to EC2 with a single command from Windows
# Usage:   .\deploy-to-ec2.ps1 -KeyPath "path\to\key.pem" -InstanceIP "16.112.128.251"
# ──────────────────────────────────────────────────────────────────

param(
    [Parameter(Mandatory=$true)]
    [string]$KeyPath,
    
    [Parameter(Mandatory=$true)]
    [string]$InstanceIP,
    
    [string]$User = "ec2-user"
)

$ErrorActionPreference = "Stop"

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SANJAYA EC2 Deployment (PowerShell)" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Validate input
if (-not (Test-Path $KeyPath)) {
    Write-Host "❌ Error: PEM key file not found at $KeyPath" -ForegroundColor Red
    exit 1
}

# Fix key permissions
Write-Host "[1/4] Fixing PEM key permissions..." -ForegroundColor Yellow
$KeyItem = Get-Item $KeyPath
icacls $KeyPath /inheritance:r | Out-Null
icacls $KeyPath /grant:r "$($env:USERNAME):(F)" | Out-Null

# Push code first
Write-Host "[2/4] Pushing code to GitHub..." -ForegroundColor Yellow
Push-Location -Path (Split-Path $PSScriptRoot -Parent)
try {
    git add -A
    git commit -m "Deployment: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ErrorAction SilentlyContinue
    git push origin main
    Write-Host "✓ Code pushed to GitHub" -ForegroundColor Green
}
catch {
    Write-Host "⚠ Git push skipped (no changes or error)" -ForegroundColor Yellow
}
finally {
    Pop-Location
}

# Deploy to EC2
Write-Host "[3/4] Connecting to EC2 and deploying..." -ForegroundColor Yellow
$DeployCommand = @"
set -e
echo "Starting SANJAYA deployment..."

# Navigate to app directory
APP_DIR="/home/ec2-user/sanjaya"
cd `$APP_DIR || mkdir -p `$APP_DIR && cd `$APP_DIR

# Pull latest code
git clone https://github.com/Yashagx/SANJAYA.git . 2>/dev/null || (git fetch origin && git checkout main && git pull origin main)

# Run deployment script
chmod +x deploy.sh
./deploy.sh
"@

# Execute via ssh
& ssh -i $KeyPath -o StrictHostKeyChecking=no `
    $User@$InstanceIP `
    $DeployCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
}
else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Get IP and display info
Write-Host "" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✓ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Application Details:" -ForegroundColor Yellow
Write-Host "   URL: http://$InstanceIP`:8000" -ForegroundColor White
Write-Host "   Login: http://$InstanceIP`:8000/login" -ForegroundColor White
Write-Host ""
Write-Host "📝 Quick Commands:" -ForegroundColor Yellow
Write-Host "   View logs:  ssh -i $KeyPath $User@$InstanceIP 'docker logs sanjaya-app-prod'" -ForegroundColor White
Write-Host "   Restart:    ssh -i $KeyPath $User@$InstanceIP 'cd ~/sanjaya && docker-compose -f docker-compose.prod.yml restart'" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Create first admin user (run on EC2):" -ForegroundColor Yellow
Write-Host '   curl -X POST http://localhost:8000/auth/register \'  -ForegroundColor White
Write-Host '     -H "Content-Type: application/json" \'  -ForegroundColor White
Write-Host '     -d "{\"email\":\"admin@example.com\",\"password\":\"YourSecurePassword123!\"}"'  -ForegroundColor White
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
