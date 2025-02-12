#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# 기존 프로세스 확인 및 종료 함수
cleanup_processes() {
    echo -e "${BLUE}기존 프로세스 정리 중...${NC}"
    
    # Python 프로세스 종료
    pkill -f "python3 monitor.py"
    sleep 2
    
    # 프로세스가 완전히 종료되었는지 확인
    if pgrep -f "python3 monitor.py" > /dev/null; then
        echo -e "${RED}프로세스 강제 종료 중...${NC}"
        pkill -9 -f "python3 monitor.py"
        sleep 2
    fi
}

echo -e "${BLUE}=== Cysic Monitor Bot Installation ===${NC}\n"

# 먼저 기존 프로세스 정리
cleanup_processes

# 필요한 패키지 설치 확인 및 설치
echo -e "${BLUE}[1/3] 필요한 패키지 설치 중...${NC}"
if ! command -v python3 &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-pip
fi

# Python 패키지 설치
echo -e "\n${BLUE}[2/3] Python 패키지 설치 중...${NC}"
pip3 install -U python-telegram-bot psutil nest-asyncio

# API 토큰 입력 받기
echo -e "\n${BLUE}[3/3] 봇 설정${NC}"
while true; do
    echo -e "\n텔레그램 봇 토큰을 입력해주세요 (@BotFather에서 받은 토큰):"
    read token

    # 토큰 형식 검증
    if [[ $token == *":"* ]] && [ ${#token} -gt 45 ]; then
        break
    else
        echo -e "${RED}올바른 형식의 토큰이 아닙니다. 다시 입력해주세요.${NC}"
    fi
done

# config.py 파일 생성
echo -e "\n${BLUE}설정 파일 생성 중...${NC}"
cat > config.py << EOF
# Telegram Bot Token
TOKEN = "$token"
EOF

# 실행 권한 설정
chmod +x monitor.py

echo -e "\n${GREEN}✅ 설치가 완료되었습니다!${NC}"
echo -e "봇을 실행하려면: ${BLUE}python3 monitor.py${NC}" 