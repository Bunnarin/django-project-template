**initial setup vps**
sudo apt-get update
sudo apt-get install docker.io -y
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo apt-get install git -y

git clone $REPO_URL .
nano .env

sudo docker-compose run --rm certbot /app/certbot_init.sh

**then after that CICD will handle the rest**