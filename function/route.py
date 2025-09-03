#!/usr/bin/env python3
"""
TTS 기능을 위한 라우트 파일
"""

import os
import subprocess
import time

# TTS 설정
REF_AUDIO_PATH = "/home/drboom/py_project/shortform/route/kor_male.wav"
GPT_SOVITS_DIR = "/home/drboom/py_project/GPT-SoVITS"

def generate_tts_audio(text, output_path):
    """TTS로 오디오 파일 생성"""
    try:
        # GPT-SoVits 디렉토리 확인
        if not os.path.exists(GPT_SOVITS_DIR):
            print(f"GPT-SoVits 디렉토리를 찾을 수 없습니다: {GPT_SOVITS_DIR}")
            return False
        
        cmd = [
            'conda', 'run', '-n', 'GPTSoVits', 'python', 'tts_cli.py',
            '--text', text,
            '--ref_audio', REF_AUDIO_PATH,
            '--output', str(output_path)
        ]
        
        print(f"TTS 생성 중: '{text[:30]}...'")
        result = subprocess.run(cmd, cwd=GPT_SOVITS_DIR, timeout=300, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"TTS 생성 완료: {output_path}")
            return True
        else:
            print(f"TTS 생성 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"TTS 실행 오류: {e}")
        return False

def kill_tts_processes():
    """TTS 관련 프로세스들을 종료하여 RAM을 해제합니다."""
    try:
        # GPT-SoVits 관련 프로세스 종료
        subprocess.run(['pkill', '-f', 'tts_cli.py'], capture_output=True)
        subprocess.run(['pkill', '-f', 'GPTSoVits'], capture_output=True)
        
        # GPU 메모리 정리 (CUDA 캐시 클리어)
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("GPU 메모리 캐시 정리 완료")
        except:
            pass
            
        print("TTS 프로세스 종료 및 메모리 해제 완료")
        
    except Exception as e:
        print(f"TTS 프로세스 종료 중 오류: {e}")

if __name__ == "__main__":
    # 테스트
    test_text = "테스트 음성입니다."
    test_output = "/tmp/test_tts.wav"
    
    if generate_tts_audio(test_text, test_output):
        print("TTS 테스트 성공!")
    else:
        print("TTS 테스트 실패!") 