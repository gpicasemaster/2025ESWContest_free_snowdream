# 실제 기능 모듈들을 임포트합니다.
from function.function_picture import start_picture_mode, play_photo_sound_sequence, run_photo_analysis
from function.function_story import go_to_fairytale, select_next_story, select_previous_story, read_selected_story
from function.function_question import start_question_mode, record_and_process_question, stop_question_recording, go_to_question
from function.function_learning import LearningFunction
import time
import pygame
import os
import subprocess

# 새로운 시스템 임포트
from memory_manager import emergency_exit_to_main, get_memory_status
from navigation_system import nav_manager, NavigationState

# pygame 초기화
pygame.mixer.init()

# 사운드 파일 경로
SOUND_DIR = "/home/drboom/py_project/hanium_snowdream/function/sound/"
SELECT_SOUND_FILES = {
    "사진": "select_photo.mp3",
    "학습": "select_study.mp3", 
    "질문": "select_talk.mp3",
    "동화": "select_story.mp3"
}
FUNCTION_SOUND_FILES = {
    "사진": "function_photo_appear.mp3",
    "학습": "function_study_appear.mp3", 
    "질문": "function_talk_appear.mp3",
    "동화": "function_story_appear.mp3"
}

# 현재 선택된 기능 인덱스 (0: 사진, 1: 학습, 2: 질문, 3: 동화)
current_function_index = 0
functions = ["사진", "학습", "질문", "동화"]

# 마지막 기능 변경 시간을 추적
last_function_change_time = 0
FUNCTION_CHANGE_DELAY = 2.0  # 2초 딜레이 (사운드 재생 시간 고려)

# 사진 모드 상태 추적
in_photo_mode = False

# 동화 모드 상태 추적
in_story_mode = False

# 질문 모드 상태 추적
in_question_mode = False

# 질문 녹음 상태 추적
question_recording_active = False

# 학습 모드 상태 추적
in_learning_mode = False
learning_sub_mode = None  # 'reading' 또는 'writing'
in_writing_mode = False  # 쓰기 모드 활성화 상태
in_reading_mode = False  # 읽기 모드 활성화 상태
reading_learning_instance = None  # 읽기 학습 인스턴스

# 사운드 재생 상태 추적
is_playing_sound = False

# 상호작용 버튼 디바운싱
last_interaction_time = 0
interaction_debounce_delay = 0.5  # 0.5초 디바운싱

# 입력 처리 상태 추적
input_processing_time = 0
INPUT_PROCESSING_DELAY = 0.1  # 0.1초 입력 무시

# 전역 기능 처리 상태 추적
is_processing_function = False

def execute_function(signal):
    """입력된 신호에 따라 기능을 순환하거나 실행합니다."""
    global current_function_index, last_function_change_time, in_photo_mode, in_story_mode, in_question_mode, in_learning_mode, learning_sub_mode, in_writing_mode, in_reading_mode, reading_learning_instance, is_playing_sound, input_processing_time, is_processing_function, last_interaction_time
    
    current_time = time.time()
    
    # 상호작용 버튼('5') 디바운싱 체크
    if signal == '5':
        if current_time - last_interaction_time < interaction_debounce_delay:
            print(f"🚫 상호작용 버튼 디바운싱: {current_time - last_interaction_time:.2f}초 경과, {interaction_debounce_delay}초 대기 중...")
            return
        last_interaction_time = current_time
        print(f"✅ 상호작용 버튼 처리 허용")
    
    # 취소 버튼 (신호 '6') - 최우선 처리! 언제든지 메인 메뉴로 복귀
    if signal == '6':
        print("🔄 취소 버튼 - 메인 메뉴로 복귀")
        handle_cancel_button()
        return
    
    # 기능 처리 중이면 다른 입력 무시 (취소 버튼 제외)
    if is_processing_function:
        print("[DEBUG] 기능 처리 중 - 입력 무시 (취소 버튼은 가능)")
        return
    
    # 입력 처리 중이면 모든 입력 무시
    if current_time - input_processing_time < INPUT_PROCESSING_DELAY:
        return
    
    # 사운드 재생 중이면 모든 입력 무시
    if is_playing_sound:
        return
    
    # 동화 모드에서는 조이스틱으로 동화 선택
    if in_story_mode:
        if signal == '1':  # 위 (이전 동화)
            print("이전 동화로 이동")
            input_processing_time = current_time
            select_previous_story()
        elif signal == '2':  # 아래 (다음 동화)
            print("다음 동화로 이동")
            input_processing_time = current_time
            select_next_story()
        elif signal == '5':  # 상호작용 버튼 (동화 읽기)
            print("선택된 동화를 읽습니다")
            input_processing_time = current_time
            is_processing_function = True  # 기능 처리 시작
            read_selected_story()
            is_processing_function = False  # 기능 처리 완료
            in_story_mode = False  # 동화 읽기 완료 후 모드 종료
            nav_manager.complete_function()  # 네비게이션 시스템에 완료 알림
        return
    
    # 읽기 모드에서는 단계 선택 또는 단어 학습 처리
    if in_reading_mode and reading_learning_instance:
        if reading_learning_instance.in_stage_selection:
            # 단계 선택 중
            if signal == '1':  # 위 (이전 단계)
                print("이전 단계로 이동")
                input_processing_time = current_time
                reading_learning_instance.handle_stage_selection('up')
            elif signal == '3':  # 아래 (다음 단계) - 조이스틱에서 3이 아래로 나옴
                print("다음 단계로 이동")
                input_processing_time = current_time
                reading_learning_instance.handle_stage_selection('down')
            elif signal == '5':  # 상호작용 버튼 (단계 확정)
                print("단계 선택 확정")
                input_processing_time = current_time
                is_processing_function = True
                reading_learning_instance.confirm_stage_selection()
                is_processing_function = False
        elif reading_learning_instance.in_word_learning:
            # 단어 학습 중
            if signal == '5':  # 상호작용 버튼 (다음 단어)
                print("다음 단어로 이동")
                input_processing_time = current_time
                is_processing_function = True
                reading_learning_instance.next_word()
                
                # 학습이 완료되었는지 확인
                if not reading_learning_instance.in_word_learning:
                    in_reading_mode = False
                    reading_learning_instance = None
                    nav_manager.complete_function()
                
                is_processing_function = False
        return
    
    # 쓰기 모드에서는 상호작용 버튼으로 글자 분석 처리 (학습 모드보다 우선)
    if get_writing_active_state():
        if signal == 'BUTTON_PRESS' or signal == '5':  # 버튼을 누름 (임시로 5도 허용)
            input_processing_time = current_time
            is_processing_function = True  # 기능 처리 시작
            
            # 쓰기 버튼 처리
            writing_continues = handle_writing_button()
            if not writing_continues:  # 기능 완료
                # 쓰기가 완료되면 학습 모드 종료
                in_learning_mode = False
                learning_sub_mode = None
                nav_manager.complete_function()  # 네비게이션 시스템에 완료 알림
            
            is_processing_function = False  # 기능 처리 완료
        return

    # 학습 모드에서는 조이스틱으로 읽기/쓰기 선택
    if in_learning_mode:
        if signal == '1' or signal == '2':  # 위/아래 (토글 방식)
            from function.function_learning import LearningFunction
            learning = LearningFunction()
            input_processing_time = current_time
            
            # 현재 선택된 기능과 다른 기능으로 토글
            if learning_sub_mode == 'reading':
                learning_sub_mode = 'writing'
                print("쓰기 기능 선택")
                learning.play_writing_prompt()
            elif learning_sub_mode == 'writing':
                learning_sub_mode = 'reading'
                print("읽기 기능 선택")
                learning.play_reading_prompt()
            else:
                # 처음 선택하는 경우 (기본값: 읽기)
                learning_sub_mode = 'reading'
                print("읽기 기능 선택")
                learning.play_reading_prompt()
        elif signal == '5':  # 상호작용 버튼 (선택 실행)
            if learning_sub_mode:
                print(f"선택된 학습 기능 실행: {learning_sub_mode}")
                input_processing_time = current_time
                is_processing_function = True  # 기능 처리 시작
                from function.function_learning import LearningFunction
                learning = LearningFunction()
                
                # 선택 확인 메시지 재생
                if learning_sub_mode == 'reading':
                    learning.play_reading_selected_prompt()
                    # 읽기 모드로 전환
                    in_reading_mode = True
                    reading_learning_instance = learning
                    learning.start_reading_mode()
                elif learning_sub_mode == 'writing':
                    learning.play_writing_selected_prompt()
                    # 간단한 쓰기 모드 시작
                    go_to_simple_writing()
                    # 쓰기 모드는 별도로 관리되므로 여기서는 학습 모드를 종료하지 않음
                
                is_processing_function = False  # 기능 처리 완료
                
                # 쓰기 모드가 아닌 경우에만 학습 모드 종료
                if learning_sub_mode != 'writing':
                    in_learning_mode = False  # 학습 완료 후 모드 종료 (읽기/쓰기 모드 제외)
                    learning_sub_mode = None
                
                # 읽기 모드나 쓰기 모드가 아닌 경우에만 완료 처리
                if not in_reading_mode and learning_sub_mode != 'writing':
                    nav_manager.complete_function()  # 네비게이션 시스템에 완료 알림
            else:
                print("먼저 읽기 또는 쓰기 기능을 선택해주세요")
        return

    # 질문 모드에서는 상호작용 버튼으로 가짜 녹음 처리
    if in_question_mode:
        if signal == 'BUTTON_PRESS' or signal == '5':  # 버튼을 누름 (임시로 5도 허용)
            input_processing_time = current_time
            is_processing_function = True  # 기능 처리 시작
            
            # 가짜 녹음 상태가 아니면 첫 시작
            if not get_fake_recording_state():
                go_to_simple_question()  # 기능 시작
            else:
                # 가짜 녹음 버튼 처리
                recording_continues = handle_fake_recording_button()
                if not recording_continues:  # 기능 완료
                    in_question_mode = False  # 질문 모드 종료
                    nav_manager.complete_function()  # 네비게이션 시스템에 완료 알림
            
            is_processing_function = False  # 기능 처리 완료
        return
    
    # 기존 쓰기 모드 상호작용 버튼 처리 코드는 writing_mode.py에서 직접 처리됨
    
    # 사진 모드에서는 상호작용 버튼으로 가짜 사진 촬영 처리
    if in_photo_mode:
        if signal == 'BUTTON_PRESS' or signal == '5':  # 버튼을 누름 (임시로 5도 허용)
            input_processing_time = current_time
            is_processing_function = True  # 기능 처리 시작
            
            # 가짜 사진 촬영 상태가 아니면 첫 시작
            if not get_photo_taking_state():
                go_to_simple_photo()  # 기능 시작
            else:
                # 가짜 사진 촬영 버튼 처리
                photo_continues = handle_fake_photo_button()
                if not photo_continues:  # 기능 완료
                    in_photo_mode = False  # 사진 모드 종료
                    nav_manager.complete_function()  # 네비게이션 시스템에 완료 알림
            
            is_processing_function = False  # 기능 처리 완료
        return
    
    # 신호 '5'는 선택된 기능 실행
    if signal == '5':
        if False:  # 사진 모드 처리는 위에서 이미 함
            pass
        else:
            # 일반 모드에서 상호작용 버튼을 누르면 선택된 기능 실행
            print("선택된 기능을 실행합니다")
            input_processing_time = current_time  # 입력 처리 시간 설정
            is_processing_function = True  # 기능 처리 시작
            play_function_sound()  # 실행 시 사운드 재생
            execute_selected_function()
            is_processing_function = False  # 기능 처리 완료
        return
    
    # 0.5초가 지나지 않았으면 기능 변경을 무시
    if current_time - last_function_change_time < FUNCTION_CHANGE_DELAY:
        return
    
    # 입력 4번 제거 - 사용하지 않는 신호 무시
    if signal == '4':
        return
    
    if signal == '1':  # 위 (이전 기능으로 이동)
        current_function_index = (current_function_index - 1) % len(functions)
        print(f"이전 기능으로 이동: {functions[current_function_index]}")
        last_function_change_time = current_time
        input_processing_time = current_time
        play_select_sound()
        
        # 기능 변경 시에만 현재 선택된 기능 표시
        print(f"현재 선택된 기능: {functions[current_function_index]}")
        if in_photo_mode:
            print("사진을 찍으려면 상호작용 버튼을 누르세요")
        else:
            print("기능을 실행하려면 상호작용 버튼을 누르세요")
        return  # 함수 종료
        
    elif signal == '3':  # 아래 (다음 기능으로 이동) - 조이스틱에서 3이 아래로 나옴
        current_function_index = (current_function_index + 1) % len(functions)
        print(f"다음 기능으로 이동: {functions[current_function_index]}")
        last_function_change_time = current_time
        input_processing_time = current_time
        play_select_sound()
        
        # 기능 변경 시에만 현재 선택된 기능 표시
        print(f"현재 선택된 기능: {functions[current_function_index]}")
        if in_photo_mode:
            print("사진을 찍으려면 상호작용 버튼을 누르세요")
        else:
            print("기능을 실행하려면 상호작용 버튼을 누르세요")
        return  # 함수 종료
    
    # 신호가 '1' 또는 '2'일 때만 여기까지 도달 (위에서 return으로 종료됨)

def play_select_sound():
    """현재 선택된 기능의 선택 사운드를 재생합니다."""
    global is_playing_sound
    
    current_function = functions[current_function_index]
    sound_file = SELECT_SOUND_FILES.get(current_function)
    
    if sound_file:
        sound_path = os.path.join(SOUND_DIR, sound_file)
        if os.path.exists(sound_path):
            try:
                is_playing_sound = True
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                
                # 재생이 끝날 때까지 대기 (최대 10초)
                start_time = time.time()
                while pygame.mixer.music.get_busy() and (time.time() - start_time) < 10:
                    pygame.time.wait(100)
                
                # 강제로 재생 중지 (안전장치)
                pygame.mixer.music.stop()
                
                is_playing_sound = False
                
                # 사운드 재생 후 추가 딜레이 (입력 안정화)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"선택 사운드 재생 오류: {e}")
                is_playing_sound = False
        else:
            print(f"선택 사운드 파일을 찾을 수 없습니다: {sound_path}")
    else:
        print(f"'{current_function}'에 대한 선택 사운드 파일이 정의되지 않았습니다.")

def play_function_sound():
    """현재 선택된 기능의 실행 사운드를 재생합니다."""
    global is_playing_sound
    
    current_function = functions[current_function_index]
    sound_file = FUNCTION_SOUND_FILES.get(current_function)
    
    if sound_file:
        sound_path = os.path.join(SOUND_DIR, sound_file)
        if os.path.exists(sound_path):
            try:
                is_playing_sound = True
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                
                # 재생이 끝날 때까지 대기
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                is_playing_sound = False
                
            except Exception as e:
                print(f"실행 사운드 재생 오류: {e}")
                is_playing_sound = False
        else:
            print(f"실행 사운드 파일을 찾을 수 없습니다: {sound_path}")
    else:
        print(f"'{current_function}'에 대한 실행 사운드 파일이 정의되지 않았습니다.")

def execute_selected_function():
    """현재 선택된 기능을 실행합니다."""
    global current_function_index, in_photo_mode, in_story_mode, in_question_mode, in_learning_mode, learning_sub_mode
    
    if current_function_index == 0:
        # 사진 기능: 모드 진입
        in_photo_mode = True
        print("사진 모드 진입")
        print("상호작용 버튼을 눌러서 간단한 사진 기능을 시작하세요")
    elif current_function_index == 1:
        # 학습 기능: 모드 진입
        in_learning_mode = True
        # learning_sub_mode는 초기화하지 않고 기존 값 유지하거나 기본값 'reading' 설정
        if learning_sub_mode is None:
            learning_sub_mode = 'reading'  # 기본값: 읽기
        go_to_study()
        print("학습 모드 진입")
        print("위아래로 읽기/쓰기를 선택하고, 상호작용 버튼으로 실행하세요")
        
        # 현재 선택된 기능 안내
        from function.function_learning import LearningFunction
        learning = LearningFunction()
        if learning_sub_mode == 'reading':
            print("현재 선택: 읽기 기능")
            learning.play_reading_prompt()
        else:
            print("현재 선택: 쓰기 기능")
            learning.play_writing_prompt()
    elif current_function_index == 2:
        # 질문 기능: 모드 진입
        in_question_mode = True
        print("질문 모드 진입")
        print("상호작용 버튼을 눌러서 잡담 기능을 시작하세요")
    elif current_function_index == 3:
        # 동화 기능: 모드 진입
        in_story_mode = True
        go_to_fairytale()
        print("동화 모드 진입")
        print("좌우로 동화를 선택하고, 상호작용 버튼으로 읽기를 시작하세요")

def go_to_study():
    """학습 기능"""
    print("학습 모드: 위/아래로 읽기/쓰기를 선택하세요")

def go_to_question():
    """질문 기능 - 사용하지 않음 (temporary_function_call.py 사용)"""
    pass

def go_to_fairytale():
    """동화 기능"""
    from function.function_story import start_story_mode
    start_story_mode()

def handle_cancel_button():
    """취소 버튼 처리 - 모든 리소스 해제하고 메인 메뉴로 복귀"""
    global current_function_index, in_photo_mode, in_story_mode, in_question_mode, in_learning_mode, learning_sub_mode, in_writing_mode, in_reading_mode, reading_learning_instance, is_processing_function, last_interaction_time
    
    print("🚨 취소 버튼 실행 - 모든 기능 종료 중...")
    
    # 1. 진행 중인 처리 강제 중단
    is_processing_function = True
    
    # 1.5. 동화 재생 중단 신호 전송
    try:
        cancel_signal_file = "/tmp/cancel_story_signal.txt"
        with open(cancel_signal_file, 'w') as f:
            f.write("1")
        print("📢 동화 재생 중단 신호 전송")
    except:
        pass
    
    # 2. 메모리 정리 및 모든 모델 언로드
    cleanup_results = emergency_exit_to_main()
    
    # 3. 모든 모드 플래그 초기화
    in_photo_mode = False
    in_story_mode = False
    in_question_mode = False
    in_learning_mode = False
    learning_sub_mode = None
    in_writing_mode = False
    in_reading_mode = False
    reading_learning_instance = None
    
    # 4. 디바운싱 상태 초기화
    last_interaction_time = 0
    
    
    # 5. 네비게이션 시스템 초기화
    success, msg, state = nav_manager.go_back()
    
    # 6. 메인 메뉴 상태로 복귀
    current_function_index = 0  # 첫 번째 기능(사진)으로 리셋
    is_processing_function = False
    
    print("✅ 메인 메뉴로 복귀 완료")
    print(f"현재 선택된 기능: {functions[current_function_index]}")
    print("조이스틱으로 기능을 선택하고 상호작용 버튼으로 실행하세요")