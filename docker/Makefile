
SHELL := /bin/bash

.PHONY: *

# --- Ollama ---
# ollama pull gemma4:31b-cloud
# ollama run gemma4:31b-cloud
# ollama launch claude --model kimi-k2.6:cloud
# ollama launch claude --model gemma4:31b-cloud -- --dangerously-skip-permissions
# ollama launch claude --model gemma4:4b
# ollama launch claude --model gemma4:e2b

login:
	ollama login

logout:
	ollama signout

claude:
# 	ollama launch claude --model gemma4:31b-cloud -- --dangerously-skip-permissions
	ollama launch claude --model gemma4:e2b

# --- Docker Network ---
networks: ## 모든 Docker 네트워크 및 컨테이너 상세 정보 표시
	@{ \
	echo "NETWORK|SUBNET|CONTAINER|IP_ADDRESS"; \
	for net in $$(docker network ls --format "{{.Name}}"); do \
		subnet=$$(docker network inspect $$net --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' | xargs); \
		[ -z "$$subnet" ] && subnet="none"; \
		docker network inspect $$net --format '{{range .Containers}}'$$net'|'$$subnet'|{{.Name}}|{{.IPv4Address}}{{"\n"}}{{end}}' | grep . || \
		echo "$$net|$$subnet|-|-"; \
	done; \
	} | column -t -s '|'
