
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
docker compose run -e /app/.env --rm worker \
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


docker compose run --rm -v .:/app -w /app \
   -e DOCKER_MODE=true -e HEADLESS=true -e TOTAL_SCROLLS=20 \
   worker uv run python -m app.main \
   --source LinkedIn --page 1



```




***




`ECONNREFUSED 127.0.0.1:9222` 오류는 Playwright(또는 CDP 기반 도구)가 브라우저 제어 포트에 접속하려 했으나, 해당 포트가 열려 있지 않거나 프로세스가 응답하지 않을 때 발생합니다. 윈도우 11과 WSL2 환경에서 공통적으로 발생하는 이 현상을 해결하기 위한 체크리스트입니다.

---

### 1. 좀비 프로세스 및 포트 점유 확인
이전에 실행되었던 크롬 인스턴스가 비정상 종료되면서 포트를 물고 있거나, 프로세스가 꼬여있을 수 있습니다.

* **PowerShell(관리자 권한)에서 실행:**
    ```powershell
    # 9222 포트를 사용 중인 프로세스 확인
    netstat -ano | findstr :9222

    # 실행 중인 모든 크롬 관련 프로세스 강제 종료
    taskkill /F /IM chrome.exe /T
    ```
* **WSL2 터미널에서 실행:**
    ```bash
    killall chrome 2>/dev/null
    ```

### 2. WSL2에서의 연결 이슈 (호스트 IP 확인)
WSL2 내부에서 윈도우에 설치된 크롬을 제어하려 할 때, `127.0.0.1`은 WSL2 자신을 가리킵니다. 윈도우 호스트의 크롬에 접속하려면 **호스트 IP**를 사용해야 합니다.

* **해결 방법:** 연결 주소를 `127.0.0.1` 대신 윈도우 호스트 IP(보통 `cat /etc/resolv.conf`에서 확인되는 `nameserver` 주소)로 변경해 보세요.
* **방화벽 확인:** 윈도우 방화벽이 포트 `9222`를 차단하고 있는지 확인이 필요합니다.

### 3. 크롬 실행 옵션(Flags) 수동 검증
도구가 크롬을 띄우지 못한다면, 직접 터미널에서 원격 디버깅 모드로 실행되는지 확인해야 합니다.

* **PowerShell에서 수동 실행 테스트:**
    ```powershell
    chrome --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_dev"
    ```
    위 명령어로 크롬이 정상적으로 뜨는지 확인하세요. 만약 실행되지 않는다면 크롬 설치 파일 자체가 손상되었을 가능성이 큽니다.

### 4. GPU 가속 및 샌드박스 이슈
가상화 환경이나 특정 보안 모듈이 충돌할 때 브라우저 초기화가 실패합니다. Antigravity 설정이나 실행 스크립트의 `args`에 아래 옵션을 추가해 보세요.

* `--disable-gpu`
* `--no-sandbox`
* `--disable-dev-shm-usage`

### 5. Antigravity 및 Playwright 종속성 재설치
Antigravity 버전(1.23.2)과 현재 설치된 Playwright 브라우저 바이너리 간의 버전 불일치일 수 있습니다.

* **VSCode 터미널:**
    ```bash
    # Playwright 브라우저 및 시스템 종속성 강제 재설치
    npx playwright install --with-deps chrome
    ```


***

로그를 보니 단순히 포트 문제가 아니라, **WSL2 내부에 설치된 Chromium(Snap 버전) 환경** 자체가 깨졌거나 필요한 라이브러리가 누락된 상태입니다. 특히 `libpxbackend-1.0.so` 로드 실패와 D-Bus 서비스(UPower) 부재가 실행을 가로막고 있습니다.

데이터 엔지니어링 환경에서 흔히 겪는 Snap 패키지 관련 이슈로 보이는데, 아래 단계별로 조치해 보세요.

---

### 1. Snap Chromium의 라이브러리 경로 초기화
`libgiolibproxy.so` 관련 에러는 Snap 환경의 캐시가 꼬였을 때 자주 발생합니다. 캐시를 강제로 삭제하여 재생성하게 합니다.

```bash
rm -rf ~/snap/chromium/common/.cache/gio-modules
# 이후 다시 실행 시도
chromium-browser --remote-debugging-port=9222 --headless=new
```

### 2. 누락된 시스템 라이브러리 설치
WSL2(Ubuntu/Debian 기준)에서 브라우저 실행에 필요한 최소 GUI 및 시스템 라이브러리가 없을 때 발생하는 에러입니다. 다음 패키지들을 설치해 주세요.

```bash
sudo apt update
sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 upower
```
* `upower`: 로그에 나타난 `org.freedesktop.UPower` 에러를 해결하기 위해 필요합니다.

### 3. (가장 권장) Snap 대신 Debian/Ubuntu 바이너리로 교체
WSL2에서 Snap으로 설치된 Chromium은 샌드박스 보안 정책 때문에 외부 연결(CDP)이나 특정 라이브러리 호출 시 문제가 잦습니다. 가급적 **Playwright 내부 바이너리**를 직접 사용하거나 `apt`로 재설치하는 것이 정신 건강에 이롭습니다.

* **Playwright 전용 브라우저 설치:**
  ```bash
  # 프로젝트 디렉토리에서 실행
  npx playwright install chromium
  ```
* **기존 Snap 삭제 후 직접 설치:**
  ```bash
  sudo snap remove chromium
  sudo apt install chromium-browser
  ```

### 4. CDP 접속을 위한 명시적 실행 옵션
브라우저가 뜨더라도 `ECONNREFUSED`가 계속된다면, WSL2 내부의 루프백 주소 인식이 문제일 수 있습니다. 실행 시 주소를 명시해 보세요.

```bash
chromium-browser --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --headless=new --disable-gpu --no-sandbox
```

---

**요약하자면:**
로그상의 `libpxbackend` 에러는 무시해도 실행되는 경우가 많으나, 실제 실행이 안 되는 핵심 이유는 **필수 라이브러리(`upower` 등) 누락** 또는 **Snap 샌드박스 제한**일 가능성이 큽니다. `apt install upower`를 먼저 해보시고, 안 된다면 Snap 버전 Chromium을 지우고 Playwright가 직접 관리하는 바이너리를 사용하시는 걸 추천드립니다.