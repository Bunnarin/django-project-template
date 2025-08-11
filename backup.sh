#!/bin/sh

# Exit on error
set -e

# Debug information
echo "=== Starting backup with environment ==="
echo "Current directory: $(pwd)"
echo "Environment:"
printenv | sort

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading .env file"
    set -a
    source .env
    set +a
fi

# Configuration with default values
export DB_NAME=${DB_NAME:-${POSTGRES_DB:-postgres}}
export DB_USER=${DB_USER:-${POSTGRES_USER:-postgres}}
export DB_PASSWORD=${DB_PASSWORD:-${POSTGRES_PASSWORD:-postgres}}
# Use service name as defined in docker-compose.yaml
export DB_HOST=${DB_HOST:-postgresql}
export DB_PORT=${DB_PORT:-5432}
export BACKUP_DIR=${BACKUP_DIR:-/app/backup}
export RETENTION_DAYS=${RETENTION_DAYS:-7}

# Debug info
echo "=== Database Connection Details ==="
echo "DB_HOST: $DB_HOST"
echo "DB_PORT: $DB_PORT"
echo "DB_NAME: $DB_NAME"
echo "DB_USER: $DB_USER"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup file name with timestamp
TIMESTAMP=$(date +\%Y-\%m-\%d_\%H-\%M-\%S)
BACKUP_FILE="${DB_NAME}_${TIMESTAMP}.dump"
FULL_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Start backup
log "Starting backup of database: $DB_NAME"

# Set PGPASSWORD for psql/pg_dump
export PGPASSWORD="$DB_PASSWORD"

# Test connection first
echo "Testing connection to PostgreSQL at $DB_HOST:$DB_PORT..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; then
    log "ERROR: Cannot connect to PostgreSQL server at $DB_HOST:$DB_PORT"
    log "Please check if the PostgreSQL container is running and accessible"
    exit 1
fi

# Create backup
log "Running pg_dump..."
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -Fc -Z 9 -d "$DB_NAME" > "$FULL_PATH"; then
    # Set proper permissions
    chmod 600 "$FULL_PATH"
    
    log "Backup completed successfully: $FULL_PATH"
    ls -lh "$FULL_PATH"
    
    # Find and delete old backups
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    DELETED=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -type f -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
    
    if [ "$DELETED" -gt 0 ]; then
        log "Deleted $DELETED old backup(s)"
    fi
    
    # List current backups
    log "Current backups in $BACKUP_DIR:"
    ls -lh "$BACKUP_DIR"/"${DB_NAME}"_*.dump 2>/dev/null || echo "No backup files found"
else
    log "ERROR: Backup failed"
    exit 1
fi