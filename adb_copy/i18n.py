"""Internationalization (i18n) module for ADBCopy.

Provides translation support using a simple dictionary-based approach.
"""

from typing import Dict, Callable


class Translation:
    """Translation manager for the application.
    
    Supports multiple languages with fallback to English.
    """
    
    def __init__(self) -> None:
        """Initialize translation manager."""
        self._current_language = "en"
        self._translations: Dict[str, Dict[str, str]] = {
            "en": {},  # English (default, no translation needed)
            "ko": self._load_korean()
        }
    
    def _load_korean(self) -> Dict[str, str]:
        """Load Korean translations.
        
        Returns:
            Dictionary mapping English text to Korean text
        """
        return {
            # Menu items
            "File": "파일",
            "Transfer": "전송",
            "Language": "언어",
            "About": "정보",
            "About ADBCopy": "ADBCopy 정보",
            "Exit": "종료",
            "Push (Local→Remote)": "로컬→원격 전송 (Push)",
            "Pull (Remote→Local)": "원격→로컬 전송 (Pull)",
            "English": "English",
            "Korean": "한국어",
            
            # Main window
            "ADBCopy - ADB File Explorer": "ADBCopy - ADB 파일 탐색기",
            "UI initialized": "UI 초기화 완료",
            "Device Watcher started": "기기 감시 시작됨",
            "Connected device": "연결된 기기",
            "No device connected": "연결된 기기가 없습니다",
            
            # Console messages
            "ADBCopy started": "ADBCopy 시작됨",
            "Transfer started": "전송 시작",
            "Transfer completed": "전송 완료",
            "Transfer failed": "전송 실패",
            "All transfers completed": "모든 전송 작업 완료",
            
            # File panel
            "Local Panel": "로컬 패널",
            "Remote Panel": "원격 패널",
            "Local path...": "로컬 경로...",
            "Go": "이동",
            "Refresh": "새로고침",
            
            # Transfer queue
            "Status": "상태",
            "Filename": "파일명",
            "Source": "원본",
            "Destination": "대상",
            "Time(sec)": "시간(초)",
            "Overall Progress": "전체 진행률",
            "Waiting": "대기",
            "In Progress": "진행",
            "Completed": "완료",
            "Failed": "실패",
            "Pause": "일시정지",
            "Resume": "재개",
            "Retry Failed": "실패건 재시도",
            "Clear Completed": "완료건 지우기",
            
            # Status
            "⏳ Waiting": "⏳ 대기",
            "⚡ Transferring": "⚡ 전송중",
            "✓ Completed": "✓ 완료",
            "✗ Failed": "✗ 실패",
            
            # Context menu
            "Delete": "삭제",
            "Rename": "이름 변경",
            "New Folder": "새 폴더",
            
            # Dialogs
            "Confirm": "확인",
            "Cancel": "취소",
            "Overwrite": "덮어쓰기",
            "Skip": "건너뛰기",
            "Rename": "이름 변경",
            "Apply to all": "모두 적용",
            
            # Messages
            "File already exists": "파일이 이미 존재합니다",
            "Invalid path": "유효하지 않은 경로입니다",
            "No device connected": "연결된 기기가 없습니다",
            "Permission denied": "접근 권한이 없습니다",
            "Load failed": "로드 실패",
            
            # Time format
            "Time": "시간",
            "Speed": "속도",
            "Ready": "준비",
            
            # Format strings
            "files": "개 파일",
            "directories": "개 디렉토리",
            "Total size": "총 크기",
            "selected": "선택",
            
            # Additional translations
            "Device Watcher started": "기기 감시 시작됨",
            "UI initialized": "UI 초기화 완료",
            "Transfer worker initialized": "전송 워커 초기화 완료",
            "Connected device": "연결된 기기",
            "Transfer failed": "전송 실패",
            "All transfers completed": "모든 전송 작업 완료",
            "Transfer paused": "전송 일시정지",
            "Transfer resumed": "전송 재개",
            "Console hidden": "콘솔 숨김",
            "Console shown": "콘솔 표시",
            "No dragged file information": "드래그된 파일 정보 없음",
            "Dropped to same panel (ignored)": "같은 패널에 드롭됨 (무시)",
            "No transferable files": "전송 가능한 파일 없음",
            "folders skipped (folder transfer not supported)": "개 폴더는 건너뜁니다 (폴더 전송은 미지원)",
            "Please select files to transfer from local panel.": "로컬 패널에서 전송할 파일을 선택하세요.",
            "Please select files to transfer from remote panel.": "원격 패널에서 전송할 파일을 선택하세요.",
            "No transferable files (folders are excluded)": "전송 가능한 파일이 없습니다 (폴더는 제외됨)",
            "files added for transfer": "개 파일 전송 추가",
            "Upload": "업로드",
            "Download": "다운로드",
            "Added to transfer queue (in progress)": "전송 큐에 추가됨 (진행 중)",
            "Transfer started": "전송 시작",
            "Transfer completed": "전송 완료",
            "Retrying": "개 실패 작업 재시도 중...",
            "No failed tasks to retry": "재시도할 실패 작업이 없습니다",
            "Closing application...": "애플리케이션 종료 중...",
            "Info": "알림",
            "Device state abnormal": "기기 상태 비정상",
            "Using first active device": "첫 번째 활성 기기 사용",
            "files drag started": "개 파일 드래그 시작",
            
            # Status texts (with emoji)
            "⏳ Waiting": "⏳ 대기",
            "⚡ Transferring": "⚡ 전송중",
            "✓ Completed": "✓ 완료",
            "✗ Failed": "✗ 실패",
            
            # Progress bar
            "Overall Progress": "전체 진행률",
            
            # Missing translations
            "ADBCopy started": "ADBCopy 시작됨",
            "Source size": "원본 크기",
            "Destination size": "대상 크기",
            "Unknown": "알 수 없음",
            "Local path...": "로컬 경로...",
            "Go": "이동",
            "Back": "뒤로",
            "Forward": "앞으로",
            "My PC": "내 PC",
            "Desktop": "바탕 화면",
            "Documents": "문서",
            "Downloads": "다운로드",
            "Pictures": "사진",
            "Music": "음악",
            "Videos": "비디오",
            "Path error": "경로 오류",
            "Path does not exist": "존재하지 않는 경로입니다",
            "Path does not exist or is inaccessible:\n{0}": "존재하지 않거나 접근할 수 없는 경로입니다:\n{0}",
            
            # File detail widget translations
            "Confirm Delete": "삭제 확인",
            "Delete {0} item(s)?": "{0}개 항목을 삭제하시겠습니까?",
            "Delete Failed": "삭제 실패",
            "New name:": "새 이름:",
            "Rename Failed": "이름 변경 실패",
            "Folder name:": "폴더 이름:",
            "Folder Creation Failed": "폴더 생성 실패",
            "{0} file(s)": "{0}개 파일",
            "{0} dir(s)": "{0}개 디렉토리",
            "Total size: {0}": "총 크기: {0}",
            "0 items": "0개 항목",
            "{0} file(s) selected": "{0}개 파일 선택",
            "{0} dir(s) selected": "{0}개 디렉토리 선택",
            "0 selected": "0개 선택",
            "Name": "이름",
            "Size": "크기",
            "Date": "날짜",
            "Permissions": "권한",
            "Type": "종류",
            "Parent": "상위",
            "Folder": "폴더",
            "File": "파일",
            "Loading...": "로딩 중...",
            "0 items": "0개 항목",
        }
    
    def set_language(self, language: str) -> None:
        """Set the current language.
        
        Args:
            language: Language code ("en" or "ko")
        """
        if language in self._translations:
            self._current_language = language
    
    def get_language(self) -> str:
        """Get the current language code.
        
        Returns:
            Current language code
        """
        return self._current_language
    
    def translate(self, text: str) -> str:
        """Translate text to the current language.
        
        Args:
            text: English text to translate
            
        Returns:
            Translated text or original if translation not found
        """
        if self._current_language == "en":
            return text
        
        translations = self._translations.get(self._current_language, {})
        return translations.get(text, text)
    
    def __call__(self, text: str) -> str:
        """Shorthand for translate().
        
        Args:
            text: English text to translate
            
        Returns:
            Translated text
        """
        return self.translate(text)


# Global translation instance
_translator = Translation()


def tr(text: str) -> str:
    """Translate text using the global translator.
    
    Args:
        text: English text to translate
        
    Returns:
        Translated text
    """
    return _translator(text)


def set_language(language: str) -> None:
    """Set the global language.
    
    Args:
        language: Language code ("en" or "ko")
    """
    _translator.set_language(language)


def get_language() -> str:
    """Get the current global language.
    
    Returns:
        Current language code
    """
    return _translator.get_language()

