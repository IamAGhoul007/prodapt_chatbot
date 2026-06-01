import sys
import site
import os

for p in site.getsitepackages() + [site.getusersitepackages()]:
    adk_path = os.path.join(p, 'google', 'adk')
    if os.path.exists(adk_path) and adk_path not in sys.path:
        sys.path.append(adk_path)

try:
    import a2a
    print("SUCCESS: imported a2a")
except Exception as e:
    print("FAIL:", e)
