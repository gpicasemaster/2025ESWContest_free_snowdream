시각장애인 아동의 문맹률 감소를 위한 저비용 다국어 학습기기 - 설몽


사용 디바이스 
Jetson orin nano 8gb super
Arduino Due
Arduino nano


### 사진 기능
- 카메라를 통한 실시간 이미지 촬영
- AI 기반 이미지 분석 및 음성 설명

### 학습 기능
- **읽기 모드**: 이미지/텍스트 인식 및 음성 변환
- **쓰기 모드**: 태블릿 펜으로 문자 그리기 → OCR 인식 → 음성 피드백

###  질문 기능
- 음성 질문 녹음 및 AI 기반 답변 생성
- 자연어 처리를 통한 대화형 학습

###  동화 기능
- 다양한 동화 컨텐츠 제공
- 음성으로 읽어주는 오디오북 기능

## 🛠 시스템 요구사항

### 하드웨어
- 아두이노 조이스틱 (상하좌우 + 상호작용 버튼)
- 태블릿 (펜 입력 지원)
- 마이크 (음성 녹음용)
- 스피커 (음성 출력용)

### 소프트웨어
- Python 3.8+
- Conda (miniforge3 권장)
- 필수 Python 환경:
  - `snowdream`: 메인 시스템 환경
  - `cnn_env`: OCR 처리 환경

##  설치 및 실행

### 1. 환경 설정
```bash
# 저장소 클론
git clone <repository-url>
cd hanium_snowdream

# Conda 환경 생성 (snowdream)
conda create -n snowdream python=3.8
conda activate snowdream
pip install pygame pillow evdev numpy

# Conda 환경 생성 (cnn_env)
conda create -n cnn_env python=3.8
conda activate cnn_env
pip install easyocr torch torchvision
```

### 2. 권한 설정
```bash
# 태블릿 디바이스 접근 권한 (sudo 필요)
sudo usermod -a -G input $USER
sudo chmod 666 /dev/input/event*
```

### 3. 실행
```bash
# 시스템 테스트
python run_system.py test

# 메인 시스템 실행
python run_system.py

# 또는 직접 실행
sudo python home.py
```

## 📁 프로젝트 구조

```
hanium_snowdream/
├── home.py                 # 메인 실행 파일
├── function_call.py        # 기능 라우팅 및 상태 관리
├── run_system.py          # 시스템 실행 스크립트
├── test_full_system.py    # 전체 시스템 테스트
├── connect_arduino.py     # 아두이노 통신
├── memory_manager.py      # 메모리 관리
├── navigation_system.py   # 네비게이션 시스템
├── function/              # 각 기능별 모듈
│   ├── writing_mode.py    # 쓰기 모드 (핵심)
│   ├── coordinate_to_image.py # 좌표→이미지 변환
│   ├── tablet_recorder.py # 태블릿 입력 처리  
│   ├── function_picture.py # 사진 기능
│   ├── function_story.py  # 동화 기능
│   ├── function_question.py # 질문 기능
│   ├── function_learning.py # 학습 기능
│   └── function_study/    # 학습 관련 유틸리티
│       ├── ocr_recognizer.py # OCR 엔진
│       └── coordinates.txt   # 태블릿 좌표 데이터
├── drawings/              # 생성된 이미지 저장
├── sound/                # 음성 파일
└── ocr_results.json      # OCR 결과 로그
```

##  사용 방법

### 조이스틱 조작법
- **위/아래**: 기능 순환 (사진 → 학습 → 질문 → 동화)
- **상호작용 버튼**: 선택된 기능 실행
- **취소 버튼**: 언제든지 메인 메뉴로 복귀

### 학습 모드 - 쓰기 기능 사용법
1. 조이스틱으로 "학습" 선택 → 상호작용 버튼
2. 위/아래로 "쓰기" 선택 → 상호작용 버튼  
3. 태블릿 펜으로 문자/그림 그리기
4. 상호작용 버튼으로 이미지 저장 및 OCR 실행
5. 인식 결과 음성 피드백

## 🔧 기술 스택

### AI/ML
- **EasyOCR**: 한글/영어 문자 인식
- **PIL (Pillow)**: 이미지 처리
- **OpenCV**: 실시간 이미지 분석

### 하드웨어 인터페이스
- **evdev**: 리눅스 입력 디바이스 처리
- **PySerial**: 아두이노 시리얼 통신
- **pygame**: 오디오 재생

### 시스템
- **subprocess**: 프로세스 간 통신
- **threading**: 비동기 처리
- **JSON**: 데이터 저장 및 로깅

##  문제 해결

### 권한 오류
```bash
# 태블릿 입력 디바이스 접근 불가
sudo chmod 666 /dev/input/event*

# 쓰기 모드 실행 권한
sudo python home.py
```

### 환경 오류
```bash
# Conda 환경 확인
conda info --envs

# 패키지 설치 확인
pip list | grep -E "(easyocr|pygame|pillow)"
```

### OCR 성능 개선
- 더 선명하고 큰 글자로 그리기
- 검정 펜으로 흰 배경에 그리기
- 한 글자씩 분리해서 그리기

## 성능 최적화

- 좌표 필터링 비활성화로 모든 입력 보존
- 선 두께를 3px로 조정하여 인식률 향상
- 0.5초 디바운싱으로 중복 입력 방지
- 메모리 관리로 시스템 안정성 확보

라이센스 
<본 프로젝트는 과학기술정보통신부의 지원을 받아 수행한 한이음 드림업 프로젝트의 결과물입니다.>


개발팀

Team snowdream(설몽)

팀장 박민규
팀원 이승현
팀원 이승주
팀원 김현수
팀원 김민석

---
