#!/usr/bin/env python3
"""
통합 메모리 관리 시스템
- 모든 AI 모델의 로드/언로드 관리
- GPU 메모리 정리
- 프로세스 종료
"""

import subprocess
import os
import gc
import psutil
import signal

class MemoryManager:
    def __init__(self):
        """메모리 관리자 초기화"""
        self.loaded_models = {
            'whisper': None,
            'llava_active': False,
            'tinyllama_active': False,
            'tts_processes': []
        }
    
    def unload_whisper_model(self):
        """Whisper 모델 언로드"""
        try:
            # function_question.py의 전역 변수 접근
            import function.function_question as fq
            if hasattr(fq, 'whisper_model') and fq.whisper_model is not None:
                print("🧹 Whisper 모델 언로드 중...")
                del fq.whisper_model
                fq.whisper_model = None
                self.loaded_models['whisper'] = None
                print("✅ Whisper 모델 언로드 완료")
                return True
        except Exception as e:
            print(f"⚠️ Whisper 언로드 중 오류: {e}")
        return False
    
    def stop_all_ollama_models(self):
        """모든 Ollama 모델 중지"""
        models_to_stop = ['llava', 'tinyllama']
        stopped_models = []
        
        for model in models_to_stop:
            try:
                print(f"🛑 {model} 모델 중지 중...")
                result = subprocess.run(
                    ['ollama', 'stop', model], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ {model} 모델 중지 완료")
                    stopped_models.append(model)
                    self.loaded_models[f'{model}_active'] = False
                else:
                    print(f"⚠️ {model} 모델 중지 실패: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"⚠️ {model} 모델 중지 타임아웃")
            except Exception as e:
                print(f"⚠️ {model} 모델 중지 오류: {e}")
        
        return stopped_models
    
    def kill_all_tts_processes(self):
        """모든 TTS 관련 프로세스 종료"""
        tts_patterns = [
            'tts_cli.py',
            'GPTSoVits', 
            'GPT-SoVITS',
            'tts_server'
        ]
        
        killed_count = 0
        for pattern in tts_patterns:
            try:
                print(f"🔫 TTS 프로세스 종료 중: {pattern}")
                result = subprocess.run(
                    ['pkill', '-f', pattern], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode == 0:
                    killed_count += 1
                    print(f"✅ {pattern} 프로세스 종료 완료")
            except Exception as e:
                print(f"⚠️ {pattern} 프로세스 종료 오류: {e}")
        
        return killed_count > 0
    
    def kill_tablet_processes(self):
        """태블릿 관련 프로세스 종료"""
        try:
            # 실행 중인 태블릿 프로세스 찾기
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'tablet' in cmdline.lower() or 'coordinate' in cmdline.lower():
                        print(f"🔫 태블릿 프로세스 종료: PID {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            print("✅ 태블릿 프로세스 정리 완료")
            return True
        except Exception as e:
            print(f"⚠️ 태블릿 프로세스 종료 오류: {e}")
            return False
    
    def clear_gpu_memory(self):
        """GPU 메모리 정리"""
        try:
            import torch
            if torch.cuda.is_available():
                print("🧹 GPU 메모리 캐시 정리 중...")
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                print("✅ GPU 메모리 정리 완료")
                return True
        except ImportError:
            print("ℹ️ PyTorch가 설치되지 않음 - GPU 메모리 정리 건너뜀")
        except Exception as e:
            print(f"⚠️ GPU 메모리 정리 오류: {e}")
        return False
    
    def clear_system_memory(self):
        """시스템 메모리 정리"""
        try:
            print("🧹 시스템 메모리 가비지 컬렉션 중...")
            gc.collect()
            print("✅ 시스템 메모리 정리 완료")
            return True
        except Exception as e:
            print(f"⚠️ 시스템 메모리 정리 오류: {e}")
            return False
    
    def emergency_memory_cleanup(self):
        """긴급 메모리 정리 - 모든 모델과 프로세스 종료"""
        print("🚨 긴급 메모리 정리 시작...")
        
        cleanup_results = {
            'whisper': self.unload_whisper_model(),
            'ollama': len(self.stop_all_ollama_models()) > 0,
            'tts': self.kill_all_tts_processes(),
            'tablet': self.kill_tablet_processes(),
            'gpu': self.clear_gpu_memory(),
            'system': self.clear_system_memory()
        }
        
        success_count = sum(1 for success in cleanup_results.values() if success)
        total_count = len(cleanup_results)
        
        print(f"🎯 메모리 정리 완료: {success_count}/{total_count} 작업 성공")
        print("=" * 50)
        
        return cleanup_results
    
    def get_memory_status(self):
        """현재 메모리 사용량 확인"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            gpu_info = "N/A"
            
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.memory_allocated() / 1024**3  # GB
                    gpu_cached = torch.cuda.memory_reserved() / 1024**3   # GB
                    gpu_info = f"GPU: {gpu_memory:.1f}GB 사용, {gpu_cached:.1f}GB 캐시"
            except:
                pass
            
            print(f"💾 메모리 상태:")
            print(f"   RAM: {memory.percent}% 사용 ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)")
            print(f"   {gpu_info}")
            
            return {
                'ram_percent': memory.percent,
                'ram_used_gb': memory.used/1024**3,
                'ram_total_gb': memory.total/1024**3,
                'gpu_info': gpu_info
            }
        except Exception as e:
            print(f"⚠️ 메모리 상태 확인 오류: {e}")
            return None

# 전역 메모리 관리자 인스턴스
memory_manager = MemoryManager()

# 편의 함수들
def emergency_exit_to_main():
    """취소 버튼 시 호출 - 모든 리소스 해제하고 메인으로"""
    print("🔄 메인 메뉴로 비상 복귀 중...")
    cleanup_results = memory_manager.emergency_memory_cleanup()
    return cleanup_results

def get_memory_status():
    """현재 메모리 상태 확인"""
    return memory_manager.get_memory_status()

if __name__ == "__main__":
    # 테스트
    print("메모리 관리 시스템 테스트")
    get_memory_status()
    print("\n긴급 정리 테스트")
    emergency_exit_to_main()