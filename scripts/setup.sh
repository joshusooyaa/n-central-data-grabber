#!/bin/bash

DB_NAME="n_central_monitor_data"
DB_USER="root"
LOG_FILE="logs/log_files/db-setup.log"
SQL_FILE="db/db.sql"

read -sp "Enter MySQL root password: " DB_PASS
echo

check_db_exists() {
    DB_EXISTS=$(mysql -u$DB_USER -p$DB_PASS -sN -e "SHOW DATABASES LIKE '$DB_NAME';" 2>/dev/null)
    if [ "$DB_EXISTS" ]; then
        echo "Database '$DB_NAME' already exists."
        return 0
    else
        return 1
    fi
}

run_sql() {
    if ! check_db_exists; then
        echo "Creating database and tables..."
        mysql -u$DB_USER -p$DB_PASS < $SQL_FILE 2>&1 | grep -Ev "\[Warning\].*password" > $LOG_FILE
        MYSQL_EXIT_CODE=${PIPESTATUS[0]}
        if [ $MYSQL_EXIT_CODE -eq 0 ]; then
            echo "Database and tables created successfully."
        else
            echo "Failed to execute SQL file. See '$LOG_FILE' for more details."
            exit 1
        fi
    fi
}

if [ ! -f "$SQL_FILE" ]; then
    echo "SQL file not found: $SQL_FILE"
    exit 1
fi

run_sql