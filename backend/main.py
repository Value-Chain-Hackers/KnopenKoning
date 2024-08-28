# main.py
import os
import sys
import uvicorn

from pathlib import Path
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    print("BASE_DIR: ", BASE_DIR)
    print("Loading environment variables {}".format(BASE_DIR / ".env"))
    load_dotenv(BASE_DIR / ".env")

    print(" 🚀 Starting the backend server...")
    print(" 📡 Listening on http://0.0.0.0:18000/")
    if sys.platform == "win32":
        # Based on Eryk Sun's code: https://stackoverflow.com/a/43095532
        import ctypes

        from signal import SIGINT, CTRL_C_EVENT

        _console_ctrl_handlers = {} # must be global / kept alive to avoid GC

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(
            ctypes.wintypes.BOOL,
            ctypes.wintypes.DWORD)

        def _errcheck_bool(result, func, args):
            if not result:
                raise ctypes.WinError(ctypes.get_last_error())
            return args

        kernel32.SetConsoleCtrlHandler.errcheck = _errcheck_bool
        kernel32.SetConsoleCtrlHandler.argtypes = (
            PHANDLER_ROUTINE,
            ctypes.wintypes.BOOL)
        from db.session import engine, SessionLocal, Base
        from db.company import Company
        from db.records import Records
        from db.website import Website
        try:
            Base.metadata.create_all(bind=engine)
            print("Tables created successfully!")
        except Exception as e:
            print(e)
        # get all companies and create their cache and data folders
        companies = SessionLocal().query(Company).all()
        for company in companies:
            if not os.path.exists(f"./.cache/{company.company_name}"):
                print(f"Creating cache folder for {company.company_name}")
                os.makedirs(f"./.cache/{company.company_name}")
            if not os.path.exists(f"./data/{company.company_name}"):
                print(f"Creating data folder for {company.company_name}")
                os.makedirs(f"./data/{company.company_name}")


        from uvicorn.supervisors.multiprocess import Multiprocess
        uvicorn_multiprocess_startup_orig = Multiprocess.startup
        def uvicorn_multiprocess_startup(self, *args, **kwargs):
            ret = uvicorn_multiprocess_startup_orig(self, *args, **kwargs)

            def win_ctrl_handler(dwCtrlType):
                if (dwCtrlType == CTRL_C_EVENT and
                    not self.should_exit.is_set()):
                    kernel32.SetConsoleCtrlHandler(_console_ctrl_handlers[win_ctrl_handler], False)
                    self.signal_handler(SIGINT, None)
                    del _console_ctrl_handlers[win_ctrl_handler]
                    return True
                return False

            if win_ctrl_handler not in _console_ctrl_handlers:
                h = PHANDLER_ROUTINE(win_ctrl_handler)
                kernel32.SetConsoleCtrlHandler(h, True)
                _console_ctrl_handlers[win_ctrl_handler] = h

            return ret
        Multiprocess.startup = uvicorn_multiprocess_startup

    uvicorn.run("backend.app:app", host="0.0.0.0", port=18000 , workers=1)