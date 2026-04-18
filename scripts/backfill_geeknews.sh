#!/bin/bash

# Configuration
DAG_ID="geeknews"
START_LIMIT="2026-03-01"
END_LIMIT="2026-03-31"

# Loop from March 31st down to March 1st
current_date="$END_LIMIT"

echo "Starting backfill for DAG: $DAG_ID"
echo "Range: $END_LIMIT down to $START_LIMIT"

until [[ "$current_date" < "$START_LIMIT" ]]; do
    echo "------------------------------------------"
    echo "Backfilling date: $current_date"
    echo "------------------------------------------"

    # Command: docker compose exec airflow airflow dags backfill -s <DATE> -e <DATE> geeknews
    docker compose exec airflow airflow dags backfill \
        -s "$current_date" \
        -e "$current_date" \
        "$DAG_ID"

    # Move to the previous day
    current_date=$(date -I -d "$current_date - 1 day")
done

echo "Backfill process completed!"
