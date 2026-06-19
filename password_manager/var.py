import json

from .const import PATH_SYSINFO
from .helper import has_gui

class _Flags:
    def __init__(self) -> None:
        if PATH_SYSINFO.exists():
            sysinfo = json.loads(PATH_SYSINFO.read_bytes())
            self.has_gui = sysinfo["has_gui"]
        else:
            self.has_gui = has_gui()
            sysinfo = {"has_gui":self.has_gui}
            PATH_SYSINFO.write_text(json.dumps(sysinfo))

Flags = _Flags()
