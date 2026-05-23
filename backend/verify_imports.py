import sys
from pathlib import Path

# Insert backend directory into sys.path
backend_dir = Path(__file__).parent.absolute()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

modules = [
    "app.rag",
    "app.analytics",
    "app.query_engine",
    "app.db",
    "app.curriculum",
    "app.saved_content",
]

failed = False
for mod_name in modules:
    try:
        __import__(mod_name)
        print(f"✅ {mod_name} imported")
    except ImportError as e:
        print(f"❌ {mod_name} failed: {e}")
        failed = True
    except Exception as e:
        print(f"⚠️ {mod_name} error: {e}")
        failed = True

if failed:
    sys.exit(1)
print("All core modules imported successfully.")
