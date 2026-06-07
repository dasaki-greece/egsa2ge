import sys
from pathlib import Path

# Προαιρετικά: Προσθήκη του src στο PYTHONPATH ώστε να βρίσκει το package
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from egsa87_google_earth.app import main

if __name__ == "__main__":
    main()
