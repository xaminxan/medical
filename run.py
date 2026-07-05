"""FDA Engine entry point."""
import sys
from pathlib import Path

# Register agent_core as nanobot BEFORE any other imports
# This allows all internal "from nanobot.xxx" imports to work
sys.path.insert(0, str(Path(__file__).parent))
import agent_core
sys.modules["nanobot"] = agent_core

# Now import the rest
import uvicorn
from fda_engine.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
