import importlib
import sys

dependencies = [
    ("opencv-python", "cv2"),
    ("mediapipe", "mediapipe"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("websockets", "websockets"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scikit-learn", "sklearn")
]

print("Starting dependency verification...")
print(f"Python Version: {sys.version}\n")

missing_any = False
installed_versions = {}

for pkg_name, import_name in dependencies:
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "unknown")
        print(f"[OK] {pkg_name} is installed. Imported as '{import_name}' (Version: {version})")
        installed_versions[pkg_name] = version
    except ImportError as e:
        print(f"[MISSING] {pkg_name} is NOT installed (Failed to import '{import_name}'): {e}")
        missing_any = True

if missing_any:
    print("\nSome dependencies are missing. Please run:")
    print("pip install -r requirements.txt")
else:
    print("\nAll dependencies are successfully installed and verified!")
