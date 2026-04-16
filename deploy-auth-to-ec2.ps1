param(
    [string]$KeyPath = "d:\SANJAYA\sanjaya-key.pem",
    [string]$InstanceIP = "18.61.252.222",
    [string]$User = "ec2-user"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $KeyPath)) {
    throw "Key file not found: $KeyPath"
}

Write-Host "Uploading auth_service to EC2..." -ForegroundColor Cyan
scp -i $KeyPath -o StrictHostKeyChecking=no -r auth_service "$User@$InstanceIP:/home/ec2-user/sanjaya-auth/"

$remoteScript = @"
set -e
sudo yum install -y docker >/dev/null 2>&1 || true
sudo systemctl start docker
sudo systemctl enable docker

if ! docker compose version >/dev/null 2>&1; then
  sudo yum install -y docker-compose-plugin >/dev/null 2>&1 || true
fi

cd /home/ec2-user/sanjaya-auth/auth_service
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i 's|MFA_DELIVERY_MODE=smtp|MFA_DELIVERY_MODE=log|' .env
  sed -i 's|DEBUG_OTP_IN_RESPONSE=false|DEBUG_OTP_IN_RESPONSE=true|' .env
fi

docker compose down >/dev/null 2>&1 || true
docker compose up -d --build
sleep 8
curl -sS http://localhost:8100/health
"@

Write-Host "Deploying auth stack on EC2..." -ForegroundColor Cyan
ssh -i $KeyPath -o StrictHostKeyChecking=no "$User@$InstanceIP" $remoteScript

Write-Host "Done. Auth service URL: http://$InstanceIP:8100" -ForegroundColor Green
