**initial setup vps**
sudo -i
apt-get update
apt-get install docker.io -y
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
apt-get install git -y
git clone $REPO_URL
cd $APP_DIR
nano .env

docker-compose run --rm certbot /app/certbot_init.sh
cd ..
mkdir staging
cd staging
git clone $REPO_URL
cd $APP_DIR
nano .env

**then after that CICD will handle the rest**