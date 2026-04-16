$script = @"
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -aG docker ec2-user
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-`$(uname -s)-`$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
cd /home/ec2-user/auth_service
sudo /usr/local/bin/docker-compose down -v
sudo /usr/local/bin/docker-compose up --build -d
sleep 15
curl http://localhost:8000/health
"@

$script | ssh -i "d:\SANJAYA\sanjaya-key.pem" -o StrictHostKeyChecking=no ec2-user@16.112.128.251
