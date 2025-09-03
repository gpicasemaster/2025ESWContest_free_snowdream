#!/usr/bin/env python3
"""
Tree 네비게이션 시스템
- 메뉴 상태 관리
- 뒤로가기 스택
- 취소 버튼 처리
"""

from enum import Enum
from typing import Optional, List
import time

class NavigationState(Enum):
    """네비게이션 상태 정의"""
    MAIN_MENU = "main_menu"           # 메인 메뉴 (사진, 학습, 질문, 동화)
    PHOTO_MODE = "photo_mode"         # 사진 모드
    LEARNING_SELECT = "learning_select" # 학습 모드 - 읽기/쓰기 선택
    LEARNING_ACTIVE = "learning_active" # 학습 진행 중
    QUESTION_MODE = "question_mode"    # 질문 모드
    STORY_SELECT = "story_select"     # 동화 선택 모드
    STORY_READING = "story_reading"   # 동화 읽기 중

class NavigationManager:
    def __init__(self):
        """네비게이션 관리자 초기화"""
        self.current_state = NavigationState.MAIN_MENU
        self.history_stack = []  # 뒤로가기 스택
        self.main_menu_index = 0  # 메인 메뉴 선택 인덱스
        self.main_menu_items = ["사진", "학습", "질문", "동화"]
        
        # 각 모드별 상태 변수들
        self.learning_sub_mode = None  # 'reading' 또는 'writing'
        self.story_index = 0
        self.is_processing = False
        
        # 마지막 상호작용 시간 (중복 입력 방지)
        self.last_interaction_time = 0
        self.interaction_cooldown = 0.5  # 0.5초 쿨다운
        
    def can_interact(self) -> bool:
        """상호작용 가능한지 확인 (쿨다운 체크)"""
        current_time = time.time()
        if current_time - self.last_interaction_time >= self.interaction_cooldown:
            self.last_interaction_time = current_time
            return True
        return False
    
    def get_current_menu_item(self) -> str:
        """현재 선택된 메뉴 아이템 반환"""
        if self.current_state == NavigationState.MAIN_MENU:
            return self.main_menu_items[self.main_menu_index]
        return "알 수 없음"
    
    def navigate_main_menu(self, direction: str) -> tuple[bool, str]:
        """메인 메뉴 네비게이션"""
        if self.current_state != NavigationState.MAIN_MENU:
            return False, "메인 메뉴가 아님"
        
        if not self.can_interact():
            return False, "쿨다운 중"
            
        if direction == "up" or direction == "1":
            self.main_menu_index = (self.main_menu_index - 1) % len(self.main_menu_items)
            return True, f"이전 기능: {self.get_current_menu_item()}"
        elif direction == "down" or direction == "2":
            self.main_menu_index = (self.main_menu_index + 1) % len(self.main_menu_items)
            return True, f"다음 기능: {self.get_current_menu_item()}"
        
        return False, "잘못된 방향"
    
    def enter_selected_function(self) -> tuple[bool, str, Optional[str]]:
        """선택된 기능으로 진입"""
        if self.current_state != NavigationState.MAIN_MENU:
            return False, "메인 메뉴가 아님", None
            
        if not self.can_interact():
            return False, "쿨다운 중", None
        
        selected_function = self.get_current_menu_item()
        previous_state = self.current_state
        
        if selected_function == "사진":
            self.current_state = NavigationState.PHOTO_MODE
            self.history_stack.append(previous_state)
            return True, "사진 모드 진입", "photo"
            
        elif selected_function == "학습":
            self.current_state = NavigationState.LEARNING_SELECT
            self.learning_sub_mode = None
            self.history_stack.append(previous_state)
            return True, "학습 모드 진입 - 읽기/쓰기 선택", "learning"
            
        elif selected_function == "질문":
            self.current_state = NavigationState.QUESTION_MODE
            self.history_stack.append(previous_state)
            return True, "질문 모드 진입", "question"
            
        elif selected_function == "동화":
            self.current_state = NavigationState.STORY_SELECT
            self.history_stack.append(previous_state)
            return True, "동화 모드 진입", "story"
        
        return False, "알 수 없는 기능", None
    
    def handle_learning_navigation(self, direction: str) -> tuple[bool, str]:
        """학습 모드 내부 네비게이션"""
        if self.current_state != NavigationState.LEARNING_SELECT:
            return False, "학습 선택 모드가 아님"
            
        if not self.can_interact():
            return False, "쿨다운 중"
        
        if direction in ["up", "down", "1", "2"]:
            if self.learning_sub_mode == "reading":
                self.learning_sub_mode = "writing"
                return True, "쓰기 기능 선택"
            elif self.learning_sub_mode == "writing":
                self.learning_sub_mode = "reading"
                return True, "읽기 기능 선택"
            else:
                # 처음 선택
                self.learning_sub_mode = "reading"
                return True, "읽기 기능 선택"
        
        return False, "잘못된 입력"
    
    def execute_learning_function(self) -> tuple[bool, str, Optional[str]]:
        """학습 기능 실행"""
        if self.current_state != NavigationState.LEARNING_SELECT or not self.learning_sub_mode:
            return False, "학습 기능이 선택되지 않음", None
            
        if not self.can_interact():
            return False, "쿨다운 중", None
        
        self.current_state = NavigationState.LEARNING_ACTIVE
        return True, f"{self.learning_sub_mode} 실행", self.learning_sub_mode
    
    def handle_story_navigation(self, direction: str) -> tuple[bool, str]:
        """동화 선택 네비게이션"""
        if self.current_state != NavigationState.STORY_SELECT:
            return False, "동화 선택 모드가 아님"
            
        if not self.can_interact():
            return False, "쿨다운 중"
        
        if direction == "up" or direction == "1":
            return True, "이전 동화"
        elif direction == "down" or direction == "2":
            return True, "다음 동화"
        
        return False, "잘못된 방향"
    
    def start_story_reading(self) -> tuple[bool, str]:
        """동화 읽기 시작"""
        if self.current_state != NavigationState.STORY_SELECT:
            return False, "동화 선택 모드가 아님"
            
        if not self.can_interact():
            return False, "쿨다운 중"
        
        self.current_state = NavigationState.STORY_READING
        return True, "동화 읽기 시작"
    
    def go_back(self) -> tuple[bool, str, Optional[str]]:
        """뒤로가기 (취소 버튼)"""
        if not self.can_interact():
            return False, "쿨다운 중", None
        
        # 항상 메인 메뉴로 돌아가기
        previous_state = self.current_state
        self.current_state = NavigationState.MAIN_MENU
        self.history_stack.clear()
        
        # 모드별 상태 초기화
        self.learning_sub_mode = None
        self.story_index = 0
        self.is_processing = False
        
        return True, f"{previous_state.value}에서 메인 메뉴로 복귀", "main_menu"
    
    def complete_function(self) -> tuple[bool, str]:
        """기능 완료 시 메인 메뉴로 복귀"""
        previous_state = self.current_state
        self.current_state = NavigationState.MAIN_MENU
        self.history_stack.clear()
        
        # 상태 초기화
        self.learning_sub_mode = None
        self.story_index = 0
        self.is_processing = False
        
        return True, f"{previous_state.value} 완료 - 메인 메뉴로 복귀"
    
    def get_status_info(self) -> dict:
        """현재 네비게이션 상태 정보"""
        return {
            'current_state': self.current_state.value,
            'main_menu_item': self.get_current_menu_item(),
            'learning_sub_mode': self.learning_sub_mode,
            'story_index': self.story_index,
            'is_processing': self.is_processing,
            'history_depth': len(self.history_stack),
            'can_go_back': len(self.history_stack) > 0 or self.current_state != NavigationState.MAIN_MENU
        }

# 전역 네비게이션 관리자
nav_manager = NavigationManager()

# 편의 함수들
def get_current_state():
    """현재 네비게이션 상태 반환"""
    return nav_manager.current_state

def is_main_menu():
    """메인 메뉴 상태인지 확인"""
    return nav_manager.current_state == NavigationState.MAIN_MENU

def emergency_return_to_main():
    """비상시 메인 메뉴로 복귀"""
    return nav_manager.go_back()

if __name__ == "__main__":
    # 테스트
    print("네비게이션 시스템 테스트")
    print(f"현재 상태: {nav_manager.get_status_info()}")
    
    # 메뉴 이동 테스트
    success, msg = nav_manager.navigate_main_menu("down")
    print(f"메뉴 이동: {success}, {msg}")
    
    # 기능 진입 테스트
    success, msg, func = nav_manager.enter_selected_function()
    print(f"기능 진입: {success}, {msg}, {func}")
    
    # 뒤로가기 테스트
    success, msg, state = nav_manager.go_back()
    print(f"뒤로가기: {success}, {msg}, {state}")