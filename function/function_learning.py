#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import pygame
from pathlib import Path

# TTS 설정 - route.py 사용
from function.route import generate_tts_audio, kill_tts_processes

# pygame 초기화
pygame.mixer.init()

class LearningFunction:
    def __init__(self):
        """학습 기능 클래스"""
        self.audio_dir = Path(__file__).parent / "audio_prompts"
        self.audio_dir.mkdir(exist_ok=True)
        
        # 오디오 파일 경로
        self.reading_select_wav = self.audio_dir / "reading_select.wav"
        self.reading_selected_wav = self.audio_dir / "reading_selected.wav"
        self.writing_select_wav = self.audio_dir / "writing_select.wav"
        self.writing_selected_wav = self.audio_dir / "writing_selected.wav"
        
        # 읽기 모드 새 오디오 파일들
        self.select_stage_wav = self.audio_dir / "select_stage.wav"
        self.stage1_selected_wav = self.audio_dir / "stage1_selected.wav"
        self.stage2_selected_wav = self.audio_dir / "stage2_selected.wav"
        self.stage3_selected_wav = self.audio_dir / "stage3_selected.wav"
        
        # TTS 대본
        self.reading_prompt = "읽기 기능을 선택하시겠습니까?"
        self.reading_selected_prompt = "읽기 기능을 선택하셨습니다"
        self.writing_prompt = "쓰기 기능을 선택하시겠습니까?"
        self.writing_selected_prompt = "쓰기 기능을 선택하셨습니다"
        
        # 읽기 모드 새 TTS 대본들
        self.select_stage_prompt = "단계를 골라주세요"
        self.stage1_selected_prompt = "1단계를 선택하셨습니다"
        self.stage2_selected_prompt = "2단계를 선택하셨습니다"
        self.stage3_selected_prompt = "3단계를 선택하셨습니다"
        
        # 읽기 파일 경로
        self.reading_file_path = Path(__file__).parent / "function_study" / "function_read.txt"
        
        # 읽기 모드 상태
        self.reading_stages = {}
        self.current_stage = 1
        self.current_word_index = 0
        self.in_stage_selection = False
        self.in_word_learning = False
    
    def ensure_audio_exists(self, text, audio_path):
        """오디오 파일이 존재하는지 확인하고 없으면 생성"""
        if not audio_path.exists():
            print(f"오디오 파일이 없습니다. TTS로 생성합니다: {audio_path}")
            return generate_tts_audio(text, audio_path)
        else:
            print(f"오디오 파일이 존재합니다: {audio_path}")
            return True
    
    def play_audio(self, audio_path):
        """오디오 파일 재생"""
        try:
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            
            # 재생이 끝날 때까지 대기
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            return True
        except Exception as e:
            print(f"WAV 재생 오류: {e}")
            return False
    
    def play_reading_prompt(self):
        """읽기 기능 선택 프롬프트 재생"""
        print("읽기 기능 선택 프롬프트 재생...")
        if self.ensure_audio_exists(self.reading_prompt, self.reading_select_wav):
            return self.play_audio(self.reading_select_wav)
        return False
    
    
    def play_reading_selected_prompt(self):
        """읽기 기능 선택 확인 메시지 재생"""
        print("읽기 기능 선택 확인 메시지 재생...")
        if self.ensure_audio_exists(self.reading_selected_prompt, self.reading_selected_wav):
            return self.play_audio(self.reading_selected_wav)
        return False
    
    
    def play_writing_prompt(self):
        """쓰기 기능 선택 프롬프트 재생"""
        print("쓰기 기능 선택 프롬프트 재생...")
        if self.ensure_audio_exists(self.writing_prompt, self.writing_select_wav):
            return self.play_audio(self.writing_select_wav)
        return False
    
    def play_writing_selected_prompt(self):
        """쓰기 기능 선택 확인 메시지 재생"""
        print("쓰기 기능 선택 확인 메시지 재생...")
        if self.ensure_audio_exists(self.writing_selected_prompt, self.writing_selected_wav):
            return self.play_audio(self.writing_selected_wav)
        return False
    
    def parse_reading_file(self):
        """function_read.txt 파일을 파싱하여 단계별 단어 딕셔너리 생성"""
        stages = {}
        
        try:
            with open(self.reading_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            current_stage = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('===') and line.endswith('==='):
                    # 단계 헤더 파싱 (예: ===1단계===)
                    stage_text = line.replace('===', '')
                    if '1단계' in stage_text:
                        current_stage = 1
                    elif '2단계' in stage_text:
                        current_stage = 2
                    elif '3단계' in stage_text:
                        current_stage = 3
                    
                    if current_stage:
                        stages[current_stage] = []
                        
                elif line and current_stage and line[0].isdigit():
                    # 번호가 있는 단어 라인 파싱 (예: 1. 강)
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        word = parts[1].strip()
                        stages[current_stage].append(word)
            
            print(f"파싱 결과: {stages}")
            return stages
            
        except Exception as e:
            print(f"읽기 파일 파싱 오류: {e}")
            return {}
    
    def start_reading_mode(self):
        """읽기 모드 시작"""
        print("=== 📖 읽기 모드 시작 ===")
        
        # 파일 파싱
        self.reading_stages = self.parse_reading_file()
        if not self.reading_stages:
            print("❌ 읽기 파일을 불러올 수 없습니다.")
            return
        
        # 단계 선택 모드 진입
        self.in_stage_selection = True
        self.current_stage = 1
        
        # "단계를 골라주세요" 음성 재생
        print("🔊 단계를 골라주세요")
        if self.ensure_audio_exists(self.select_stage_prompt, self.select_stage_wav):
            self.play_audio(self.select_stage_wav)
        
        print(f"현재 선택: {self.current_stage}단계")
        print("조이스틱으로 단계를 선택하고 상호작용 버튼으로 확정하세요")
    
    def handle_stage_selection(self, direction):
        """단계 선택 처리 (조이스틱 위/아래)"""
        if not self.in_stage_selection:
            return
            
        if direction == 'up':
            self.current_stage = max(1, self.current_stage - 1)
        elif direction == 'down':
            self.current_stage = min(3, self.current_stage + 1)
        
        print(f"현재 선택: {self.current_stage}단계")
        
        # 단계별 음성 안내는 일단 생략 (너무 많은 TTS 생성 방지)
    
    def confirm_stage_selection(self):
        """단계 선택 확정 (상호작용 버튼)"""
        if not self.in_stage_selection:
            return
            
        print(f"✅ {self.current_stage}단계를 선택하셨습니다")
        
        # 선택 확정 음성 재생
        stage_prompts = {
            1: (self.stage1_selected_prompt, self.stage1_selected_wav),
            2: (self.stage2_selected_prompt, self.stage2_selected_wav),
            3: (self.stage3_selected_prompt, self.stage3_selected_wav)
        }
        
        prompt_text, prompt_wav = stage_prompts[self.current_stage]
        if self.ensure_audio_exists(prompt_text, prompt_wav):
            self.play_audio(prompt_wav)
        
        # 단어 학습 모드로 전환
        self.in_stage_selection = False
        self.in_word_learning = True
        self.current_word_index = 0
        
        self.start_word_learning()
    
    def start_word_learning(self):
        """선택된 단계의 단어 학습 시작"""
        stage_words = self.reading_stages.get(self.current_stage, [])
        if not stage_words:
            print(f"❌ {self.current_stage}단계에 학습할 단어가 없습니다.")
            return
        
        if self.current_word_index >= len(stage_words):
            print(f"✅ {self.current_stage}단계 학습 완료!")
            self.finish_reading_mode()
            return
        
        current_word = stage_words[self.current_word_index]
        print(f"📚 {self.current_word_index + 1}번째 단어: {current_word}")
        
        # TTS로 단어 읽기
        self.speak_and_braille_word(current_word)
    
    def speak_and_braille_word(self, word):
        """점자를 먼저 출력하고 TTS로 읽기"""
        print(f"📟 단어 점자 + 음성 출력: {word}")
        
        # 1️⃣ 점자 출력 먼저
        self.output_braille(word)
        
        # 2️⃣ 그 다음 TTS 음성 파일 생성 및 재생
        word_audio_path = self.audio_dir / f"word_{word}.wav"
        if self.ensure_audio_exists(word, word_audio_path):
            self.play_audio(word_audio_path)
        
        print("상호작용 버튼을 눌러서 다음 단어로 이동하세요")
    
    def output_braille(self, word):
        """BrailleTranslator를 사용하여 점자 출력"""
        try:
            # 현재 프로젝트의 BrailleTranslator 임포트
            sys.path.append('/home/drboom/py_project/hanium_snowdream')
            from braille.braille_translator import BrailleTranslator
            
            translator = BrailleTranslator()
            
            # 현재 상태 로드 (로그 파일에서 읽기 시도)
            current_state = ['11', '22', '33', '44', '55', '66', '77', '88', '11', '22']
            try:
                with open(translator.log_file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        loaded_state = content.split()
                        if len(loaded_state) >= 10:
                            current_state = loaded_state[:10]
                        else:
                            current_state = loaded_state + ['88'] * (10 - len(loaded_state))
            except FileNotFoundError:
                pass
            
            # 단어를 점자로 변환
            braille = translator.translate_text(word)
            target_state = translator.convert_braille_to_number(braille)
            
            # 10개 미만이면 '88'로 채우기
            if len(target_state) < 10:
                padding_needed = 10 - len(target_state)
                target_state.extend(['88'] * padding_needed)
            
            # 상태 전환 계산 및 아두이노 전송
            transitions = translator.calculate_state_transition(current_state, target_state)
            print(f"📟 점자 출력: {word} → {' '.join(target_state)}")
            print(f"🔄 상태 전환: {transitions}")
            
            # 로그 파일에 상태 저장
            translator.log_to_file(translator.log_file_path, ' '.join(target_state))
            translator.log_to_file(translator.change_log_path, transitions)
            
            # 아두이노에 모터 제어 명령 전송
            translator.send_motor_commands(transitions)
            
        except Exception as e:
            print(f"❌ 점자 출력 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def next_word(self):
        """다음 단어로 이동 (상호작용 버튼)"""
        if not self.in_word_learning:
            return
            
        self.current_word_index += 1
        self.start_word_learning()
    
    def finish_reading_mode(self):
        """읽기 모드 종료"""
        print("🎉 읽기 학습이 완료되었습니다!")
        self.in_stage_selection = False
        self.in_word_learning = False
        self.current_stage = 1
        self.current_word_index = 0
    
    def start_writing_mode(self):
        """쓰기 모드 시작"""
        print("=== 📝 쓰기 모드 시작 ===")
        
        try:
            # subprocess로 sudo 권한으로 실행
            print("🔑 sudo 권한으로 쓰기 모드 실행 중...")
            
            # 작업 디렉토리를 function 폴더로 설정
            working_dir = '/home/drboom/py_project/hanium_snowdream/function'
            
            cmd = [
                'sudo',
                '/home/drboom/miniforge3/envs/snowdream/bin/python',
                'writing_mode.py'
            ]
            
            # 백그라운드로 실행
            self.writing_process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("✅ 쓰기 모드 프로세스 시작!")
            print("📝 태블릿에 펜으로 그려보세요")
            print("🔘 상호작용 버튼을 누르면 이미지가 저장됩니다")
            
            return self.writing_process
            
        except Exception as e:
            print(f"❌ 쓰기 모드 오류: {e}")
            return None
        
    
    
    
    
    def test_audio_generation(self):
        """오디오 생성 테스트"""
        print("=== 오디오 생성 테스트 ===")
        
        # 읽기 프롬프트 테스트
        print("1. 읽기 프롬프트 생성 테스트")
        self.play_reading_prompt()
        time.sleep(2)
        
        # 쓰기 프롬프트 테스트
        print("2. 쓰기 프롬프트 생성 테스트")
        self.play_writing_prompt()
        
        print("테스트 완료!")

def main():
    """메인 함수"""
    learning = LearningFunction()
    
    # 테스트 모드
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        learning.test_audio_generation()
    else:
        learning.start_learning_menu()

if __name__ == "__main__":
    main() 