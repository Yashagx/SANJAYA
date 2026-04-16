$script = @"
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

sudo mkdir -p /usr/libexec/docker/cli-plugins
sudo curl -SL https://github.com/docker/buildx/releases/download/v0.17.1/buildx-v0.17.1.linux-amd64 -o /usr/libexec/docker/cli-plugins/docker-buildx
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-buildx

cd /home/ec2-user/auth_service
sudo docker compose down -v
sudo docker compose up --build -d
sleep 15
curl -s http://localhost:8000/health
"@

$script | ssh -i "d:\SANJAYA\sanjaya-key.pem" -o StrictHostKeyChecking=no ec2-user@16.112.128.251
