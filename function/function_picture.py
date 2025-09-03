# ===================================================================
#                      IMPORTS & CONFIGURATIONS
# ===================================================================
import cv2
import requests
import json
import base64
import os
import time
import subprocess
import pygame

# --- LLaVA & TTS 설정 ---
OLLAMA_URL = "http://localhost:11434/api/generate"
LLAVA_MODEL = "llava"
CAPTURE_FILE = "capture.jpg"
REF_AUDIO_PATH = "/home/drboom/py_project/shortform/route/kor_male.wav"
TTS_OUTPUT_DIR = "/home/drboom/py_project/snowdream/"
GPT_SOVITS_DIR = "/home/drboom/py_project/GPT-SoVITS"  # 경로 수정

# 사진 촬영 사운드 설정
PHOTO_SOUND_DIR = "/home/drboom/py_project/hanium_snowdream/function/sound/"
PHOTO_AIMING_SOUND = "photo_aiming.mp3"
PHOTO_CHEESE_SOUND = "photo_cheese.mp3"

# 음성 안내 TTS 캐시 설정
TTS_CACHE_DIR = "/home/drboom/py_project/hanium_snowdream/function/tts_cache/"
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

# pygame 초기화
pygame.mixer.init()

# ===================================================================
#                      HELPER FUNCTIONS (사진 분석, TTS 등)
# ===================================================================

def generate_tts_for_text(text, output_path):
    """GPT-SoVITS를 사용해서 텍스트를 TTS로 변환"""
    try:
        # GPT-SoVits 디렉토리 존재 확인
        if not os.path.exists(GPT_SOVITS_DIR):
            print(f"❌ GPT-SoVits 디렉토리를 찾을 수 없습니다: {GPT_SOVITS_DIR}")
            return False
        
        # TTS 명령 실행
        cmd = [
            'conda', 'run', '-n', 'GPTSoVits', 'python', 'tts_cli.py',
            '--text', text,
            '--ref_audio', REF_AUDIO_PATH,
            '--output', output_path
        ]
        print(f"🔊 '{text}' 음성으로 변환 중...")
        result = subprocess.run(cmd, cwd=GPT_SOVITS_DIR, timeout=300, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ TTS 변환 완료: {output_path}")
            return True
        else:
            print(f"❌ TTS 변환 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ TTS 실행 오류: {e}")
        return False

def ensure_tts_wav_exists(text, wav_filename):
    """TTS WAV 파일이 없으면 생성, 있으면 바로 사용"""
    wav_path = os.path.join(TTS_CACHE_DIR, wav_filename)
    
    if os.path.exists(wav_path):
        print(f"✅ 기존 음성 파일 사용: {wav_filename}")
        return wav_path
    else:
        print(f"🔊 음성 파일 생성 중: '{text}'")
        if generate_tts_for_text(text, wav_path):
            return wav_path
        else:
            print(f"❌ 음성 파일 생성 실패: {wav_filename}")
            return None

def play_cached_announcement(text, wav_filename):
    """캐시된 음성 안내를 재생합니다"""
    wav_path = ensure_tts_wav_exists(text, wav_filename)
    if wav_path:
        try:
            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()
            
            # 재생 완료까지 대기
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            return True
        except Exception as e:
            print(f"❌ 음성 재생 오류: {e}")
            return False
    return False

def play_photo_sound_sequence():
    """사진 촬영 사운드 시퀀스를 재생합니다."""
    try:
        # 1. aiming 사운드 재생
        aiming_path = os.path.join(PHOTO_SOUND_DIR, PHOTO_AIMING_SOUND)
        if os.path.exists(aiming_path):
            print("🎯 사진 촬영 준비 사운드 재생 중...")
            pygame.mixer.music.load(aiming_path)
            pygame.mixer.music.play()
            
            # aiming 사운드 끝날 때까지 대기
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        
        # 2. cheese 사운드 재생
        cheese_path = os.path.join(PHOTO_SOUND_DIR, PHOTO_CHEESE_SOUND)
        if os.path.exists(cheese_path):
            print("📸 치즈! 사운드 재생 중...")
            pygame.mixer.music.load(cheese_path)
            pygame.mixer.music.play()
            
            # cheese 사운드 끝날 때까지 대기
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            print("📸 사진 촬영!")
        else:
            print(f"❌ cheese 사운드 파일을 찾을 수 없습니다: {cheese_path}")
            
    except Exception as e:
        print(f"❌ 사진 촬영 사운드 재생 오류: {e}")

def capture_image_from_webcam():
    """웹캠에서 이미지를 캡처하여 파일로 저장하고 경로를 반환"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return None
    
    print("📸 사진 촬영 사운드 시퀀스 시작...")
    
    # 사진 촬영 사운드 시퀀스 재생
    play_photo_sound_sequence()
    
    # 사운드 시퀀스 끝나면 실제 촬영
    ret, frame = cap.read()
    if not ret:
        print("❌ 프레임을 캡처할 수 없습니다.")
        cap.release()
        return None
    
    # 이미지 품질 조정하여 저장 (압축)
    cv2.imwrite(CAPTURE_FILE, frame, [cv2.IMWRITE_JPEG_QUALITY, 70])  # 품질 70%로 압축
    print(f"✅ '{CAPTURE_FILE}'으로 사진 저장 완료 (압축됨).")
    cap.release()
    return CAPTURE_FILE

def image_to_base64(filepath):
    """이미지 파일을 Base64 문자열로 변환 (추가 압축 포함)"""
    from PIL import Image
    import io
    
    # PIL로 이미지 열기
    with Image.open(filepath) as img:
        # JPEG 포맷으로 추가 압축
        buffer = io.BytesIO()
        
        # RGB로 변환 (JPEG 호환성)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 크기 조정 (최대 800x600)
        img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        
        # 품질 60으로 저장
        img.save(buffer, format='JPEG', quality=60, optimize=True)
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def ask_llava_about_image(image_path, prompt):
    """LLaVA에게 이미지에 대해 질문하고 답변을 반환 (음성 안내 포함)"""
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일이 없습니다: {image_path}")
        return None
    
    # 1. 분석 시작 음성 안내
    print("🤖 LLaVA에게 이미지에 대해 질문 중...")
    play_cached_announcement(
        "인공지능이 사진을 분석하고 있습니다.",
        "photo_analysis_start.wav"
    )
    
    encoded_image = image_to_base64(image_path)
    data = { "model": LLAVA_MODEL, "prompt": prompt, "images": [encoded_image], "stream": False }
    
    print(f"📝 프롬프트: {prompt}")
    print(f"🖼️ 이미지 크기: {len(encoded_image)} characters")
    
    # 2. 분석 진행 중 음성 안내
    print("🕐 이미지 분석 요청 중... (시간이 걸릴 수 있습니다)")
    play_cached_announcement(
        "분석이 진행 중입니다. 잠시만 기다려주세요.",
        "photo_analysis_progress.wav"
    )
    
    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=120)  # 타임아웃 증가
        print("✅ 분석 완료!")
        
        # 3. 분석 완료 음성 안내
        play_cached_announcement(
            "분석이 완료되었습니다.",
            "photo_analysis_complete.wav"
        )
        response.raise_for_status()
        full_response = response.json().get("response", "")
        print(f"\n💬 LLaVA 답변: {full_response.strip()}")
        return full_response
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 연결 오류: Ollama 서버가 실행 중인지 확인하세요")
        print("💡 해결방법: 'ollama serve' 명령어로 서버를 시작하세요")
        return None
    except requests.exceptions.Timeout as e:
        print(f"❌ 요청 시간 초과: 이미지가 너무 크거나 서버가 바쁩니다")
        return None
    except requests.RequestException as e:
        print(f"❌ API 요청 오류: {e}")
        return None

def stop_llava():
    """LLaVA 모델을 종료하여 TTS를 위한 메모리를 확보"""
    try:
        print("🔄 LLaVA 모델을 종료하여 메모리를 확보합니다...")
        subprocess.run(['ollama', 'stop', 'llava'], capture_output=True, text=True, timeout=10)
        return True
    except Exception as e:
        print(f"⚠️ LLaVA 종료 중 오류: {e}")
        return False

def start_llava():
    """LLaVA 모델을 다시 로드"""
    try:
        print("🔄 LLaVA 모델을 다시 로드합니다...")
        subprocess.run(['ollama', 'run', 'llava', ''], capture_output=True, text=True, timeout=30)
        return True
    except Exception as e:
        print(f"⚠️ LLaVA 로드 중 오류: {e}")
        return False

def text_to_speech(text, output_file="response.wav"):
    """텍스트를 음성으로 변환하여 wav 파일 생성하고 스피커로 재생 (음성 안내 포함)"""
    stopped_successfully = False
    try:
        if stop_llava():
            stopped_successfully = True
        
        output_path = os.path.join(TTS_OUTPUT_DIR, output_file)
        
        # GPT-SoVits 디렉토리 존재 확인
        if not os.path.exists(GPT_SOVITS_DIR):
            print(f"❌ GPT-SoVits 디렉토리를 찾을 수 없습니다: {GPT_SOVITS_DIR}")
            return False
        
        # TTS 변환 시작 음성 안내
        play_cached_announcement(
            "결과를 음성으로 변환하고 있습니다.",
            "photo_tts_converting.wav"
        )
        
        cmd = [
            'conda', 'run', '-n', 'GPTSoVits', 'python', 'tts_cli.py',
            '--text', text,
            '--ref_audio', REF_AUDIO_PATH,
            '--output', output_path
        ]
        print(f"🔊 '{text}' 음성으로 변환 중...")
        result = subprocess.run(cmd, cwd=GPT_SOVITS_DIR, timeout=300, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 음성 변환 완료! 파일: {output_path}")
            
            # 스피커로 바로 재생
            try:
                print("🔊 pygame으로 스피커 재생 중...")
                pygame.mixer.music.load(output_path)
                pygame.mixer.music.play()
                
                # 재생이 끝날 때까지 대기
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                print("✅ 오디오 재생 완료!")
                
            except Exception as e:
                print(f"❌ pygame 오디오 재생 오류: {e}")
                # pygame 실패 시 aplay로 재시도
                try:
                    print("🔄 aplay로 재생 시도...")
                    subprocess.run(['aplay', output_path], timeout=60)
                    print("✅ 오디오 재생 완료! (aplay 사용)")
                except Exception as e2:
                    print(f"❌ aplay도 실패: {e2}")
                    print("⚠️ 오디오 재생 실패. 파일은 생성되었습니다.")
            
            return True
        else:
            print(f"❌ TTS 실패 (종료 코드: {result.returncode})")
            if result.stderr:
                print(f"오류 메시지: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ TTS 실행 오류: {e}")
        return False
    finally:
        if stopped_successfully:
            start_llava()

def run_photo_analysis():
    """사진 촬영부터 분석, TTS까지의 전체 과정을 실행하는 함수 (음성 안내 포함)"""
    print("\n" + "="*20 + " 📸 사진 분석 시퀀스 시작 " + "="*20)
    
    # 촬영 시작 음성 안내
    play_cached_announcement(
        "사진 촬영을 준비합니다.",
        "photo_capture_ready.wav"
    )
    
    captured_file = capture_image_from_webcam()
    if not captured_file:
        print("사진 촬영 실패. 분석을 중단합니다.")
        return

    prompt = "이 사진에 무엇이 보이나요? 한 줄로 간단히 설명해주세요."
    response_text = ask_llava_about_image(captured_file, prompt)
    
    # 디버깅: 이미지 파일 존재 확인
    if os.path.exists(captured_file):
        file_size = os.path.getsize(captured_file)
        print(f"📁 이미지 파일 크기: {file_size} bytes")
    else:
        print("❌ 이미지 파일이 존재하지 않습니다!")
        return

    if response_text:
        text_to_speech(response_text)

    try:
        os.remove(captured_file)
        print(f"🗑️ 임시 파일 '{captured_file}'을(를) 삭제했습니다.")
    except OSError as e:
        print(f"❌ 임시 파일 삭제 오류: {e}")
        
    print("="*22 + " ✅ 시퀀스 종료 " + "="*22)

# ===================================================================
#                       MAIN FUNCTION
# ===================================================================
def start_picture_mode():
    """사진 분석 모드를 시작하는 메인 함수"""
    print("\n" + "---" * 15)
    print("📸 사진 분석 모드 시작")
    print("---" * 15)
    
    run_photo_analysis()
    
    print("\n" + "---" * 15)
    print("📸 사진 분석 모드 종료")
    print("---" * 15)
