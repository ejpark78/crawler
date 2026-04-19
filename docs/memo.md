
## 💡 Claude Code 활용 시나리오

   1. 초기 세팅: CLAUDE.md 생성 후 "이 가이드에 맞춰 프로젝트 구조를 잡고 uv 환경을 세팅해줘"라고 요청합니다.
   2. 테스트 우선 개발: "GeekNews 파싱을 위한 실패하는 테스트 코드를 먼저 작성하고, 이를 통과하는 크롤러를 만들어줘"라고 지시합니다.
   3. 확장: "Hacker News와 GPTERS도 동일한 TDD 방식으로 추가해줘"라고 확장합니다.
   4. 인프라 가동: "Docker Compose 파일을 생성하고 Airflow에서 모든 소스가 정상적으로 도는지 확인해줘"로 마무리합니다.


## 💡 Claude Code와 TDD로 개발하는 순서
   CLAUDE.md에 위 내용을 반영한 후, Claude Code에게 다음과 같이 명령하세요.
   
   1단계: 실패하는 테스트와 모델 먼저 만들기

   "Pydantic을 사용해 공통 뉴스 모델을 만들고, GeekNews 스크래퍼가 제목과 URL을 올바르게 가져오는지 검증하는 실패하는 테스트 코드를 tests/에 먼저 작성해줘."

   2단계: 테스트를 통과하는 크롤러 구현

   "방금 만든 테스트를 통과할 수 있도록 Scrapling을 사용해 GeekNews 파싱 로직을 완성해줘."

   3단계: 다른 소스로 확장

   "동일한 방식으로 Hacker News와 GPTERS에 대한 테스트를 먼저 쓰고, 기능을 구현해줘."

## 🌟 TDD 적용의 장점

* 사이트 구조 변경 대응: 긱뉴스의 HTML 클래스명이 바뀌면 테스트가 먼저 깨지므로, 운영 환경에서 에러가 나기 전에 즉시 파악하고 수정할 수 있습니다.
* 데이터 품질: Pydantic 모델 검증을 통해 URL 형식이 잘못되었거나 제목이 비어있는 데이터를 사전에 차단합니다.
* 리팩토링 안심: 추상 클래스 구조를 변경하더라도 기존 테스트가 보호해주므로 과감한 코드 개선이 가능합니다.

이제 테스트 코드부터 시작하는 완벽한 파이프라인을 구축해 보세요! 다음 단계로 CI/CD(GitHub Actions) 연동까지 고려해 드릴까요?

```
docker compose -f /app/compose.yml run -e /app/.env --rm worker \
   uv run python -m app.main --source GeekNews --date 2026-04-01 --page 2


docker run --rm -v .:/app -w /app \
   crawler/worker:latest \
   uv run python3 -m pytest tests/test_pytorch_kr.py -v -s


uv run python scratch/test_parsing.py



for page in {2..10}; do 
   echo "# Page: $page"; 
   docker compose run --rm -v .:/app -w /app \
      worker uv run python -m app.main \
      --source PyTorchKR --page $page

   echo "# Page: $page DONE"
done


```

