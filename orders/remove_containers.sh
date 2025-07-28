#!/bin/bash

# Stop and remove all running Docker containers
echo -e "\e[32m✓\e[0m Stopping all running Docker containers..."
docker stop $(docker ps -q)

echo -e "\e[32m✓\e[0m Removing all Docker containers..."
docker rm $(docker ps -a -q)

# Prune system: remove unused images, networks, and build cache
echo -e "\e[32m✓\e[0m Pruning Docker system (images, cache, networks)..."
docker system prune -a -f

# Take down Docker Compose services with volume removal
echo -e "\e[32m✓\e[0m Taking down Docker Compose (with volumes)..."
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.prod.yml down -v

# Remove any dangling volumes not used by a container
echo -e "\e[32m✓\e[0m Removing dangling volumes..."
docker volume prune -f

echo -e "\e[32m✓\e[0m ✅ All Docker containers, volumes, images, and Compose services have been cleaned up."
