#!/bin/bash

# Define color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if an argument is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <environment: dev|prod> <command: up|down> [delete]${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Initializing ..."

# Check if the system is running Linux
if [ "$(uname)" == "Linux" ]; then
    echo -e "${GREEN}✓${NC} System OS: Linux Detected"
    
    # Get the IP address of the Linux system
    ip_address=$(hostname -I | awk '{print $1}')
    echo -e "${GREEN}✓${NC} IP Address: $ip_address"
    
    # Step 1: Copy the environment file based on environment
    echo "Copying the environment file..."

    if [ "$1" == "dev" ]; then
        cp .env.local .env
        echo "Copied .env.local to .env"
    elif [ "$1" == "prod" ]; then
        cp .env.production .env
        echo "Copied .env.production to .env"
    else
        echo "Unknown environment, skipping env copy"
    fi
    chmod +x entrypoint.dev.sh
    # chmod +x pg_backup.sh
    # sudo apt update
    # sudo apt install -y cron
    # crontab -l
    # 🕐 2. Add a Cron Job
    # Edit your crontab:

    # bash
    # crontab -e
    # Add a line like this to run the backup daily at 2 AM:

    # bash
    # 0 2 * * * /bin/bash /path/to/pg_backup.sh >> /path/to/pg_backup.log 2>&1
    # 📁 Replace /path/to/pg_backup.sh and .log with the actual path.



fi

# Function to create the network and volumes
create_network_and_volume() {
    docker network create webnet 2>/dev/null || echo "Network 'webnet' already exists or failed to create"
    # Uncomment and customize these if needed
    docker volume create postgres-data 2>/dev/null || echo "Volume 'postgres-data' already exists or failed to create"
    docker volume create elasticsearch-data 2>/dev/null || echo "Volume 'elasticsearch-data' already exists or failed to create"
}

# Function to start containers
start_containers() {
    create_network_and_volume
    docker-compose -f "$compose_file" build
    docker-compose -f "$compose_file" up -d
}

# Function to stop containers
stop_containers() {
    docker-compose -f "$compose_file" down
}

# Function to stop and remove containers, images, volumes, orphans
stop_and_remove_containers() {
    docker-compose -f "$compose_file" down --rmi all --volumes --remove-orphans
}

# Function to handle environment and commands
handle_environment() {
    case "$1" in
        dev)
            compose_file="docker-compose.dev.yml"
            ;;
        prod)
            compose_file="docker-compose.prod.yml"
            ;;
        *)
            echo -e "${RED}Invalid environment! Please specify 'dev' or 'prod'.${NC}"
            exit 1
            ;;
    esac

    case "$2" in
        up)
            start_containers
            ;;
        down)
            if [ "$3" == "delete" ]; then
                stop_and_remove_containers
            else
                stop_containers
            fi
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 <environment: dev|prod> <command: up|down> [delete]${NC}"
            exit 1
            ;;
    esac
}

# Main script logic
handle_environment "$1" "$2" "$3"
