#!/bin/bash

# Set variables
CONTAINER_NAME="users-db"
DB_NAME="users_db"
DB_USER="postgres"
BACKUP_DIR="/home/banwe/db_backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run backup
docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > "$BACKUP_FILE"

# Optional: delete backups older than 7 days
find "$BACKUP_DIR" -type f -name "*.sql" -mtime +7 -exec rm {} \;

echo "Backup created at $BACKUP_FILE"
