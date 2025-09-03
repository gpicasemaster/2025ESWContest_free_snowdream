#!/usr/bin/env python3
"""
한이음 눈송이 꿈 프로젝트 - 시스템 실행 스크립트
"""
import os
import sys
import subprocess
import time

def check_dependencies():
    """시스템 의존성 확인"""
    print("🔍 시스템 의존성 확인 중...")
    
    # 필수 디렉토리
    required_dirs = [
        "/home/drboom/py_project/hanium_snowdream/function",
        "/home/drboom/py_project/hanium_snowdream/drawings"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ 필수 디렉토리 없음: {dir_path}")
            return False
        else:
            print(f"✅ 디렉토리 확인: {dir_path}")
    
    # Conda 환경 확인
    try:
        result = subprocess.run(['conda', 'info', '--envs'], capture_output=True, text=True)
        if 'snowdream' not in result.stdout:
            print("❌ snowdream conda 환경이 없습니다")
            return False
        if 'cnn_env' not in result.stdout:
            print("❌ cnn_env conda 환경이 없습니다")
            return False
        print("✅ Conda 환경 확인됨")
    except:
        print("❌ Conda가 설치되지 않았습니다")
        return False
    
    return True

def run_system():
    """메인 시스템 실행"""
    print("🚀 한이음 눈송이 꿈 프로젝트 시작")
    
    if not check_dependencies():
        print("❌ 의존성 확인 실패. 시스템을 시작할 수 없습니다.")
        return False
    
    print("✅ 모든 의존성 확인 완료")
    print("📱 아두이노 연결 대기 중...")
    
    # home.py 실행
    try:
        cmd = [
            '/home/drboom/miniforge3/envs/snowdream/bin/python',
            '/home/drboom/py_project/hanium_snowdream/home.py'
        ]
        
        print("🎯 메인 시스템 실행 중...")
        print("조이스틱과 상호작용 버튼을 사용하여 조작하세요")
        print("Ctrl+C로 종료 가능")
        print("-" * 50)
        
        subprocess.run(cmd, cwd='/home/drboom/py_project/hanium_snowdream')
        
    except KeyboardInterrupt:
        print("\n👋 사용자가 시스템을 종료했습니다")
    except Exception as e:
        print(f"❌ 시스템 실행 오류: {e}")
        return False
    
    return True

def run_test():
    """시스템 테스트 실행"""
    print("🧪 시스템 테스트 실행 중...")
    
    try:
        cmd = [
            '/home/drboom/miniforge3/envs/snowdream/bin/python',
            '/home/drboom/py_project/hanium_snowdream/test_full_system.py'
        ]
        
        result = subprocess.run(cmd, cwd='/home/drboom/py_project/hanium_snowdream')
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")
        return False

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            return 0 if run_test() else 1
        elif sys.argv[1] == 'help':
            print("한이음 눈송이 꿈 프로젝트 실행 스크립트")
            print("\n사용법:")
            print("  python run_system.py        # 메인 시스템 실행")
            print("  python run_system.py test   # 시스템 테스트")
            print("  python run_system.py help   # 도움말")
            return 0
        else:
            print(f"❌ 알 수 없는 옵션: {sys.argv[1]}")
            return 1
    
    return 0 if run_system() else 1

if __name__ == "__main__":
    sys.exit(main())