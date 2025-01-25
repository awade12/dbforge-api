#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting installation process...${NC}"

# Install git if not present
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Installing Git...${NC}"
    sudo apt-get update
    sudo apt-get install -y git
fi

# Check if directory exists and handle appropriately
if [ -d "dbforge-api" ]; then
    echo -e "${RED}Directory dbforge-api already exists. Removing...${NC}"
    sudo rm -rf dbforge-api
fi

# Clone the repository
echo -e "${GREEN}Cloning repository...${NC}"
git clone https://github.com/awade12/dbforge-api.git
cd dbforge-api

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install certbot
if ! command -v certbot &> /dev/null; then
    echo -e "${RED}Certbot is not installed. Installing Certbot...${NC}"
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Domain name prompt with validation
DOMAIN_NAME=""
while [ -z "$DOMAIN_NAME" ]; do
    read -p "Enter your domain name (e.g., example.com): " DOMAIN_NAME
    if [ -z "$DOMAIN_NAME" ]; then
        echo -e "${RED}Domain name cannot be empty. Please try again.${NC}"
    fi
done

# Stop nginx temporarily for certbot
if systemctl is-active --quiet nginx; then
    sudo systemctl stop nginx
fi

echo -e "${GREEN}Obtaining SSL certificate for $DOMAIN_NAME...${NC}"
sudo certbot certonly --standalone --non-interactive --agree-tos --email admin@$DOMAIN_NAME -d $DOMAIN_NAME

echo -e "${GREEN}Building Docker image...${NC}"
sudo docker build -t clidb-api .

# Stop existing container if running
CONTAINER_ID=$(docker ps -q --filter "name=clidb-api")
if [ ! -z "$CONTAINER_ID" ]; then
    echo -e "${GREEN}Stopping existing container...${NC}"
    sudo docker stop $CONTAINER_ID
    sudo docker rm $CONTAINER_ID
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

# Add certbot renewal cron job
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# curl -sSL https://data.wadedesignco.com/storage/v1/object/public/metalove/installer.sh | sudo bash