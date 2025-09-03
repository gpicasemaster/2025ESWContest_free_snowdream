// 하드웨어 진단 테스트 코드
// 조이스틱과 버튼 상태를 실시간으로 출력

const int joystick_X = A6;
const int joystick_Y = A7;
const int button1 = A2;  // 상호작용 버튼
const int button2 = A1;  // 취소 버튼

void setup() {
  Serial.begin(9600);
  pinMode(button1, INPUT_PULLUP);
  pinMode(button2, INPUT_PULLUP);
  
  Serial.println("=== 하드웨어 진단 테스트 시작 ===");
  Serial.println("조이스틱과 버튼을 움직여보세요");
  Serial.println("X축, Y축, 버튼1, 버튼2 상태를 출력합니다");
  Serial.println("================================");
  
  delay(2000);
}

void loop() {
  // 아날로그 값 읽기
  int x_value = analogRead(joystick_X);
  int y_value = analogRead(joystick_Y);
  
  // 디지털 값 읽기
  int button1_state = digitalRead(button1);
  int button2_state = digitalRead(button2);
  
  // 모든 값 출력
  Serial.print("X:");
  Serial.print(x_value);
  Serial.print(" Y:");
  Serial.print(y_value);
  Serial.print(" BTN1:");
  Serial.print(button1_state == LOW ? "PRESSED" : "RELEASE");
  Serial.print(" BTN2:");
  Serial.println(button2_state == LOW ? "PRESSED" : "RELEASE");
  
  // 변화 감지 시 특별 메시지
  static int last_x = -1, last_y = -1;
  static int last_btn1 = HIGH, last_btn2 = HIGH;
  
  if (abs(x_value - last_x) > 50 || abs(y_value - last_y) > 50) {
    Serial.println(">>> 조이스틱 움직임 감지!");
    last_x = x_value;
    last_y = y_value;
  }
  
  if (button1_state != last_btn1) {
    Serial.println(button1_state == LOW ? ">>> 상호작용 버튼 눌림!" : ">>> 상호작용 버튼 해제!");
    last_btn1 = button1_state;
  }
  
  if (button2_state != last_btn2) {
    Serial.println(button2_state == LOW ? ">>> 취소 버튼 눌림!" : ">>> 취소 버튼 해제!");
    last_btn2 = button2_state;
  }
  
  delay(100);  // 0.1초마다 출력
}