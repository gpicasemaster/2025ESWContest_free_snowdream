// Arduino Due - Complete Code with Joystick + Buttons
// Pins: A6(X), A7(Y), A2(Button1-상호작용), A1(Button2-취소)
const int joystick_X = A6;
const int joystick_Y = A7;
const int button1 = A2;  // 상호작용 버튼
const int button2 = A1;  // 취소 버튼

int prev_button1 = HIGH;
int prev_button2 = HIGH;
String prev_direction = "CENTER";

int center_X = 512;
int center_Y = 512;
const int deadzone = 400;

// 누적입력 방지 플래그 시스템
int flag = 0;

int readSerial() {
  if(Serial.available()) {
    if (Serial.read()) {
      flag = 0;  // 파이썬 완료 신호 받으면 플래그 리셋
    }
  }
}
  
void setup() {
  Serial.begin(9600);
  pinMode(button1, INPUT_PULLUP);
  pinMode(button2, INPUT_PULLUP);

  delay(3000);

  // 조용히 캘리브레이션
  center_X = analogRead(joystick_X);
  center_Y = analogRead(joystick_Y);
}

void loop() {
  int x_value = analogRead(joystick_X);
  int y_value = analogRead(joystick_Y);
  int button1_state = digitalRead(button1);
  int button2_state = digitalRead(button2);
  
  String direction = getJoystickDirection(x_value, y_value);
  
  // 파이썬 완료 신호 확인
  readSerial();
  
  // 조이스틱 처리 - 누적입력 방지 플래그 포함
  if (direction != prev_direction && direction != "CENTER" && flag == 0) {
    if (direction == "UP") {
      Serial.println("1");
    } 
    else if (direction == "DOWN") {
      Serial.println("2");
    } 
    else if (direction == "LEFT") {
      Serial.println("3");
    } 
    else if (direction == "RIGHT") {
      Serial.println("4");
    }
    prev_direction = direction;
    flag = 1;  // 플래그 설정 - 누적입력 방지
    delay(100);
  } 
  else if (direction == "CENTER") {
    prev_direction = direction;
  }

  // Button 1 처리 (상호작용 버튼)
  if (button1_state != prev_button1) {
    if (button1_state == LOW) {
      Serial.println("5");  // 상호작용 신호
    }
    prev_button1 = button1_state;
  }

  // Button 2 처리 (취소 버튼 - 나중에 구현)
  if (button2_state != prev_button2) {
    if (button2_state == LOW) {
      Serial.println("6");  // 취소 신호 (나중에 사용)
    }
    prev_button2 = button2_state;
  }

  delay(10);  // 안정적인 루프
}

String getJoystickDirection(int x, int y) {
  int x_diff = x - center_X;
  int y_diff = y - center_Y;

  if (abs(x_diff) < deadzone && abs(y_diff) < deadzone) {
    return "CENTER";
  }

  if (abs(x_diff) > abs(y_diff)) {
    if (x_diff > deadzone) {
      return "RIGHT";
    } else if (x_diff < -deadzone) {
      return "LEFT";
    }
  } else {
    if (y_diff > deadzone) {
      return "DOWN";
    } else if (y_diff < -deadzone) {
      return "UP";
    }
  }

  return "CENTER";
}