#!/usr/bin/env bash
# /dockerstartup/custom_startup.sh

echo "Starting custom startup scripts..."

for script in /dockerstartup/custom_startup/*.sh; do
    # custom_startup.sh 자기 자신은 제외하고 실행
    if [ -f "$script" ] && [[ "$script" != *"custom_startup.sh" ]]; then
        echo "Executing: $script"
        bash "$script"
    fi
done

echo "Custom startup completion."
