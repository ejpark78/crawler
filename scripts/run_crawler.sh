#!/bin/bash

# Configuration
# Note: Using the path provided in your request. 
# If running from the project root, you might need to adjust this to ./docker/compose.worker.yml
COMPOSE_FILE="/app/docker/compose.worker.yml"
SOURCE="GeekNews"
URL="https://news.hada.io/"

# Date range: 2026-04-11 to 2026-04-17
START_DATE="2026-04-11"
END_DATE="2026-04-17"

# Loop through each date in the range
current_date="$START_DATE"
until [[ "$current_date" > "$END_DATE" ]]; do
    echo "------------------------------------------"
    echo "Processing date: $current_date"
    echo "------------------------------------------"

    # Loop through pages 1 to 5
    for page in {1..5}; do
        echo "Executing: Date=$current_date, Page=$page"
        
        docker compose -f "$COMPOSE_FILE" run --rm worker uv run python -m app.main \
            --source "$SOURCE" \
            --url "$URL" \
            --date "$current_date" \
            --page "$page"
            
        # Optional: add a small sleep between requests to be polite to the server
        # sleep 1
    done

    # Advance to the next day
    current_date=$(date -I -d "$current_date + 1 day")
done

echo "Done!"
