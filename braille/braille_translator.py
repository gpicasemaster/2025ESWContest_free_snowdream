#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import serial
import time
import glob

class BrailleTranslator:
    def __init__(self):
        # 로그 파일 경로를 현재 프로젝트로 변경
        self.log_file_path = '/home/drboom/py_project/hanium_snowdream/braille_log/log.txt'
        self.change_log_path = '/home/drboom/py_project/hanium_snowdream/braille_log/braille_log_change.txt'

        # 시리얼 통신 설정 - 동적 검색 방식 사용
        self.serial_port = None
        self.init_serial_connection()

        # 상태이동의 기준이 되는 전체 순서
        self.sequence = [
            '44', '22', '66', '11', '55', '33', '77', '88', '49',
            '24', '62', '16', '51', '35', '73', '87', '48', '29',
            '64', '12', '56', '31', '75', '83', '47', '28', '69',
            '14', '52', '36', '71', '85', '43', '27', '68', '19',
            '54', '32', '76', '81', '45', '23', '67', '18', '59',
            '34', '72', '86', '41', '25', '63', '17', '58', '39',
            '74', '82', '46', '21', '65', '13', '57', '38', '79',
            '84', '42', '26', '61', '15', '53', '37', '78', '89'
        ]

        # 점자 -> 숫자 매핑 규칙
        self.braille_char_to_number_map = {
            '⠤': '11', '⠒': '22', '⠶': '33', '⠉': '44', '⠭': '55', '⠛': '66', '⠿': '77', '⠀ ': '88', '⠄': '19',
            '⠢': '21', '⠖': '32', '⠱': '43', '⠍': '54', '⠫': '65', '⠟': '76', '⠸': '87', '⠄': '18', '⠂': '29',
            '⠦': '31', '⠑': '42', '⠵': '53', '⠋': '64', '⠯': '75', '⠘': '86', '⠼': '17', '⠂': '28', '⠆': '39',
            '⠡': '41', '⠕': '52', '⠳': '63', '⠏': '74', '⠨': '85', '⠜': '16', '⠺': '27', '⠆': '38', '⠁': '49',
            '⠥': '51', '⠓': '62', '⠷': '73', '⠈': '84', '⠬': '15', '⠚': '26', '⠾': '37', '⠁': '48', '⠅': '59',
            '⠣': '61', '⠗': '72', '⠰': '83', '⠌': '14', '⠪': '25', '⠞': '36', '⠹': '47', '⠅': '58', '⠃': '69',
            '⠧': '71', '⠐': '82', '⠴': '13', '⠊': '24', '⠮': '35', '⠙': '46', '⠽': '57', '⠃': '68', '⠇': '79',
            '⠠': '81', '⠔': '12', '⠲': '23', '⠎': '34', '⠩': '45', '⠝': '56', '⠻': '67', '⠇': '78', '⠀ ': '89'
        }
        
        # 영어, 한글 점자 정의
        self.english_braille = { 'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑', 'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚', 'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕', 'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞', 'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵', ' ': '⠀', '.': '⠲', ',': '⠂', '?': '⠦', '!': '⠖', '-': '⠤',}
        self.CAPITAL_SIGN = '⠠'
        self.NUMBER_SIGN = '⠼'
        self.korean_chosung = { 'ㄱ': '⠁', 'ㄴ': '⠉', 'ㄷ': '⠙', 'ㄹ': '⠑', 'ㅁ': '⠍', 'ㅂ': '⠃', 'ㅅ': '⠛', 'ㅇ': '', 'ㅈ': '⠚', 'ㅊ': '⠚⠓', 'ㅋ': '⠅', 'ㅌ': '⠞', 'ㅍ': '⠏', 'ㅎ': '⠓', 'ㄲ': '⠈⠁', 'ㄸ': '⠈⠙', 'ㅃ': '⠈⠃', 'ㅆ': '⠈⠛', 'ㅉ': '⠈⠚'}
        self.korean_jungsung = {'ㅏ': '⠣', 'ㅑ': '⠜', 'ㅓ': '⠡', 'ㅕ': '⠳', 'ㅗ': '⠥', 'ㅛ': '⠬', 'ㅜ': '⠍', 'ㅠ': '⠩', 'ㅡ': '⠪', 'ㅣ': '⠕', 'ㅐ': '⠗', 'ㅔ': '⠝', 'ㅒ': '⠜⠗', 'ㅖ': '⠳⠗', 'ㅘ': '⠣⠗', 'ㅙ': '⠣⠗', 'ㅚ': '⠥⠗', 'ㅝ': '⠍⠗', 'ㅞ': '⠍⠗', 'ㅟ': '⠍⠗', 'ㅢ': '⠪⠗'}
        self.korean_jongsung = {'ㄱ': '⠁', 'ㄴ': '⠉', 'ㄷ': '⠊', 'ㄹ': '⠐', 'ㅁ': '⠑', 'ㅂ': '⠃', 'ㅅ': '⠆', 'ㅇ': 'circ', 'ㅈ': '⠚', 'ㅊ': '⠚⠓', 'ㅋ': '⠅', 'ㅌ': '⠞', 'ㅍ': '⠏', 'ㅎ': '⠓', 'ㄲ': '⠁⠁', 'ㄳ': '⠁⠆', 'ㄵ': '⠉⠚', 'ㄶ': '⠉⠓', 'ㄺ': '⠐⠁', 'ㄻ': '⠐⠑', 'ㄼ': '⠐⠃', 'ㄽ': '⠐⠆', 'ㄾ': '⠐⠞', 'ㄿ': '⠐⠏', 'ㅀ': '⠐⠓', 'ㅄ': '⠃⠆', 'ㅆ': '⠌'}

    def find_braille_arduino_port(self):
        """점자 모터 아두이노 포트를 찾습니다"""
        ports = []
        for pattern in ['/dev/ttyACM*', '/dev/ttyUSB*']:
            ports.extend(glob.glob(pattern))
        
        # ACM0을 점자 모터로 우선 시도
        braille_candidates = [p for p in ports if "ACM0" in p]
        if not braille_candidates:
            braille_candidates = ports
        
        for port in braille_candidates:
            try:
                ser = serial.Serial(port, 9600, timeout=2)
                time.sleep(1)
                print(f"✅ 점자 모터 연결: {port}")
                return ser
            except Exception as e:
                print(f"❌ {port} 연결 실패: {e}")
                continue
        
        return None

    def init_serial_connection(self):
        """시리얼 연결 초기화 - 동적 검색 방식 사용"""
        try:
            self.serial_port = self.find_braille_arduino_port()
            
            if self.serial_port:
                time.sleep(2)  # Arduino 리셋 대기
                
                # 버퍼 비우기
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                
                # 아두이노 깨우기 (더미 명령)
                self.serial_port.write(b'\n')
                time.sleep(0.5)
                self.serial_port.reset_input_buffer()
                
                print("✅ 점자 모터 Arduino 연결 성공!")
            else:
                print("❌ 점자 모터 Arduino 연결 실패")
                print("USB 포트를 확인하거나 Arduino를 연결해주세요.")
                
        except Exception as e:
            print(f"Arduino 연결 실패: {e}")
            self.serial_port = None

    def decompose_hangul(self, char):
        if not ('가' <= char <= '힣'): return None, None, None
        code = ord(char) - ord('가')
        chosung_idx, rem = divmod(code, 21 * 28)
        jungsung_idx, jongsung_idx = divmod(rem, 28)
        chosung_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        jungsung_list = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
        jongsung_list = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        return chosung_list[chosung_idx], jungsung_list[jungsung_idx], jongsung_list[jongsung_idx] if jongsung_idx > 0 else None

    def translate_text(self, text):
        result = ""
        is_number_mode = False
        for char in text:
            if '가' <= char <= '힣':
                is_number_mode = False
                cho, jung, jong = self.decompose_hangul(char)
                result += self.korean_chosung.get(cho, '')
                result += self.korean_jungsung.get(jung, '')
                if jong: result += self.korean_jongsung.get(jong, '')
            elif 'a' <= char.lower() <= 'z':
                is_number_mode = False
                if char.isupper(): result += self.CAPITAL_SIGN
                result += self.english_braille.get(char.lower(), '')
            elif char.isdigit():
                if not is_number_mode:
                    result += self.NUMBER_SIGN
                    is_number_mode = True
                num_map = str.maketrans('1234567890', 'abcdefghij')
                braille_char = char.translate(num_map)
                result += self.english_braille.get(braille_char, '')
            else:
                is_number_mode = False
                result += self.english_braille.get(char, '')
        return result

    def convert_braille_to_number(self, braille_text):
        numbers = []
        for char in braille_text:
            # NUMBER_SIGN과 CAPITAL_SIGN은 제어 문자이므로 제외
            if char in [self.NUMBER_SIGN, self.CAPITAL_SIGN]:
                continue
            number = self.braille_char_to_number_map.get(char)
            if number: numbers.append(number)
        return numbers[:10]

    def calculate_state_transition(self, current_state, target_state):
        transitions = []
        sequence_map = {num: i for i, num in enumerate(self.sequence)}
        sequence_length = len(self.sequence)
        for i in range(min(len(current_state), len(target_state))):
            current_num = current_state[i]
            target_num = target_state[i]
            try:
                current_idx = sequence_map[current_num]
                target_idx = sequence_map[target_num]
                direct_dist = target_idx - current_idx
                if direct_dist > 0:
                    wrap_dist = direct_dist - sequence_length
                else:
                    wrap_dist = direct_dist + sequence_length
                if abs(direct_dist) <= abs(wrap_dist):
                    transitions.append(str(direct_dist))
                else:
                    transitions.append(str(wrap_dist))
            except KeyError:
                transitions.append('?')
        return " ".join(transitions)

    def send_motor_commands(self, transitions):
        """아두이노에 모터 제어 명령을 전송"""
        print(f"[DEBUG] send_motor_commands 시작")
        print(f"[DEBUG] transitions 입력값: '{transitions}'")
        
        if not self.serial_port or not self.serial_port.is_open:
            print("[ERROR] Arduino가 연결되지 않았습니다.")
            return
        
        print(f"[DEBUG] 시리얼 포트 상태: {self.serial_port.is_open}")
        
        try:
            # 전환값을 공백으로 분리
            values = transitions.split()
            print(f"[DEBUG] 파싱된 values: {values}")
            print(f"[DEBUG] values 개수: {len(values)}")
            
            # 10개 모터에 대한 명령 생성
            commands = []
            for i in range(min(10, len(values))):
                try:
                    value = int(values[i])
                    # 1 = 1/8바퀴 = 256 스텝
                    steps = abs(value) * 256
                    direction = 1 if value >= 0 else 0
                    command = f"M{i+1}:{steps}:{direction}"
                    commands.append(command)
                    print(f"[DEBUG] 모터{i+1}: value={value}, steps={steps}, direction={direction}")
                except ValueError:
                    print(f"[ERROR] 잘못된 값: {values[i]}")
            
            print(f"[DEBUG] 생성된 commands: {commands}")
            
            # 명령들을 하나의 문자열로 결합
            full_command = " ".join(commands) + "\n"
            print(f"[DEBUG] 최종 명령: '{full_command.strip()}'")
            print(f"[DEBUG] 명령 길이: {len(full_command)} bytes")
            
            # 아두이노에 전송
            print(f"[DEBUG] 아두이노에 전송 시작...")
            bytes_sent = self.serial_port.write(full_command.encode())
            print(f"[DEBUG] 전송된 바이트: {bytes_sent}")
            self.serial_port.flush()  # 버퍼 비우기
            print(f"[DEBUG] 전송 완료, 응답 대기 중...")
            
            # 아두이노로부터 응답 대기 (타임아웃 15초로 증가 - 모터 동작 시간 고려)
            self.serial_port.timeout = 15
            response = self.serial_port.readline().decode().strip()
            print(f"[DEBUG] 원시 응답: '{response}'")
            
            if response:
                print(f"[SUCCESS] 아두이노 응답: {response}")
            else:
                print(f"[WARNING] 아두이노로부터 응답이 없습니다")
                
            # 아두이노가 처리할 시간 주기
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[ERROR] 모터 제어 중 오류: {e}")
            import traceback
            traceback.print_exc()

    def log_to_file(self, file_path, text_to_log):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_to_log)
        except Exception as e:
            print(f"'{file_path}' 파일 작성 중 오류 발생: {e}")

    def close_connection(self):
        """시리얼 연결 종료"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("점자 모터 연결 종료")