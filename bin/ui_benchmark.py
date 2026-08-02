from __future__ import annotations

import sys

if getattr(sys, "frozen", False):
    sys.path.insert(0, getattr(sys, "_MEIPASS", ""))

from deps_check import require_dependencies

require_dependencies(frozen=getattr(sys, "frozen", False))

from app_paths import ensure_runtime_dirs
from ui.app import AuditApp  # re-export for tests/test_imports.py


def main() -> None:
    ensure_runtime_dirs()
    app = AuditApp()
    app.mainloop()


if __name__ == "__main__":
    main()
