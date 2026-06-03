from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


def main() -> None:
    from core.server import MCPServer

    server = MCPServer(
        config_path=CURRENT_DIR / "config.json",
        modules_dir=CURRENT_DIR / "modules",
    ).initialize()
    server.run()


if __name__ == "__main__":
    main()
