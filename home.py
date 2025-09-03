import time
import sys
import os
import warnings

# 모든 경고 숨기기
warnings.filterwarnings("ignore")

# pygame 경고 숨기기
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from connect_arduino import initialize_connection, read_signal, send_signal, close_connection
from function_call import execute_function, execute_selected_function

def main():
    """
    프로젝트의 메인 실행 루프.
    아두이노 연결을 확인하고, 신호를 받아 기능 호출을 지시합니다.
    """
   
    # 1. 아두이노 연결 시도
    ser = initialize_connection()

    # 연결에 실패하면 프로그램 종료
    if not ser:
        print("프로그램을 종료합니다.")
        return

    try:
        print("한이음 눈송이 꿈 프로젝트 시작")
        print("조이스틱 조작법:")
        print("   위/아래 : 기능 순환")
        print("   상호작용 버튼: 선택된 기능 실행")
        print("아두이노 레버 조작을 기다립니다...")
        
        while True:
            # 2. 아두이노로부터 신호 읽기
            signal = read_signal(ser)
           
            # 3. 신호가 있으면 해당 기능 실행
            if signal :
                execute_function(signal)
                send_signal(ser)  # 아두이노 플래그 리셋
                
            # 불필요한 CPU 사용을 막기 위해 잠시 대기
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 중단되었습니다.")
    finally:
        # 4. 프로그램 종료 시 연결 해제
        close_connection(ser)
        print("프로그램을 안전하게 종료합니다.")

if __name__ == "__main__":
    main()