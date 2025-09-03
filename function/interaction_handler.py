#!/usr/bin/env python3
"""
상호작용 버튼 신호 처리 모듈
- 쓰기 모드에서 상호작용 버튼 신호를 writing_mode.py로 전달
"""
import os

def send_interaction_signal():
    """상호작용 버튼 신호 전송"""
    signal_file = "/home/drboom/py_project/hanium_snowdream/function/function_study/interaction_signal.txt"
    try:
        # 디렉토리 생성
        import os
        os.makedirs(os.path.dirname(signal_file), exist_ok=True)
        
        with open(signal_file, 'w') as f:
            f.write("1")
        print("📡 상호작용 버튼 신호 전송됨")
        return True
    except Exception as e:
        print(f"❌ 신호 전송 오류: {e}")
        return False

def clear_interaction_signal():
    """상호작용 신호 초기화"""
    signal_file = "/home/drboom/py_project/hanium_snowdream/function/function_study/interaction_signal.txt"
    try:
        with open(signal_file, 'w') as f:
            f.write("0")
        return True
    except Exception as e:
        print(f"❌ 신호 초기화 오류: {e}")
        return False

def check_interaction_signal():
    """상호작용 신호 확인"""
    signal_file = "/home/drboom/py_project/hanium_snowdream/function/function_study/interaction_signal.txt"
    try:
        if os.path.exists(signal_file):
            with open(signal_file, 'r') as f:
                signal = f.read().strip()
            return signal == "1"
    except Exception as e:
        print(f"❌ 신호 확인 오류: {e}")
    return False

if __name__ == "__main__":
    # 테스트용
    print("상호작용 신호 전송 테스트")
    send_interaction_signal()