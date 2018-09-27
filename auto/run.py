import subprocess
import time

p = subprocess.Popen(['python', 'futureTest.py'])
print(p.pid)
time.sleep(5)
p.kill()