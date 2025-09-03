# ===================================================================
#                      IMPORTS & CONFIGURATIONS
# ===================================================================
import os
import pygame
import subprocess
import time

# --- 동화 설정 ---
TEXTBOOK_DIR = "/home/drboom/py_project/hanium_snowdream/function/function_textbook/"
REF_AUDIO_PATH = "/home/drboom/py_project/shortform/route/kor_male.wav"
GPT_SOVITS_DIR = "/home/drboom/py_project/GPT-SoVITS"

# 동화 선택 상태
current_story_index = 0
current_language = "kor"  # 기본값: 한국어
available_stories = []

# pygame 초기화
pygame.mixer.init()

# ===================================================================
#                      HELPER FUNCTIONS
# ===================================================================

def get_available_stories():
    """사용 가능한 동화 목록을 반환합니다."""
    stories = []
    if os.path.exists(TEXTBOOK_DIR):
        for item in os.listdir(TEXTBOOK_DIR):
            story_dir = os.path.join(TEXTBOOK_DIR, item)
            if os.path.isdir(story_dir):
                # kor, eng 파일이 모두 있는지 확인
                kor_file = os.path.join(story_dir, f"{item}_kor.txt")
                eng_file = os.path.join(story_dir, f"{item}_eng.txt")
                if os.path.exists(kor_file) and os.path.exists(eng_file):
                    stories.append(item)
    return stories

def read_story_file(story_name, language):
    """동화 파일을 읽어서 줄별로 반환합니다."""
    file_path = os.path.join(TEXTBOOK_DIR, story_name, f"{story_name}_{language}.txt")
    if not os.path.exists(file_path):
        print(f"❌ 동화 파일을 찾을 수 없습니다: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        print(f"❌ 동화 파일 읽기 오류: {e}")
        return None

def create_wav_filename(story_name, language, line_number):
    """WAV 파일명을 생성합니다."""
    return f"{story_name}_{language}_{line_number}.wav"

def check_wav_exists(story_name, language, line_number):
    """WAV 파일이 존재하는지 확인합니다."""
    wav_dir = os.path.join(TEXTBOOK_DIR, story_name)
    wav_file = os.path.join(wav_dir, create_wav_filename(story_name, language, line_number))
    return os.path.exists(wav_file)

def generate_tts_for_line(text, output_path):
    """한 줄의 텍스트를 TTS로 변환합니다."""
    try:
        cmd = [
            'conda', 'run', '-n', 'GPTSoVits', 'python', 'tts_cli.py',
            '--text', text,
            '--ref_audio', REF_AUDIO_PATH,
            '--output', output_path
        ]
        print(f"🔊 TTS 생성 중: '{text[:30]}...'")
        result = subprocess.run(cmd, cwd=GPT_SOVITS_DIR, timeout=300, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ TTS 생성 완료: {output_path}")
            return True
        else:
            print(f"❌ TTS 생성 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ TTS 실행 오류: {e}")
        return False

def check_cancel_signal():
    """취소 신호를 확인합니다."""
    cancel_signal_file = "/tmp/cancel_story_signal.txt"
    try:
        if os.path.exists(cancel_signal_file):
            with open(cancel_signal_file, 'r') as f:
                signal = f.read().strip()
            if signal == "1":
                # 신호 리셋
                with open(cancel_signal_file, 'w') as f:
                    f.write("0")
                return True
    except:
        pass
    return False

def play_wav_file(wav_path):
    """WAV 파일을 재생합니다. (취소 버튼 감지 가능)"""
    try:
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()
        
        # 재생이 끝날 때까지 대기 (취소 버튼 감지)
        while pygame.mixer.music.get_busy():
            # 취소 신호 확인
            if check_cancel_signal():
                print("⏹️  취소 버튼 감지! 동화 재생을 중단합니다.")
                pygame.mixer.music.stop()
                return False
            pygame.time.wait(50)  # 더 빠른 반응을 위해 50ms로 단축
        
        return True
    except Exception as e:
        print(f"❌ WAV 재생 오류: {e}")
        return False

def read_story_title(story_name, language):
    """동화 제목을 읽어줍니다."""
    title_text = f"동화 제목 : {language} {story_name}"
    title_wav = os.path.join(TEXTBOOK_DIR, story_name, f"{story_name}_{language}_title.wav")
    
    # 제목 WAV 파일이 없으면 생성
    if not os.path.exists(title_wav):
        print(f"📖 동화 제목 TTS 생성 중: '{title_text}'")
        if generate_tts_for_line(title_text, title_wav):
            print("✅ 제목 TTS 생성 완료")
        else:
            print("❌ 제목 TTS 생성 실패")
            return False
    
    # 제목 재생
    print(f"📖 동화 제목 재생: {title_text}")
    return play_wav_file(title_wav)

def read_story_content(story_name, language):
    """동화 내용을 한 줄씩 읽어줍니다. (취소 기능 지원)"""
    lines = read_story_file(story_name, language)
    if not lines:
        return False
    
    wav_dir = os.path.join(TEXTBOOK_DIR, story_name)
    
    for i, line in enumerate(lines, 1):
        # 각 줄 시작 전에 취소 신호 확인
        if check_cancel_signal():
            print("⏹️  동화 읽기가 취소되었습니다.")
            return False
            
        wav_filename = create_wav_filename(story_name, language, i)
        wav_path = os.path.join(wav_dir, wav_filename)
        
        # WAV 파일이 없으면 TTS 생성
        if not os.path.exists(wav_path):
            print(f"📖 {i}번째 줄 TTS 생성 중...")
            if not generate_tts_for_line(line, wav_path):
                print(f"❌ {i}번째 줄 TTS 생성 실패")
                continue
        
        # WAV 파일 재생
        print(f"📖 {i}번째 줄 재생 중...")
        play_result = play_wav_file(wav_path)
        if not play_result:
            # False가 반환되면 취소 또는 오류
            if check_cancel_signal() or play_result is False:
                print("⏹️  동화 읽기가 중단되었습니다.")
                return False
            print(f"❌ {i}번째 줄 재생 실패")
            continue
        
        # 줄 간 대기 중에도 취소 신호 확인
        for _ in range(5):  # 0.5초를 0.1초씩 5번으로 분할
            if check_cancel_signal():
                print("⏹️  동화 읽기가 취소되었습니다.")
                return False
            time.sleep(0.1)
    
    print("✅ 동화 읽기 완료!")
    return True

# ===================================================================
#                      MAIN FUNCTIONS
# ===================================================================

def start_story_mode():
    """동화 모드를 시작합니다."""
    global current_story_index, available_stories
    
    print("\n" + "---" * 15)
    print("📚 동화 모드 시작")
    print("---" * 15)
    
    # 사용 가능한 동화 목록 가져오기
    available_stories = get_available_stories()
    if not available_stories:
        print("❌ 사용 가능한 동화가 없습니다.")
        return
    
    current_story_index = 0
    print(f"📚 사용 가능한 동화: {', '.join(available_stories)}")
    
    # 현재 보유 중인 동화책 안내
    announce_available_stories()
    
    # 첫 번째 동화 제목 읽기
    announce_current_story()

def create_announcement_parts():
    """동화 안내에 필요한 기본 WAV 파일들을 생성합니다."""
    announcement_dir = os.path.join(TEXTBOOK_DIR, "announcements")
    os.makedirs(announcement_dir, exist_ok=True)
    
    # 기본 문구들
    parts = {
        "prefix": "사용가능한",
        "suffix": "입니다"
    }
    
    for part_name, text in parts.items():
        wav_path = os.path.join(announcement_dir, f"{part_name}.wav")
        if not os.path.exists(wav_path):
            print(f"📢 {part_name} TTS 생성 중: '{text}'")
            if generate_tts_for_line(text, wav_path):
                print(f"✅ {part_name} TTS 생성 완료")
            else:
                print(f"❌ {part_name} TTS 생성 실패")
                return False
    
    return True

def create_story_title_wavs():
    """각 동화 제목의 WAV 파일을 생성합니다."""
    announcement_dir = os.path.join(TEXTBOOK_DIR, "announcements")
    os.makedirs(announcement_dir, exist_ok=True)
    
    for story in available_stories:
        wav_path = os.path.join(announcement_dir, f"story_{story}.wav")
        if not os.path.exists(wav_path):
            print(f"📖 동화 제목 TTS 생성 중: '{story}'")
            if generate_tts_for_line(story, wav_path):
                print(f"✅ '{story}' TTS 생성 완료")
            else:
                print(f"❌ '{story}' TTS 생성 실패")
                return False
    
    return True

def combine_wav_files(wav_files, output_path):
    """여러 WAV 파일을 하나로 합성합니다."""
    try:
        import wave
        import numpy as np
        
        # 모든 WAV 파일을 읽어서 합성
        combined_data = []
        sample_rate = None
        
        for wav_file in wav_files:
            if os.path.exists(wav_file):
                with wave.open(wav_file, 'rb') as wf:
                    if sample_rate is None:
                        sample_rate = wf.getframerate()
                        channels = wf.getnchannels()
                        sample_width = wf.getsampwidth()
                    
                    data = wf.readframes(wf.getnframes())
                    combined_data.append(data)
        
        # 합성된 데이터를 하나의 WAV 파일로 저장
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(combined_data))
        
        return True
    except Exception as e:
        print(f"❌ WAV 파일 합성 오류: {e}")
        return False

def announce_available_stories():
    """현재 보유 중인 동화책을 TTS로 안내합니다."""
    if not available_stories:
        return False
    
    # 기본 문구 WAV 파일들 생성
    if not create_announcement_parts():
        return False
    
    # 각 동화 제목 WAV 파일들 생성
    if not create_story_title_wavs():
        return False
    
    # 합성할 WAV 파일 목록 생성
    announcement_dir = os.path.join(TEXTBOOK_DIR, "announcements")
    wav_files = []
    
    # "사용가능한"
    wav_files.append(os.path.join(announcement_dir, "prefix.wav"))
    
    # 각 동화 제목들
    for story in available_stories:
        wav_files.append(os.path.join(announcement_dir, f"story_{story}.wav"))
    
    # "입니다"
    wav_files.append(os.path.join(announcement_dir, "suffix.wav"))
    
    # 최종 합성 파일 경로
    final_wav = os.path.join(announcement_dir, "available_stories_combined.wav")
    
    # 합성된 파일이 없으면 생성
    if not os.path.exists(final_wav):
        print("🔗 동화 목록 WAV 파일 합성 중...")
        if combine_wav_files(wav_files, final_wav):
            print("✅ 동화 목록 WAV 파일 합성 완료")
        else:
            print("❌ 동화 목록 WAV 파일 합성 실패")
            return False
    
    # 합성된 파일 재생
    story_list = ", ".join(available_stories)
    print(f"📢 동화책 목록 재생: 사용가능한 동화는 {story_list}입니다.")
    return play_wav_file(final_wav)

def announce_current_story():
    """현재 선택된 동화의 제목을 읽어줍니다."""
    if not available_stories:
        return False
    
    current_story = available_stories[current_story_index]
    story_title_text = f"선택된 동화는 {current_story}입니다."
    
    # 동화 안내 WAV 파일을 저장할 디렉토리 생성
    announcement_dir = os.path.join(TEXTBOOK_DIR, "announcements")
    os.makedirs(announcement_dir, exist_ok=True)
    
    title_wav = os.path.join(announcement_dir, f"selected_story_{current_story_index}.wav")
    
    # 제목 WAV 파일이 없으면 생성
    if not os.path.exists(title_wav):
        print(f"📖 동화 제목 TTS 생성 중: '{story_title_text}'")
        if generate_tts_for_line(story_title_text, title_wav):
            print("✅ 제목 TTS 생성 완료")
        else:
            print("❌ 제목 TTS 생성 실패")
            return False
    
    # 제목 재생
    print(f"📖 동화 제목 재생: {story_title_text}")
    return play_wav_file(title_wav)

def select_next_story():
    """다음 동화를 선택합니다."""
    global current_story_index
    if not available_stories:
        return
    
    current_story_index = (current_story_index + 1) % len(available_stories)
    print(f"➡️ 다음 동화로 이동: {available_stories[current_story_index]}")
    announce_current_story()

def select_previous_story():
    """이전 동화를 선택합니다."""
    global current_story_index
    if not available_stories:
        return
    
    current_story_index = (current_story_index - 1) % len(available_stories)
    print(f"⬅️ 이전 동화로 이동: {available_stories[current_story_index]}")
    announce_current_story()

def read_selected_story():
    """현재 선택된 동화를 읽어줍니다."""
    if not available_stories:
        print("❌ 선택된 동화가 없습니다.")
        return
    
    selected_story = available_stories[current_story_index]
    print(f"📖 '{selected_story}' 동화를 읽어드립니다...")
    read_story(selected_story, current_language)

def read_story(story_name, language):
    """동화를 읽어줍니다."""
    print(f"\n📖 '{story_name}' 동화를 읽어드립니다...")
    
    # 1. 제목 읽기
    if not read_story_title(story_name, language):
        print("❌ 제목 읽기 실패")
        return
    
    # 2. 내용 읽기
    if not read_story_content(story_name, language):
        print("❌ 내용 읽기 실패")
        return
    
    print("🎉 동화 읽기 완료!")

# ===================================================================
#                      EXPORT FUNCTIONS
# ===================================================================

def go_to_fairytale():
    """동화 기능을 실행합니다."""
    print("🧚 '동화' 기능을 실행합니다.")
    start_story_mode() 