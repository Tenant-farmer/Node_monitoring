import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler
import subprocess
import psutil
import os
import asyncio
import nest_asyncio
import logging
from config import TOKEN

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 이벤트 루프 중첩 문제 해결
nest_asyncio.apply()

def get_screen_status():
    result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
    return result.stdout

def get_screen_log(screen_name):
    try:
        # screen 세션의 PID 가져오기
        pid_result = subprocess.run(
            f"screen -ls | grep {screen_name} | awk '{{print $1}}'",
            shell=True,
            capture_output=True,
            text=True
        )
        screen_pid = pid_result.stdout.strip()
        
        if not screen_pid:
            return "⚠️ 노드 상태 확인 불가"
            
        # screen 로그 가져오기 (여러 방법 시도)
        methods = [
            # 방법 1: readlog 사용
            f"screen -S {screen_pid} -X readlog 4 && "
            f"screen -S {screen_pid} -X colon 'readbuf /tmp/screen_{screen_name}.txt' && "
            f"tail -n 4 /tmp/screen_{screen_name}.txt",
            
            # 방법 2: hardcopy 사용
            f"screen -S {screen_pid} -X hardcopy -h /tmp/screen_{screen_name}.txt && "
            f"tail -n 4 /tmp/screen_{screen_name}.txt",
            
            # 방법 3: 대체 hardcopy 방법
            f"screen -S {screen_pid} -Q hardcopy && "
            f"screen -S {screen_pid} -X eval 'hardcopy -h /tmp/screen_{screen_name}.txt' && "
            f"tail -n 4 /tmp/screen_{screen_name}.txt"
        ]
        
        for method in methods:
            result = subprocess.run(
                method,
                shell=True,
                capture_output=True,
                text=True
            )
            
            # 임시 파일 삭제
            subprocess.run(f"rm -f /tmp/screen_{screen_name}.txt", shell=True)
            
            output = result.stdout.strip()
            if output and "cannot be queried" not in output:
                # 프롬프트 상태 확인 (root@...# 형태로 끝나는지)
                last_line = output.strip().split('\n')[-1]
                if 'root@' in last_line and last_line.endswith('#'):
                    return "⚠️ 노드가 중지됨 - 재시작 필요"
                return output
        
        # 모든 방법이 실패한 경우
        return "⚠️ 노드 상태 확인 불가"
    except Exception as e:
        return "⚠️ 노드 상태 확인 불가"

def get_cysic_screens():
    try:
        # screen 목록 가져오기
        result = subprocess.run(
            "screen -ls | grep 'cysic' | awk '{print $1}'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        screens = [screen.strip() for screen in result.stdout.split('\n') if screen.strip()]
        return screens
    except Exception as e:
        logging.error(f"Error getting screen list: {e}")
        return []

async def start(update, context):
    await update.message.reply_text('Cysic node monitoring started.')

async def status(update, context):
    screen_status = get_screen_status()
    await update.message.reply_text(f"현재 screen 상태:\n{screen_status}")
    
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    await update.message.reply_text(f"시스템 상태:\nCPU: {cpu}%\nMemory: {memory}%")

async def check_screen(update, context):
    if not context.args:
        await update.message.reply_text("사용법: /check [screen_name]\n예: /check cysic.main")
        return
    
    screen_name = context.args[0]
    log_content = get_screen_log(screen_name)
    await update.message.reply_text(f"{screen_name} 의 최근 로그:\n{log_content}")

async def check_cysic(update, context):
    screens = get_cysic_screens()
    if not screens:
        await update.message.reply_text("실행 중인 cysic 관련 screen이 없습니다.")
        return
        
    # 각 screen의 로그를 가져오기 전에 잠시 대기
    await asyncio.sleep(0.1)
    
    response = ""
    error_screens = []
    normal_screens = []
    total_screens = len(screens)
    problem_count = 0
    
    for screen in screens:
        log_content = get_screen_log(screen)
        
        # 문제가 있는 스크린 카운트 (중지됨 또는 상태 확인 불가)
        if "⚠️" in log_content:
            problem_count += 1
            error_screens.append(f"{screen} 의 최근 로그:\n{log_content}")
        else:
            normal_screens.append(f"{screen} 의 최근 로그:\n{log_content}")
        
        await asyncio.sleep(0.2)
    
    # 상태 요약 추가
    response += f"📊 전체 노드: {total_screens}개 중 {problem_count}개 문제 발생\n\n"
    
    # 오류가 있는 스크린 먼저 표시
    if error_screens:
        response += "🔴 문제가 있는 스크린:\n"
        response += "\n------------------------------------------------\n".join(error_screens)
        if normal_screens:
            response += "\n\n🟢 정상 동작 중인 스크린:\n"
    
    # 정상 스크린 표시
    if normal_screens:
        if error_screens:
            response += "\n------------------------------------------------\n"
        response += "\n------------------------------------------------\n".join(normal_screens)
    
    if response:
        # 긴 메시지를 여러 개로 나누어 보내기
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part)
                await asyncio.sleep(0.5)
        else:
            await update.message.reply_text(response)
    else:
        await update.message.reply_text("로그를 가져올 수 없습니다.")

async def error_handler(update, context):
    logging.error(f"Exception while handling an update: {context.error}")

async def main():
    # 애플리케이션 빌드
    application = Application.builder().token(TOKEN).build()

    # 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("check", check_screen))
    application.add_handler(CommandHandler("cysic", check_cysic))
    application.add_error_handler(error_handler)

    # 봇 실행
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        # 메인 이벤트 루프 실행
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n봇이 종료되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
