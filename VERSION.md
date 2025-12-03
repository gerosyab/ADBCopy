# 버전 관리 가이드

## 현재 버전
버전은 `adb_copy/__init__.py`에서 관리됩니다.

```python
__version__ = "0.1.1"
```

## 버전 업데이트 방법

### 1. 버전 번호 변경
`adb_copy/__init__.py` 파일만 수정하면 됩니다:

```python
__version__ = "0.2.0"  # 새 버전
```

### 2. 자동 반영되는 곳
- `build.bat` - 빌드 시 자동으로 버전 읽어옴
- `build_onefile.bat` - 빌드 시 자동으로 버전 읽어옴
- `main_window.py` - About 다이얼로그에 표시
- 생성되는 zip 파일명 자동 변경

### 3. 수동 업데이트 필요한 파일
다음 문서 파일들은 릴리스 시 수동으로 업데이트해야 합니다:
- `README.md`
- `RELEASE.md`
- `BUILD.md`

## 릴리스 체크리스트

- [ ] `adb_copy/__init__.py` 버전 업데이트
- [ ] 빌드 테스트 (`build.bat` 또는 `build_onefile.bat`)
- [ ] README.md 업데이트 (필요시)
- [ ] RELEASE.md 업데이트
- [ ] Git 커밋 및 태그

```bash
git add .
git commit -m "Release v0.2.0"
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main
git push origin v0.2.0
```

