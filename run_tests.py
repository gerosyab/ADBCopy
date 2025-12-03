"""ADBCopy 통합 테스트 스크립트

지금까지 발견된 버그와 주요 기능들을 테스트합니다.
"""
import sys
import re
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


class TestResults:
    """테스트 결과 저장"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
    
    def add_pass(self, name: str):
        self.passed.append(name)
        print(f"✓ {name}")
    
    def add_fail(self, name: str, error: str):
        self.failed.append((name, error))
        print(f"✗ {name}: {error}")
    
    def add_skip(self, name: str, reason: str):
        self.skipped.append((name, reason))
        print(f"⊘ {name}: {reason}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print("\n" + "="*60)
        print("테스트 결과 요약")
        print("="*60)
        print(f"총 테스트: {total}")
        print(f"✓ 통과: {len(self.passed)}")
        print(f"✗ 실패: {len(self.failed)}")
        print(f"⊘ 스킵: {len(self.skipped)}")
        
        if self.failed:
            print("\n실패한 테스트:")
            for name, error in self.failed:
                print(f"  - {name}")
                print(f"    원인: {error}")
        
        return len(self.failed) == 0


def test_adb_manager(results: TestResults):
    """ADB 관리자 테스트"""
    print("\n[1] ADB Manager 테스트")
    print("-" * 60)
    
    try:
        from adb_copy.core.adb_manager import AdbManager
        manager = AdbManager()
        
        # ADB 실행 가능 여부
        if manager.check_adb_available():
            results.add_pass("ADB 실행 가능")
        else:
            results.add_fail("ADB 실행 가능", "ADB를 찾을 수 없습니다")
        
    except Exception as e:
        results.add_fail("ADB Manager 초기화", str(e))


def test_ls_parsing(results: TestResults):
    """ls 출력 파싱 테스트 (버그 수정 검증)"""
    print("\n[2] ls 파싱 테스트 (setuid/setgid 권한 비트)")
    print("-" * 60)
    
    try:
        from adb_copy.workers.file_list_worker import FileListWorker
        worker = FileListWorker()
        
        # 실제 /sdcard/ 출력 샘플 (s, t 권한 비트 포함)
        test_cases = [
            # Music만 보이던 버그 케이스
            ("""total 115
drwxrws---  2 u0_a286  media_rw  3452 2024-08-01 15:15 Alarms
drwxrws--x  6 media_rw media_rw  3452 2025-01-26 18:24 Android
drwxrwxr-x  9 media_rw media_rw  3452 2025-05-10 20:19 Music
drwxrws--- 13 u0_a286  media_rw 53248 2025-12-03 09:03 Download
drwxrws--- 22 u0_a286  media_rw  3452 2025-12-01 14:56 DCIM""", 5),
            
            # Sticky bit (t) 포함
            ("""drwxrwxrwt  2 root root 3452 2024-08-01 15:15 tmp
drwxr-xr-x  2 root root 3452 2024-08-01 15:15 normal""", 2),
        ]
        
        for i, (ls_output, expected_count) in enumerate(test_cases, 1):
            files = worker._parse_ls_output(ls_output, "/sdcard/")
            if len(files) == expected_count:
                results.add_pass(f"ls 파싱 케이스 {i} ({expected_count}개 폴더)")
            else:
                results.add_fail(
                    f"ls 파싱 케이스 {i}",
                    f"예상 {expected_count}개, 실제 {len(files)}개"
                )
        
        # 권한 비트 검증
        test_output = "drwxrws---  2 user group 3452 2024-08-01 15:15 TestFolder"
        files = worker._parse_ls_output(test_output, "/test/")
        if files and files[0].permissions == "drwxrws---":
            results.add_pass("setuid/setgid 권한 비트 파싱")
        else:
            results.add_fail("setuid/setgid 권한 비트 파싱", "권한 문자열 불일치")
            
    except Exception as e:
        results.add_fail("ls 파싱 테스트", str(e))


def test_local_drives(results: TestResults):
    """로컬 드라이브 로딩 테스트"""
    print("\n[3] 로컬 드라이브 테스트 (D:, E: 등)")
    print("-" * 60)
    
    try:
        from adb_copy.ui.file_detail_widget import FileDetailWidget
        from adb_copy.ui.folder_tree_widget import FolderTreeWidget
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # 파일 디테일 위젯 테스트
        widget = FileDetailWidget(panel_type="local")
        
        # 존재하는 드라이브 찾기
        test_drives = []
        for letter in "CDEFGH":
            drive_path = f"{letter}:\\"
            if Path(drive_path).exists():
                test_drives.append(drive_path)
        
        if not test_drives:
            results.add_skip("로컬 드라이브 테스트", "테스트할 드라이브 없음")
            return
        
        for drive_path in test_drives:
            try:
                widget.load_path(drive_path)
                
                # 에러 체크 (첫 행이 에러 메시지인지 확인)
                if widget.table.rowCount() > 0:
                    first_item = widget.table.item(0, 0)
                    if first_item and "⚠" in first_item.text():
                        results.add_fail(
                            f"{drive_path} 로딩",
                            first_item.text()
                        )
                    else:
                        results.add_pass(f"{drive_path} 로딩 성공")
                else:
                    # 빈 드라이브일 수 있음
                    results.add_pass(f"{drive_path} 로딩 성공 (빈 폴더)")
                    
            except Exception as e:
                results.add_fail(f"{drive_path} 로딩", str(e))
        
        # 폴더 트리 위젯의 드라이브 경로 검증
        tree_widget = FolderTreeWidget(panel_type="local")
        root_item = tree_widget.tree_widget.topLevelItem(0)  # My PC
        
        drive_count = 0
        for i in range(root_item.childCount()):
            child = root_item.child(i)
            if "💾" in child.text(0):
                drive_count += 1
                # UserRole에 저장된 경로 검증
                stored_path = child.data(0, Qt.ItemDataRole.UserRole)
                
                if stored_path is None:
                    results.add_fail(
                        f"드라이브 경로 저장 ({child.text(0)})",
                        "경로가 None"
                    )
                elif not Path(stored_path).exists():
                    results.add_fail(
                        f"드라이브 경로 저장 ({child.text(0)})",
                        f"유효하지 않은 경로: {stored_path}"
                    )
        
        if drive_count > 0:
            results.add_pass(f"드라이브 트리 생성 ({drive_count}개)")
        else:
            results.add_fail("드라이브 트리 생성", "드라이브를 찾을 수 없음")
            
    except Exception as e:
        results.add_fail("로컬 드라이브 테스트", str(e))


def test_path_handling(results: TestResults):
    """경로 처리 테스트"""
    print("\n[4] 경로 처리 테스트")
    print("-" * 60)
    
    try:
        # Windows 경로 테스트
        test_paths = [
            ("C:\\", True),
            ("C:\\Users", True),
            ("D:\\", Path("D:\\").exists()),
            ("C:/Users", True),  # 슬래시 혼용
        ]
        
        for path, should_exist in test_paths:
            path_obj = Path(path)
            if should_exist:
                if path_obj.exists():
                    results.add_pass(f"경로 처리: {path}")
                else:
                    results.add_fail(f"경로 처리: {path}", "경로가 존재하지 않음")
            else:
                results.add_skip(f"경로 처리: {path}", "드라이브 없음")
                
    except Exception as e:
        results.add_fail("경로 처리 테스트", str(e))


def test_version_management(results: TestResults):
    """버전 관리 테스트"""
    print("\n[5] 버전 관리 테스트")
    print("-" * 60)
    
    try:
        from adb_copy import __version__
        
        # 버전 형식 검증 (x.y.z)
        if re.match(r'^\d+\.\d+\.\d+$', __version__):
            results.add_pass(f"버전 형식 검증 (v{__version__})")
        else:
            results.add_fail("버전 형식 검증", f"잘못된 형식: {__version__}")
        
        # __init__.py 파일 존재 확인
        init_file = Path("adb_copy/__init__.py")
        if init_file.exists():
            results.add_pass("__init__.py 존재 확인")
        else:
            results.add_fail("__init__.py 존재 확인", "파일을 찾을 수 없음")
            
    except Exception as e:
        results.add_fail("버전 관리 테스트", str(e))


def test_ui_initialization(results: TestResults):
    """UI 초기화 테스트"""
    print("\n[6] UI 초기화 테스트")
    print("-" * 60)
    
    try:
        from adb_copy.ui.file_detail_widget import FileDetailWidget
        from adb_copy.ui.folder_tree_widget import FolderTreeWidget
        from adb_copy.ui.transfer_queue_widget import TransferQueueWidget
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Local 패널
        local_detail = FileDetailWidget(panel_type="local")
        if local_detail.panel_type == "local":
            results.add_pass("Local FileDetailWidget 초기화")
        else:
            results.add_fail("Local FileDetailWidget 초기화", "패널 타입 불일치")
        
        # Remote 패널
        remote_detail = FileDetailWidget(panel_type="remote")
        if remote_detail.panel_type == "remote":
            results.add_pass("Remote FileDetailWidget 초기화")
        else:
            results.add_fail("Remote FileDetailWidget 초기화", "패널 타입 불일치")
        
        # 폴더 트리
        folder_tree = FolderTreeWidget(panel_type="local")
        results.add_pass("FolderTreeWidget 초기화")
        
        # 전송 큐
        transfer_queue = TransferQueueWidget()
        results.add_pass("TransferQueueWidget 초기화")
        
    except Exception as e:
        results.add_fail("UI 초기화 테스트", str(e))


def main():
    """메인 테스트 실행"""
    print("="*60)
    print("ADBCopy 통합 테스트")
    print("="*60)
    
    results = TestResults()
    
    # 각 테스트 실행
    test_adb_manager(results)
    test_ls_parsing(results)
    test_local_drives(results)
    test_path_handling(results)
    test_version_management(results)
    test_ui_initialization(results)
    
    # 결과 출력
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

