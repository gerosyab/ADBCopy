# ADBCopy 빠른 시작 가이드

## 개발자용 (Python 소스코드 실행)

### 1. 사전 준비
```bash
# 저장소 클론
git clone https://github.com/gerosyab/ADBCopy.git
cd ADBCopy

# 의존성 설치
pip install PyQt6
```

### 2. 실행 방법

**빌드 없이 바로 실행:**
```bash
python -m adb_copy.main
```

또는:
```bash
cd adb_copy
python main.py
```

### 3. 테스트 실행

**전체 통합 테스트:**
```bash
python run_tests.py
```

**개별 모듈 테스트 (Python REPL):**
```python
# ADB 연결 테스트
from adb_copy.core.adb_manager import AdbManager
manager = AdbManager()
print(manager.check_adb_available())
print(manager.get_devices())

# ls 파싱 테스트
from adb_copy.workers.file_list_worker import FileListWorker
worker = FileListWorker()
output = "drwxrws---  2 user group 3452 2024-08-01 15:15 TestFolder"
files = worker._parse_ls_output(output, "/test/")
print(files)
```

### 4. 디버그 모드

디버그 메시지를 보려면 터미널에서 실행:
```bash
python -m adb_copy.main
# 콘솔에 [DEBUG] 메시지 출력됨
```

---

## 사용자용 (실행 파일)

### 1. 빌드

**단일 파일 (권장):**
```bash
pip install pyinstaller
.\build_onefile.bat
```

**폴더 형태 (빠른 실행):**
```bash
.\build.bat
```

### 2. 실행

**단일 파일:**
```bash
dist\onefile\ADBCopy.exe
```

**폴더:**
```bash
dist\folder\ADBCopy\ADBCopy.exe
```

---

## 버전 업데이트

### 버전 변경
`adb_copy/__init__.py` 파일만 수정:
```python
__version__ = "0.2.0"  # 새 버전
```

### 빌드 및 릴리스
```bash
# 1. 테스트
python run_tests.py

# 2. 빌드
.\build.bat
.\build_onefile.bat

# 3. Git 커밋
git add .
git commit -m "Release v0.2.0"
git push origin main

# 4. 태그 생성
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# 5. GitHub에서 Release 생성
# - dist/onefile/ADBCopy_v0.2.0_Windows_Portable.zip
# - dist/folder/ADBCopy_v0.2.0_Windows.zip
```

---

## 문제 해결

### ADB를 찾을 수 없음
```bash
# ADB 설치 확인
adb version

# PATH에 추가 (Windows)
setx PATH "%PATH%;C:\platform-tools"
```

### PyQt6 import 오류
```bash
# 재설치
pip uninstall PyQt6
pip install PyQt6
```

### 드라이브가 안 열림
```bash
# 테스트 실행으로 원인 확인
python run_tests.py
# "[3] 로컬 드라이브 테스트" 섹션 확인
```

### 빌드 시 pathlib 오류
```bash
# pathlib 제거 (내장 모듈과 충돌)
pip uninstall pathlib
```

---

## 참고 문서

- [README.md](README.md) - 전체 문서
- [VERSION.md](VERSION.md) - 버전 관리 가이드
- [RELEASE.md](RELEASE.md) - 릴리스 프로세스
- [BUILD.md](BUILD.md) - 상세 빌드 가이드

