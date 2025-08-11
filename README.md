## initial setup vps
sudo apt-get update
sudo apt-get install docker.io -y
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo apt-get install git -y

git clone $REPO_URL prod
cd prod
mv .env.staging .env
nano .env

python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

sudo docker-compose run --rm certbot /app/certbot_init.sh

**then after that CICD will handle the rest**