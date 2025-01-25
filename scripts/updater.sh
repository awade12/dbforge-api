#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting update process...${NC}"

# Check if directory exists
if [ ! -d "dbforge-api" ]; then
    echo -e "${RED}Directory dbforge-api not found. Please run the installer first.${NC}"
    exit 1
fi

# Navigate to the directory
cd dbforge-api

# Stash any local changes
echo -e "${GREEN}Stashing any local changes...${NC}"
git stash

# Pull latest changes
echo -e "${GREEN}Pulling latest changes from repository...${NC}"
git pull origin main

# Stop existing container
echo -e "${GREEN}Stopping existing container...${NC}"
CONTAINER_ID=$(docker ps -q --filter "name=clidb-api")
if [ ! -z "$CONTAINER_ID" ]; then
    sudo docker stop $CONTAINER_ID
    sudo docker rm $CONTAINER_ID
fi

# Remove old image
echo -e "${GREEN}Removing old Docker image...${NC}"
sudo docker rmi clidb-api

# Build new image
echo -e "${GREEN}Building new Docker image...${NC}"
sudo docker build -t clidb-api .

# Start new container
echo -e "${GREEN}Starting updated container...${NC}"
sudo docker run -d \
    --name clidb-api \
    --privileged \
    -p 80:3943 \
    clidb-api

# Get server IP address
SERVER_IP=$(curl -s ifconfig.me)

echo -e "${GREEN}Update complete!${NC}"
echo -e "Your API is now running at http://$SERVER_IP"
echo -e "Access the API documentation at http://$SERVER_IP/docs"

# Usage instructions as a comment:
# curl -sSL https://data.wadedesignco.com/storage/v1/object/public/metalove/updater.sh | sudo bash
