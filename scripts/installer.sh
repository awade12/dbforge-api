#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting installation process...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Installing Git...${NC}"
    sudo apt-get update
    sudo apt-get install -y git
fi

echo -e "${GREEN}Cloning repository...${NC}"
git clone https://github.com/awade12/dbforge-api.git
cd dbforge-api

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v certbot &> /dev/null; then
    echo -e "${RED}Certbot is not installed. Installing Certbot...${NC}"
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

read -p "Enter your domain name (e.g., example.com): " DOMAIN_NAME

echo -e "${GREEN}Obtaining SSL certificate for $DOMAIN_NAME...${NC}"
sudo certbot certonly --standalone -d $DOMAIN_NAME

echo -e "${GREEN}Building Docker image...${NC}"
sudo docker build -t clidb-api .

CONTAINER_ID=$(docker ps -q --filter "name=clidb-api")
if [ ! -z "$CONTAINER_ID" ]; then
    echo -e "${GREEN}Stopping existing container...${NC}"
    sudo docker stop $CONTAINER_ID
fi

echo -e "${GREEN}Starting container with SSL...${NC}"
sudo docker run -d \
    --name clidb-api \
    --privileged \
    -p 443:3943 \
    -v /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem:/app/cert/fullchain.pem \
    -v /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem:/app/cert/privkey.pem \
    clidb-api

echo -e "${GREEN}Installation complete!${NC}"
echo -e "Your application is now running at https://$DOMAIN_NAME"
echo -e "Please make sure your domain's DNS is properly configured to point to this server."

(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
