"""
bcsfe 모듈의 모든 기능을 탐색합니다.
"""
import inspect

def explore():
    import bcsfe.core
    import bcsfe.core.game_version
    from bcsfe.core import ServerHandler, CountryCode, core_data
    
    print("=== bcsfe.core 주요 클래스/함수 ===")
    for name, obj in inspect.getmembers(bcsfe.core):
        if not name.startswith('_'):
            print(f"\n--- {name} ---")
            if inspect.isclass(obj):
                print(f"  Type: Class")
                for mname, mobj in inspect.getmembers(obj):
                    if not mname.startswith('_') and callable(mobj):
                        try:
                            sig = inspect.signature(mobj)
                            print(f"  {mname}{sig}")
                        except:
                            print(f"  {mname}")
            elif callable(obj):
                try:
                    sig = inspect.signature(obj)
                    print(f"  {name}{sig}")
                except:
                    print(f"  {name}")
    
    print("\n\n=== SaveFile 메소드 목록 ===")
    try:
        core_data.init_data()
        cc = CountryCode.from_code("kr")
        from bcsfe.core.game_version import GameVersion
        gv = GameVersion.from_string("12.5.0")
        
        # ServerHandler의 save_file 속성 타입 찾기
        handler_parents = ServerHandler.__mro__
        for parent in handler_parents:
            print(f"\n--- ServerHandler 상속: {parent.__name__} ---")
            for mname, mobj in inspect.getmembers(parent):
                if not mname.startswith('_') and callable(mobj):
                    try:
                        sig = inspect.signature(mobj)
                        print(f"  {mname}{sig}")
                    except:
                        print(f"  {mname}")
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    explore()