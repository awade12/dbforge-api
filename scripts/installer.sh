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

echo -e "${GREEN}Building Docker image...${NC}"
sudo docker build -t clidb-api .

# Stop existing container if running
CONTAINER_ID=$(docker ps -q --filter "name=clidb-api")
if [ ! -z "$CONTAINER_ID" ]; then
    echo -e "${GREEN}Stopping existing container...${NC}"
    sudo docker stop $CONTAINER_ID
    sudo docker rm $CONTAINER_ID
fi

echo -e "${GREEN}Starting container...${NC}"
sudo docker run -d \
    --name clidb-api \
    --privileged \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 80:3943 \
    clidb-api

# Get server IP address
SERVER_IP=$(curl -s ifconfig.me)

echo -e "${GREEN}Installation complete!${NC}"
echo -e "Your API is now running at http://$SERVER_IP"
echo -e "Access the API documentation at http://$SERVER_IP/docs"

# curl -sSL https://data.wadedesignco.com/storage/v1/object/public/metalove/installer.sh | sudo bash