"""Internationalization (i18n) module for ADBCopy.

Provides translation support using a simple dictionary-based approach.
Notifies registered listeners whenever the language changes so widgets
can update their text live without restart.

Note: this module deliberately avoids using a QObject signal for the
listener mechanism so it can be safely imported before QApplication is
created (e.g. during module-level constants).
"""

import weakref
from typing import Callable, Dict


class _LanguageChangedDispatcher:
    """Holds weak references to listener callables and dispatches updates."""
    
    def __init__(self) -> None:
        self._listeners: list = []
    
    def add(self, callback: Callable[[str], None]) -> None:
        """Register a callback (weakly held; bound methods supported)."""
        try:
            ref = weakref.WeakMethod(callback)
        except TypeError:
            ref = weakref.ref(callback)
        self._listeners.append(ref)
    
    def emit(self, language: str) -> None:
        """Invoke all live listeners; prune dead references."""
        alive = []
        for ref in self._listeners:
            cb = ref()
            if cb is None:
                continue
            alive.append(ref)
            try:
                cb(language)
            except Exception as e:
                print(f"[DEBUG] language listener failed: {e}")
        self._listeners = alive


class Translation:
    """Translation manager for the application.
    
    Supports multiple languages with fallback to English. Listeners can
    register via `add_language_listener` to be invoked when the active
    language changes.
    """
    
    def __init__(self) -> None:
        self._current_language = "en"
        self._translations: Dict[str, Dict[str, str]] = {
            "en": {},  # English (default, no translation needed)
            "ko": self._load_korean(),
        }
        self._dispatcher = _LanguageChangedDispatcher()
    
    def _load_korean(self) -> Dict[str, str]:
        """Load Korean translations.
        
        Returns:
            Dictionary mapping English text to Korean text.
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
            "Push": "Push",
            "Pull": "Pull",
            
            # Console messages
            "ADBCopy started": "ADBCopy 시작됨",
            "Transfer started": "전송 시작",
            "Transfer completed": "전송 완료",
            "Transfer failed": "전송 실패",
            "All transfers completed": "모든 전송 작업 완료",
            "Transfer paused": "전송 일시정지",
            "Transfer resumed": "전송 재개",
            "Transfer worker initialized": "전송 워커 초기화 완료",
            "Console hidden": "콘솔 숨김",
            "Console shown": "콘솔 표시",
            "Closing application...": "애플리케이션 종료 중...",
            "Language changed to {0}": "언어가 {0}(으)로 변경되었습니다",
            
            # File panel
            "Local Panel": "로컬 패널",
            "Remote Panel": "원격 패널",
            "Local path...": "로컬 경로...",
            "Go": "이동",
            "Refresh": "새로고침",
            "Back": "뒤로",
            "Forward": "앞으로",
            
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
            "Remove": "삭제",
            "Remove Selected": "선택 항목 삭제",
            "Remove Completed": "완료 항목 삭제",
            "Remove Failed": "실패 항목 삭제",
            "Remove Waiting": "대기 항목 삭제",
            "Remove Finished": "완료/실패 항목 삭제",
            "Remove All": "전체 삭제",
            "Confirm Remove All": "전체 삭제 확인",
            "Remove all queued items?": "대기열의 모든 항목을 삭제하시겠습니까?",
            "In-progress items will be kept ({0}).": "진행 중인 {0}개 항목은 유지됩니다.",
            "Time": "시간",
            "Speed": "속도",
            "Ready": "준비",
            
            # Status texts (with emoji)
            "⏳ Waiting": "⏳ 대기",
            "⚡ Transferring": "⚡ 전송중",
            "✓ Completed": "✓ 완료",
            "✗ Failed": "✗ 실패",
            
            # Context menu (existing + new)
            "Delete": "삭제",
            "Rename": "이름 변경",
            "New Folder": "새 폴더",
            "Make Directory": "새 폴더",
            "Open": "열기",
            "Open in Explorer": "탐색기로 열기",
            "Move to Trash": "휴지통으로 이동",
            "Permanent Delete": "영구 삭제",
            "This action cannot be undone.": "이 작업은 복구할 수 없습니다.",
            "OK": "확인",
            
            # Dialogs
            "Confirm": "확인",
            "Cancel": "취소",
            "Overwrite": "덮어쓰기",
            "Skip": "건너뛰기",
            "Apply to all": "모두 적용",
            "Confirm Delete": "삭제 확인",
            "Delete this item?": "이 항목을 삭제하시겠습니까?",
            "Delete {0} item(s)?": "{0}개 항목을 삭제하시겠습니까?",
            "Delete Failed": "삭제 실패",
            "New name:": "새 이름:",
            "Rename Failed": "이름 변경 실패",
            "Folder name:": "폴더 이름:",
            "Folder Creation Failed": "폴더 생성 실패",
            "File already exists": "파일이 이미 존재합니다",
            "Source size": "원본 크기",
            "Destination size": "대상 크기",
            "Unknown": "알 수 없음",
            
            # Messages
            "Invalid path": "유효하지 않은 경로입니다",
            "Permission denied": "접근 권한이 없습니다",
            "Load failed": "로드 실패",
            "Path error": "경로 오류",
            "Path does not exist": "존재하지 않는 경로입니다",
            "Path does not exist or is inaccessible:\n{0}": "존재하지 않거나 접근할 수 없는 경로입니다:\n{0}",
            "No dragged file information": "드래그된 파일 정보 없음",
            "Dropped to same panel (ignored)": "같은 패널에 드롭됨 (무시)",
            "No transferable files": "전송 가능한 파일 없음",
            "Please select files to transfer from local panel.": "로컬 패널에서 전송할 파일을 선택하세요.",
            "Please select files to transfer from remote panel.": "원격 패널에서 전송할 파일을 선택하세요.",
            "Added to transfer queue (in progress)": "전송 큐에 추가됨 (진행 중)",
            "Info": "알림",
            "Trash not supported on this system, falling back to permanent delete": "이 시스템에서는 휴지통이 지원되지 않습니다. 영구 삭제로 전환합니다",
            "Cannot open file": "파일을 열 수 없습니다",
            "Open After Download": "다운로드 후 열기",
            
            # Format strings
            "{0} file(s)": "{0}개 파일",
            "{0} dir(s)": "{0}개 디렉토리",
            "Total size: {0}": "총 크기: {0}",
            "0 items": "0개 항목",
            "{0} file(s) selected": "{0}개 파일 선택",
            "{0} dir(s) selected": "{0}개 디렉토리 선택",
            "0 selected": "0개 선택",
            
            # File detail columns
            "Name": "이름",
            "Size": "크기",
            "Date": "날짜",
            "Permissions": "권한",
            "Type": "종류",
            "Parent": "상위",
            "Folder": "폴더",
            "File": "파일",
            "Loading...": "로딩 중...",
            
            # Special folders
            "My PC": "내 PC",
            "Desktop": "바탕 화면",
            "Documents": "문서",
            "Downloads": "다운로드",
            "Pictures": "사진",
            "Music": "음악",
            "Videos": "비디오",
        }
    
    def set_language(self, language: str) -> None:
        """Set the current language.
        
        Notifies registered listeners only when the language actually
        changes, so widgets refresh their UI exactly once.
        
        Args:
            language: Language code ("en" or "ko").
        """
        if language not in self._translations:
            return
        if language == self._current_language:
            return
        self._current_language = language
        self._dispatcher.emit(language)
    
    def get_language(self) -> str:
        """Get the current language code."""
        return self._current_language
    
    def translate(self, text: str) -> str:
        """Translate text to the current language."""
        if self._current_language == "en":
            return text
        translations = self._translations.get(self._current_language, {})
        return translations.get(text, text)
    
    def __call__(self, text: str) -> str:
        return self.translate(text)
    
    def add_language_listener(self, callback: Callable[[str], None]) -> None:
        """Register a callable invoked with the new language code on change.
        
        The callback is held via a weak reference so registered widgets
        do not need to manually unregister - the listener is automatically
        pruned when the bound object is garbage-collected.
        """
        self._dispatcher.add(callback)


# Global translation instance
_translator = Translation()


def tr(text: str) -> str:
    """Translate text using the global translator."""
    return _translator(text)


def set_language(language: str) -> None:
    """Set the global language; notifies listeners if changed."""
    _translator.set_language(language)


def get_language() -> str:
    """Get the current global language."""
    return _translator.get_language()


def get_translator() -> Translation:
    """Return the global translator (use to register language listeners)."""
    return _translator
