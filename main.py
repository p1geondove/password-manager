import sys
from password_manager.var import Flags

def main():
    if Flags.has_gui:
        from password_manager.gui import LoginWindow
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        win = LoginWindow()
        win.show()
        sys.exit(app.exec())
    else:
        import password_manager.tui
        ...

if __name__ == "__main__":
    main()
