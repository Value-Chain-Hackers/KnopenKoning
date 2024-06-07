# create a pool of ollama processes by starting a new ollama process for each worker, set the environment variable OLLAMA_HOST to determine the port numbers
# make the class a singleton and use a lock to ensure that only one instance is created 
# create start and stop methods to start and stop the ollama processes
# handle the case where process dies by restarting it
import os
import subprocess
import threading
import time
import ctypes
# Kernel32 DLL loaded for calling Windows specific functions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

class OllamaPool:
    _instance = None
    _lock = threading.Lock()
    urls = []

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OllamaPool, cls).__new__(cls)
                cls._instance._processes = []
        return cls._instance
    
    def start(self, num_workers, num_parallel):
        for i in range(num_workers):
            try:
                port = 11500 + i
                myenv = os.environ.copy()
                myenv['OLLAMA_HOST'] = f'127.0.0.1:{port}'
                myenv['OLLAMA_NUM_PARALLEL'] = str(num_parallel)
                myenv['OLLAMA_FLASH_ATTENTION'] = "1"
                #myenv['OLLAMA_DEBUG'] = "1"
                #myenv['CUDA_VISIBLE_DEVICES'] = str(i % 2)

                log_filename = f"ollama_log_{port}.log"
                # if the log file exists, remove it
                if os.path.exists(log_filename):
                    os.remove(log_filename)

                with open(log_filename, 'a') as log_file:
                    process = subprocess.Popen(['ollama', 'serve'], env=myenv, 
                                               stdout=log_file, stderr=subprocess.STDOUT)
                    self.urls.append(f'http://localhost:{port}')
                    time.sleep(2)
                    self._processes.append(process)
            except Exception as e:
                print(f"Failed to start process on port {port}: {e}")

    def stop(self):
        for process in self._processes:
            try:
                print(f"Sending signal to stop process {process.pid}")
                try:
                    process.terminate()
                    # if not kernel32.GenerateConsoleCtrlEvent(0, process.pid):  # 0 is CTRL+C
                    #     raise Exception('Failed to send CTRL+C')
                except Exception as e:
                    print(f"Error sending signal to process {process.pid}: {e}")
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"Process {process.pid} did not terminate gracefully, killing it.")
                    process.kill()
                print(f"Process {process.pid} has been stopped.")
            except Exception as e:
                print(f"Error stopping process {process.pid}: {e}")
        self._processes.clear()

