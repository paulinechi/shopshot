import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import ScenarioRequestHandler


class handler(ScenarioRequestHandler):
    pass
