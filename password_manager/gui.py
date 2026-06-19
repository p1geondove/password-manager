from PySide6.QtWidgets import QApplication, QListWidgetItem, QWidget, QVBoxLayout, QLineEdit, QTextEdit, QListWidget, QLabel
from PySide6.QtCore import Qt
import rapidfuzz

from .crypt import PWManager, PWField

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("login")
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.password_box = QLineEdit(placeholderText="password", echoMode=QLineEdit.EchoMode.Password)
        self.password_box.returnPressed.connect(self.on_login)
        layout.addWidget(self.password_box)

    def on_login(self):
        try:
            self.manager = PWManager(self.password_box.text())
            self.managerwin = ManagerWindow(self.manager)
            self.managerwin.show()
            self.close()
        except Exception as e:
            print(e)
            pass

class ManagerWindow(QWidget):
    def __init__(self, manager:PWManager):
        super().__init__()
        self.manager = manager

        self.setWindowTitle("password-manager")
        self.resize(200,300)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.searchbox = QLineEdit(placeholderText="search entries")
        self.searchbox.textChanged.connect(self.on_search)
        self.main_layout.addWidget(self.searchbox)

        self.pwlist = QListWidget()
        self.reset_list()

        self.pwlist.itemDoubleClicked.connect(self.on_doubleclick)

        # right clicking in qt implies opening a context window, but we dont show that, just pull the mousepos from that to get the QListWidgetItem at that pos
        self.pwlist.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pwlist.customContextMenuRequested.connect(self.on_rightclick)

        self.main_layout.addWidget(self.pwlist)

    def reset_list(self, *args, **kwargs):
        print("resetting list")
        self.pwlist.clear()
        for entry in self.manager.load_from_file().values():
            item = QListWidgetItem(entry.name)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.pwlist.addItem(item)

    def on_search(self, *args, **kwargs):
        query = self.searchbox.text()

        if query:
            self.pwlist.clear()
            pwinfo = self.manager.load_from_file()
            pwinfolist = list(pwinfo.values())
            sorted_names = rapidfuzz.process.extract(self.searchbox.text(), [e.name for e in pwinfolist], limit=len(pwinfo))
            name_to_idx = {name:idx for idx,(name,_,_) in enumerate(sorted_names)}
            sorted_pwinfo = sorted(pwinfolist, key=lambda x:name_to_idx[x.name])
            for entry in sorted_pwinfo:
                item = QListWidgetItem(entry.name)
                item.setData(Qt.ItemDataRole.UserRole, entry)
                self.pwlist.addItem(item)

        else: # special case if query is empty string -> show all
            self.reset_list()

    def on_rightclick(self, pos):
        item = self.pwlist.itemAt(pos)
        if item is None: return
        entry = item.data(Qt.ItemDataRole.UserRole)
        QApplication.clipboard().setText(entry.password)
        print(f"put {entry.password} into clipboard")

    def on_doubleclick(self, item:QListWidgetItem):
        entry = item.data(Qt.ItemDataRole.UserRole)
        self.entryedit = PWEntryWindow(entry, self.manager)
        self.entryedit.destroyed.connect(self.reset_list)
        self.entryedit.destroyed
        self.entryedit.show()

class PWEntryWindow(QWidget):
    def __init__(self, entry:PWField, manager:PWManager):
        super().__init__()
        self.entry = entry
        self.manager = manager

        self.setWindowTitle(entry.name)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.lineedit_name = QLineEdit(placeholderText="name", text=entry.name)
        self.lineedit_username = QLineEdit(placeholderText="username", text=entry.username)
        self.lineedit_email = QLineEdit(placeholderText="email", text=entry.email)
        self.lineedit_password = QLineEdit(placeholderText="password", text=entry.password)
        self.textedit_extra = QTextEdit(entry.extra, placeholderText="extra")

        self.lineedit_name.returnPressed.connect(self.on_edit)
        self.lineedit_username.returnPressed.connect(self.on_edit)
        self.lineedit_email.returnPressed.connect(self.on_edit)
        self.lineedit_password.returnPressed.connect(self.on_edit)

        self.label_uuid = QLabel(f"uuid: {str(entry.uuid)}")
        self.label_creation = QLabel(f"created: {str(entry.creation_time)}")
        self.label_edit = QLabel(f"last edit: {str(entry.edit_time)}")

        layout.addWidget(self.lineedit_name)
        layout.addWidget(self.lineedit_username)
        layout.addWidget(self.lineedit_email)
        layout.addWidget(self.lineedit_password)
        layout.addWidget(self.label_uuid)
        layout.addWidget(self.label_creation)
        layout.addWidget(self.label_edit)

    def on_edit(self):
        self.manager.update_entry(
            self.entry.uuid,
            self.lineedit_name.text(),
            self.lineedit_username.text(),
            self.lineedit_email.text(),
            self.lineedit_password.text(),
            self.textedit_extra.toPlainText()
        )
