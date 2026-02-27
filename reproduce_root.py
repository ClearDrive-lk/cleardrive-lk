
import sys
import os

print(f"Current working directory: {os.getcwd()}")
print("sys.path:")
for p in sys.path:
    print(f"  {p}")

try:
    print("\nAttempting to import app.core.models...")
    import app.core.models
    print("Successfully imported app.core.models")
except ImportError as e:
    print(f"\nFailed to import app.core.models: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
