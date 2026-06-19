import math
from time import perf_counter

from PySide6.QtWidgets import QApplication, QWidget

def has_gui():
    try:
        app = QApplication([])
        widget = QWidget()
        widget.show()
        widget.hide()
        app.quit()
        return True
    except:
        return False

def fmt_time(amt_seconds:int|float) -> str:
    if amt_seconds <= 0:
        return "now"
    elif amt_seconds < 1:
        size = int(math.log10(amt_seconds) / 3)-1
        return f"{amt_seconds/10**(size*3):.2f}{'mun'[-size-1]}s"
    elif amt_seconds < 60:
        return f"{amt_seconds:.2f}s"
    elif amt_seconds < 60**2:
        seconds = int(amt_seconds % 60)
        return f"{int(amt_seconds/60):02d}:{seconds:02d} mm:ss"
    elif amt_seconds < 60**2*24:
        minutes = int(amt_seconds % 60**2)
        return f"{int(amt_seconds/60**2):02d}:{minutes:02d} hh:mm"
    elif amt_seconds < 60**2*24*365:
        hours = int(amt_seconds % (60**2*24))
        return f"{int(amt_seconds/(60**2*24))}:{hours:02d} d:hh"
    return f"a pretty fucking long time..."

def timer(func):
    def wrapper(*args, **kwargs):
        start = perf_counter()
        res = func(*args, **kwargs)
        print(f"{func.__name__} took {fmt_time(perf_counter() - start)}")
        return res
    return wrapper
