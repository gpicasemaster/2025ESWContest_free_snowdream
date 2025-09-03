# ===================================================================
#                      IMPORTS & CONFIGURATIONS
# ===================================================================
import os
import pygame
import subprocess
import time
import wave
import pyaudio
import tempfile
import threading
import queue
import whisper
import requests

# --- 질문 기능 설정 ---
QUESTION_DIR = "/home/drboom/py_project/hanium_snowdream/function/question_data/"
REF_AUDIO_PATH = "/home/drboom/py_project/shortform/route/kor_male.wav"
GPT_SOVITS_DIR = "/home/drboom/py_project/GPT-SoVITS"

# 오디오 녹음 설정
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
MAX_RECORD_SECONDS = 30  # 최대 30초 녹음

# pygame 초기화
pygame.mixer.init()

# 전역 변수
recording_frames = []
is_recording = False
recording_thread = None
recording_started = False  # 녹음이 시작되었는지 추적

# 모델 로드 (한 번만 로드)
try:
    # Whisper 모델 로드
    whisper_model = whisper.load_model("small")
    
    # TinyLlama 모델은 기존 방식 유지 (ollama serve는 이미 실행 중)
    phi_process = None
    
    # TTS는 기존 방식 유지 (서버 파일이 없음)
    tts_process = None
    
except Exception as e:
    print(f"모델 로드 중 오류: {e}")
    whisper_model = None
    phi_process = None
    tts_process = None

# ===================================================================
#                      HELPER FUNCTIONS
# ===================================================================

def create_question_directory():
    """질문 데이터 디렉토리를 생성합니다."""
    os.makedirs(QUESTION_DIR, exist_ok=True)
    return QUESTION_DIR

def start_recording():
    """녹음을 시작합니다."""
    global recording_frames, is_recording, recording_thread, recording_started
    
    if is_recording:
        return
    
    recording_frames = []
    is_recording = True
    recording_started = True
    
    def record_audio_thread():
        global recording_frames, is_recording
        
        try:
            p = pyaudio.PyAudio()
            
            # 사용 가능한 입력 장치 확인
            info = p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            print(f"🔍 사용 가능한 오디오 장치 수: {numdevices}")
            
            # 모든 입력 장치 정보 출력
            print("📋 사용 가능한 입력 장치 목록:")
            input_devices = []
            for i in range(numdevices):
                try:
                    device_info = p.get_device_info_by_index(i)
                    device_name = device_info.get('name', 'Unknown')
                    max_inputs = device_info.get('maxInputChannels', 0)
                    if max_inputs > 0:
                        print(f"  {i}: {device_name} (입력 채널: {max_inputs})")
                        input_devices.append(i)
                except Exception as e:
                    print(f"  {i}: 오류 - {e}")
            
            # 웹캠 마이크 찾기 (C270, webcam, camera 등 키워드)
            device_index = None
            for i in input_devices:
                try:
                    device_info = p.get_device_info_by_index(i)
                    device_name = device_info.get('name', '').lower()
                    if any(keyword in device_name for keyword in ['c270', 'webcam', 'camera', 'usb']):
                        device_index = i
                        print(f"🎤 웹캠 마이크 발견: {device_info.get('name')} (장치 {i})")
                        break
                except:
                    continue
            
            if device_index is None:
                print("⚠️ 웹캠 마이크를 찾을 수 없습니다. 첫 번째 입력 장치를 사용합니다.")
                device_index = input_devices[0] if input_devices else None
            
            if device_index is not None:
                try:
                    device_info = p.get_device_info_by_index(device_index)
                    print(f"🎤 선택된 장치: {device_info.get('name')} (장치 {device_index})")
                except:
                    print(f"⚠️ 장치 {device_index} 정보를 가져올 수 없습니다.")
            else:
                print("❌ 사용 가능한 입력 장치가 없습니다.")
                is_recording = False
                return
            
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            input_device_index=device_index,
                            frames_per_buffer=CHUNK)
            
            print("🎤 녹음 시작... (다시 버튼을 누르면 녹음 종료)")
            
            start_time = time.time()
            while is_recording and (time.time() - start_time) < MAX_RECORD_SECONDS:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    recording_frames.append(data)
                except Exception as e:
                    print(f"❌ 녹음 오류: {e}")
                    break
            
            try:
                stream.stop_stream()
                stream.close()
                p.terminate()
                print("✅ 녹음 스트림 정리 완료")
            except Exception as e:
                print(f"⚠️ 스트림 정리 중 오류: {e}")
            
            print("✅ 녹음 종료")
            
        except Exception as e:
            print(f"❌ 녹음 초기화 오류: {e}")
            is_recording = False
    
    recording_thread = threading.Thread(target=record_audio_thread)
    recording_thread.start()

def stop_recording():
    """녹음을 중단하고 처리합니다."""
    global is_recording, recording_frames, recording_started
    
    print("🔄 녹음 중단 및 처리 시작...")
    
    if not is_recording:
        print("❌ 녹음 중이 아닙니다.")
        return
    
    is_recording = False
    recording_started = False
    
    print("⏳ 녹음 스레드 종료 대기 중...")
    if recording_thread:
        recording_thread.join(timeout=5)  # 5초 타임아웃
        if recording_thread.is_alive():
            print("⚠️ 녹음 스레드가 타임아웃으로 강제 종료됩니다.")
            is_recording = False  # 강제로 종료 플래그 설정
        else:
            print("✅ 녹음 스레드가 정상적으로 종료되었습니다.")
    
    print(f"📊 녹음된 프레임 수: {len(recording_frames)}")
    
    if not recording_frames:
        print("❌ 녹음된 데이터가 없습니다.")
        return
    
    # 녹음 데이터를 WAV 파일로 저장
    temp_wav = os.path.join(QUESTION_DIR, "recorded_question.wav")
    
    # 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(temp_wav), exist_ok=True)
    
    print("💾 녹음 데이터를 WAV 파일로 저장 중...")
    with wave.open(temp_wav, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16비트
        wf.setframerate(RATE)
        wf.writeframes(b''.join(recording_frames))
    
    print(f"📁 녹음 파일 저장 완료: {temp_wav}")
    
    # 즉시 처리 시작
    print("🚀 오디오 처리 시작...")
    process_recorded_audio(temp_wav)

def process_recorded_audio(audio_file):
    """녹음된 오디오를 처리합니다."""
    print("\n" + "="*20 + " 🎤 질문 처리 시작 " + "="*20)
    
    # 1. STT (음성 → 텍스트)
    print("🔍 1단계: Whisper로 음성 인식 중...")
    question_text = speech_to_text(audio_file)
    if not question_text:
        print("❌ 음성 인식 실패")
        return
    
    print(f"✅ 음성 인식 완료: '{question_text}'")
    
    # 2. LLM (질문 → 답변)
    print("🧠 2단계: TinyLlama로 답변 생성 중...")
    answer_text = ask_llama(question_text)
    if not answer_text:
        print("⚠️ TinyLlama 실패, 기본 답변 사용")
        answer_text = "죄송합니다. 질문을 이해하지 못했습니다. 다시 말씀해 주세요."
    
    print(f"✅ 답변 생성 완료: '{answer_text[:100]}...'")
    
    # 3. 스트리밍 TTS (답변 → 음성)
    print("🔊 3단계: 스트리밍 TTS로 음성 변환 중...")
    stream_tts_answer(answer_text)
    
    # 임시 파일 정리
    try:
        os.remove(audio_file)
        print(f"🗑️ 임시 녹음 파일 삭제: {audio_file}")
    except:
        pass
    
    print("="*22 + " ✅ 질문 처리 완료 " + "="*22)

def speech_to_text(audio_file):
    """음성 파일을 텍스트로 변환합니다."""
    try:
        # 모델이 없으면 다시 로드 시도
        global whisper_model
        if whisper_model is None:
            print("Whisper 모델 재로드 시도 중...")
            try:
                whisper_model = whisper.load_model("small")
                print("✅ Whisper 모델 재로드 성공")
            except Exception as load_error:
                print(f"❌ Whisper 모델 재로드 실패: {load_error}")
                return None
        
        # Whisper 모델로 음성 인식
        result = whisper_model.transcribe(audio_file)
        return result["text"].strip()
        
    except Exception as e:
        print(f"음성 인식 중 오류: {e}")
        return None

def ask_llama(question_text):
    """TinyLlama 모델로 질문에 답변합니다."""
    try:
        # TinyLlama 모델로 답변 생성
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": f"질문: {question_text}\n답변:",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "").strip()
            
            if answer:
                return answer
            else:
                print("TinyLlama 모델이 빈 답변을 반환했습니다")
                return None
        else:
            print(f"TinyLlama API 오류: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"TinyLlama 모델 오류: {e}")
        return None

def generate_tts_for_answer(text, output_path):
    """답변 텍스트를 TTS로 변환합니다."""
    try:
        print("🔊 GPT-SoVits TTS로 음성 변환 중...")
        
        # GPT-SoVits TTS 실행
        cmd = [
            'conda', 'run', '-n', 'GPTSoVits', 'python', 'tts_cli.py',
            '--text', text,
            '--ref_audio', REF_AUDIO_PATH,
            '--output', output_path
        ]
        print(f"📝 변환할 텍스트: '{text[:50]}...'")
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

def play_wav_file(wav_path):
    """WAV 파일을 재생합니다."""
    try:
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()
        
        # 재생이 끝날 때까지 대기
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        return True
    except Exception as e:
        print(f"❌ WAV 재생 오류: {e}")
        return False

def stream_tts_answer(answer_text):
    """답변을 문장 단위로 스트리밍 TTS 처리합니다."""
    try:
        print("🔄 스트리밍 TTS 시작...")
        
        # 답변을 문장 단위로 분리 (마침표, 느낌표, 물음표 기준)
        import re
        sentences = re.split('[.!?]', answer_text)
        sentences = [s.strip() for s in sentences if s.strip()]  # 빈 문장 제거
        
        print(f"📝 총 {len(sentences)}개 문장을 순차 처리합니다.")
        
        for i, sentence in enumerate(sentences):
            print(f"🎵 문장 {i+1}/{len(sentences)} 처리 중: '{sentence[:30]}...'")
            
            # 현재 문장 TTS 생성
            sentence_wav = os.path.join(QUESTION_DIR, f"sentence_{i+1}.wav")
            
            if generate_tts_for_answer(sentence, sentence_wav):
                # 현재 문장 재생
                print(f"🔊 문장 {i+1} 재생 중...")
                play_wav_file(sentence_wav)
                print(f"✅ 문장 {i+1} 재생 완료")
                
                # 임시 파일 삭제
                try:
                    os.remove(sentence_wav)
                except:
                    pass
            else:
                print(f"❌ 문장 {i+1} TTS 실패")
        
        print("🎉 스트리밍 TTS 완료!")
        
    except Exception as e:
        print(f"❌ 스트리밍 TTS 오류: {e}")
        # 실패 시 전체 답변을 한 번에 처리
        print("🔄 전체 답변으로 대체 처리...")
        answer_wav = os.path.join(QUESTION_DIR, "answer.wav")
        if generate_tts_for_answer(answer_text, answer_wav):
            play_wav_file(answer_wav)
            try:
                os.remove(answer_wav)
            except:
                pass

# ===================================================================
#                      MAIN FUNCTIONS
# ===================================================================

def start_question_mode():
    """질문 모드를 시작합니다."""
    print("\n" + "---" * 15)
    print("❓ 질문 모드 시작")
    print("---" * 15)
    
    # 질문 데이터 디렉토리 생성
    create_question_directory()
    
    print("💡 상호작용 버튼을 한 번 누르면 녹음 시작, 다시 누르면 녹음 종료됩니다.")
    print("⏰ 최대 30초 동안 녹음 가능합니다.")

def record_and_process_question():
    """질문을 녹음하고 처리하는 전체 과정을 실행합니다."""
    global recording_started
    
    if not recording_started:
        # 첫 번째 버튼 누름: 녹음 시작
        print("🎤 질문 녹음을 시작합니다. (다시 버튼을 누르면 녹음 종료)")
        start_recording()
    else:
        # 두 번째 버튼 누름: 녹음 종료
        print("🛑 질문 녹음을 중단하고 처리합니다.")
        stop_recording()

def stop_question_recording():
    """질문 녹음을 중단하고 처리합니다."""
    # 버튼을 떼면 녹음 중단 및 처리
    stop_recording()

# ===================================================================
#                      EXPORT FUNCTIONS
# ===================================================================

def go_to_question():
    """질문 기능을 실행합니다."""
    print("❓ '질문' 기능을 실행합니다.")
    start_question_mode() 