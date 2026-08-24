import sys

def verify():
    try:
        import sklearn
        import numpy as np
        import src.utils.json_utils
        print("PASS: Core dependencies and modules loaded.")
        sys.exit(0)
    except ImportError as e:
        print(f"FAIL: Missing dependency or module - {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
