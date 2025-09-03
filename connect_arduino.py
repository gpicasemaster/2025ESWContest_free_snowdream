import serial
import time
import glob
import os

BAUD_RATE = 9600

def find_available_ports():
    """사용 가능한 시리얼 포트를 찾습니다."""
    ports = []
    for pattern in ['/dev/ttyACM*', '/dev/ttyUSB*']:
        ports.extend(glob.glob(pattern))
    return sorted(ports)

def identify_arduino(port):
    """포트에 연결된 아두이노의 타입을 식별합니다."""
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
        time.sleep(2)  # 아두이노 부팅 대기 (조금 더 길게)
        
        # 시리얼 버퍼 클리어
        ser.flushInput()
        ser.flushOutput()
        
        # 4초 동안 메시지 확인 (아두이노 delay(3000) 고려)
        start_time = time.time()
        while time.time() - start_time < 4:
            if ser.in_waiting > 0:
                try:
                    raw_data = ser.readline()
                    message = raw_data.decode('utf-8', errors='ignore').strip()
                    if message:  # 빈 메시지 제외
                        print(f"[DEBUG] {port}: '{message}'")
                        if "BRAILLE_MOTOR_READY" in message:
                            ser.close()
                            return "braille"
                        elif "JOYSTICK_READY" in message:  # 수정: Arduino Ready → JOYSTICK_READY
                            ser.close()
                            return "joystick"
                except UnicodeDecodeError as e:
                    print(f"[DEBUG] {port}: 디코딩 오류 무시 - {e}")
                    continue
                except Exception as e:
                    print(f"[DEBUG] {port}: 읽기 오류 - {e}")
                    continue
            time.sleep(0.1)
        
        # 메시지가 없으면 기본값으로 추정
        print(f"[DEBUG] {port}: 메시지 없음, 포트명으로 추정")
        if "ACM0" in port:
            ser.close()
            return "joystick"  # 추정: 조이스틱
        elif "ACM1" in port:
            ser.close()
            return "braille"   # 추정: 점자 모터
        
        ser.close()
        return "unknown"
    except Exception as e:
        print(f"[DEBUG] {port}: 연결 실패 - {e}")
        return None

def test_arduino_type(port):
    """아두이노 포트에 빠른 테스트 신호를 보내서 타입을 확인합니다."""
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.5)
        time.sleep(0.1)
        
        # 간단한 테스트 신호 전송
        ser.write(b'1')
        time.sleep(0.1)
        
        response_found = False
        if ser.in_waiting > 0:
            try:
                response = ser.readline().decode('utf-8').strip()
                response_found = True
                ser.close()
                
                # 점자 모터는 "OK" 응답, 조이스틱은 숫자나 다른 응답
                if "OK" in response.upper():
                    return "BRAILLE"
                else:
                    return "JOYSTICK"
            except:
                pass
        
        ser.close()
        
        # 응답이 없으면 포트명으로 추정
        if "ACM0" in port:
            return "JOYSTICK_ASSUMED"
        elif "ACM1" in port:
            return "BRAILLE_ASSUMED"
        
        return "UNKNOWN"
    except:
        return None

def find_joystick_arduino():
    """메시지 기반으로 조이스틱 아두이노를 찾아서 연결합니다."""
    print("🔍 아두이노 연결 중...")
    
    ports = find_available_ports()
    if not ports:
        print("❌ 사용 가능한 시리얼 포트가 없습니다.")
        return None
    
    print(f"📋 발견된 포트: {ports}")
    
    joystick_port = None
    braille_port = None
    
    # 각 포트에서 메시지 기반 식별
    for port in ports:
        arduino_type = identify_arduino(port)
        if arduino_type == "joystick":
            joystick_port = port
        elif arduino_type == "braille":
            braille_port = port
    
    if joystick_port and braille_port:
        print(f"✅ 조이스틱: {joystick_port}, 점자모터: {braille_port} (메시지 확인됨)")
    elif joystick_port:
        print(f"✅ 조이스틱: {joystick_port} (확인됨), 점자모터: 미연결")
    else:
        print("❌ 조이스틱 아두이노를 찾을 수 없습니다.")
        return None
    
    try:
        ser = serial.Serial(joystick_port, BAUD_RATE, timeout=2)
        return ser
    except Exception as e:
        print(f"❌ 조이스틱 연결 실패: {e}")
        return None

def initialize_connection():
    """
    조이스틱 아두이노를 자동으로 찾아서 연결합니다.
    """
    ser = find_joystick_arduino()
    if ser:
        # 연결 즉시 플래그 리셋 신호 전송 (아두이노 flag=0으로 만들기)
        print("🔧 아두이노 플래그 리셋 중...")
        for i in range(5):  # 5번 시도
            ser.write(b'1')
            time.sleep(0.1)
        print("✅ 플래그 리셋 완료")
    return ser

def read_signal(ser):
    """
    연결된 시리얼 객체로부터 신호를 읽어 반환합니다.
    신호가 있을 때만 읽고 반환합니다.
    """
    if ser and ser.is_open:
        try:
            # 데이터가 있을 때만 읽기
            if ser.in_waiting > 0:
                raw_data = ser.readline()
                signal = raw_data.decode('utf-8', errors='ignore').strip()
                if signal:
                    # 실제 조이스틱 신호만 처리
                    if signal in ['1', '2', '3', '4', '5', '6']:
                        print(f"🕹️ 조이스틱 신호: '{signal}'")
                        return signal
                    else:
                        # 디버그 메시지 무시
                        return None
        except Exception as e:
            print(f"[DEBUG] 읽기 오류: {e}")
    return None

def send_signal(ser):
    """
    아두이노로 완료 신호를 전송하여 플래그를 리셋합니다.
    """
    if ser and ser.is_open:
        try:
            ser.write(b'1')  # 임의의 신호 전송 (아두이노에서 flag=0으로 리셋)
        except Exception as e:
            print(f"[DEBUG] 전송 오류: {e}")

def close_connection(ser):
    """
    시리얼 연결을 안전하게 종료합니다.
    """
    if ser and ser.is_open:
        ser.close()