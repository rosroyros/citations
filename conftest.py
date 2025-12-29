# Root conftest.py for pytest path configuration
# This ensures the dashboard package is importable before any tests run

import sys
import os

# Add project root to path so dashboard package can be imported
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"CONFTEST: project_root = {project_root}")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"CONFTEST: added project_root to sys.path")

# Also ensure backend is in path for app imports
backend_path = os.path.join(project_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
    print(f"CONFTEST: added backend_path to sys.path")

print(f"CONFTEST: sys.path[:5] = {sys.path[:5]}")

# Test dashboard import here
try:
    import dashboard
    print(f"CONFTEST: dashboard imported from {dashboard.__file__}")
    print(f"CONFTEST: dashboard.__path__ = {getattr(dashboard, '__path__', 'NO __path__')}")
    
    # Pre-import ALL dashboard submodules used by app.py and test_helpers.py
    import dashboard.analytics as da
    print(f"CONFTEST: dashboard.analytics imported")
    
    import dashboard.log_parser
    print(f"CONFTEST: dashboard.log_parser imported")
    
    import dashboard.database
    print(f"CONFTEST: dashboard.database imported")
    
    # Debug sys.modules
    print(f"CONFTEST: dashboard modules in sys.modules:")
    for key in sorted(sys.modules.keys()):
        if key.startswith('dashboard'):
            print(f"  {key}: {sys.modules[key]}")
except Exception as e:
    print(f"CONFTEST: dashboard import FAILED: {e}")
    import traceback
    traceback.print_exc()

