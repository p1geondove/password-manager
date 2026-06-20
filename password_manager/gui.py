from PySide6.QtWidgets import QApplication, QListWidgetItem, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QTextEdit, QListWidget, QLabel, QPushButton
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QShortcut, QKeySequence, QKeyEvent, QCloseEvent
from PySide6.QtGui import QKeyEvent

import rapidfuzz

from .const import PATH_SVG_EYE, PATH_SVG_MINUS, PATH_SVG_PLUS
from .crypt import PWManager, PWField

class PWListWidget(QListWidget):
    itemRemoved = Signal(QListWidgetItem)
    itemAdded = Signal(QListWidgetItem)

    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        item = self.currentItem()
        if item is None:
            return

        key = event.key()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.itemDoubleClicked.emit(item)
        if key == Qt.Key.Key_Plus:
            self.itemAdded.emit(item)
        if key in (Qt.Key.Key_Minus, Qt.Key.Key_Delete):
            self.itemRemoved.emit(item)
        else:
            super().keyPressEvent(event)

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("login")
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.password_box = QLineEdit(placeholderText="password", echoMode=QLineEdit.EchoMode.Password)
        self.password_box.returnPressed.connect(self.on_login)
        self.password_box.setStyleSheet("border: 1px solid grey; border-radius: 3px;")
        self.password_box.textChanged.connect(lambda: self.password_box.setStyleSheet("border: 1px solid grey; border-radius: 3px;"))
        layout.addWidget(self.password_box)

        self.toggle_visible_button = QPushButton()
        self.toggle_visible_button.setFlat(True)
        self.toggle_visible_button.setIcon(QIcon(str(PATH_SVG_EYE)))
        self.toggle_visible_button.setIconSize(QSize(20,20))
        self.toggle_visible_button.pressed.connect(self.on_toggle_visibitily)
        layout.addWidget(self.toggle_visible_button)

    def on_login(self):
        try:
            self.manager = PWManager(self.password_box.text())
            self.managerwin = ManagerWindow(self.manager)
            self.managerwin.show()
            self.close()
        except Exception as e:
            print(repr(self.password_box.styleSheet()))
            self.password_box.setStyleSheet("border: 1px solid red; border-radius: 3px;")
            print(repr(self.password_box.styleSheet()))
            print(f"wrong password, password file corrupted or pepper changed")

    def on_toggle_visibitily(self):
        if self.password_box.echoMode() == QLineEdit.EchoMode.Password:
            self.password_box.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_box.setEchoMode(QLineEdit.EchoMode.Password)

class ManagerWindow(QWidget):
    def __init__(self, manager:PWManager):
        super().__init__()
        self.manager = manager

        self.setWindowTitle("password-manager")
        self.resize(200,300)
        layout_main = QVBoxLayout()
        self.setLayout(layout_main)

        self.searchbox = QLineEdit(placeholderText="search entries")
        self.searchbox.textChanged.connect(self.on_search)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.searchbox.setFocus)
        layout_main.addWidget(self.searchbox)

        self.pwlist = PWListWidget()
        self.reset_list()
        self.pwlist.itemDoubleClicked.connect(self.on_entry_edit)
        self.pwlist.itemAdded.connect(self.on_add)
        self.pwlist.itemRemoved.connect(self.on_remove)
        # right clicking in qt implies opening a context window, but we dont show that, just pull the mousepos from that to get the QListWidgetItem at that pos
        self.pwlist.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pwlist.customContextMenuRequested.connect(self.on_rightclick)
        layout_main.addWidget(self.pwlist)

        layout_button = QHBoxLayout()
        self.button_add = QPushButton()
        self.button_add.setFlat(True)
        self.button_add.setIcon(QIcon(str(PATH_SVG_PLUS)))
        self.button_add.setIconSize(QSize(20,20))
        self.button_add.pressed.connect(self.on_add)
        layout_button.addWidget(self.button_add)

        self.button_remove = QPushButton()
        self.button_remove.setFlat(True)
        self.button_remove.setIcon(QIcon(str(PATH_SVG_MINUS)))
        self.button_remove.setIconSize(QSize(20,20))
        self.button_remove.pressed.connect(self.on_remove)
        layout_button.addWidget(self.button_remove)
        layout_main.addLayout(layout_button)

    def reset_list(self, *args, **kwargs):
        self.pwlist.clear()
        for entry in self.manager.load_from_file().values():
            item = QListWidgetItem(entry.name)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.pwlist.addItem(item)

    def open_entry_edit(self, entry:PWField):
        self.entryedit = PWEntryWindow(entry, self.manager)
        self.entryedit.closed.connect(self.on_search)
        self.entryedit.show()

    def on_entry_edit(self, item:QListWidgetItem):
        entry = item.data(Qt.ItemDataRole.UserRole)
        self.open_entry_edit(entry)

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

    def on_add(self):
        entry = self.manager.add_entry()
        self.open_entry_edit(entry)

    def on_remove(self):
        entry = self.pwlist.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        self.confirm_window = ConfirmRemoveWindow(self.manager, entry)
        self.confirm_window.closed.connect(self.on_search)
        self.confirm_window.show()

class PWEntryWindow(QWidget):
    closed = Signal()

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
        self.lineedit_password = QLineEdit(placeholderText="password", text=entry.password, echoMode=QLineEdit.EchoMode.Password)
        self.textedit_extra = QTextEdit(entry.extra, placeholderText="extra")

        self.toggle_visible_button = QPushButton()
        self.toggle_visible_button.setFlat(True)
        self.toggle_visible_button.setIcon(QIcon(str(PATH_SVG_EYE)))
        self.toggle_visible_button.setIconSize(QSize(20,20))
        self.toggle_visible_button.pressed.connect(self.on_toggle_visibitily)

        self.lineedit_name.returnPressed.connect(self.on_edit)
        self.lineedit_username.returnPressed.connect(self.on_edit)
        self.lineedit_email.returnPressed.connect(self.on_edit)
        self.lineedit_password.returnPressed.connect(self.on_edit)

        self.label_uuid = QLabel(f"uuid: {str(entry.uuid)}")
        self.label_creation = QLabel(f"created: {str(entry.creation_time)}")
        self.label_edit = QLabel(f"last edit: {str(entry.edit_time)}")

        passwordgroup = QHBoxLayout()
        passwordgroup.addWidget(self.lineedit_password)
        passwordgroup.addWidget(self.toggle_visible_button)

        layout.addWidget(self.lineedit_name)
        layout.addWidget(self.lineedit_username)
        layout.addWidget(self.lineedit_email)
        layout.addLayout(passwordgroup)

        layout.addWidget(self.label_uuid)
        layout.addWidget(self.label_creation)
        layout.addWidget(self.label_edit)

    def closeEvent(self, event: QCloseEvent, /) -> None:
        self.on_edit()
        self.closed.emit()
        return super().closeEvent(event)


    def on_edit(self):
        self.manager.update_entry(
            self.entry.uuid,
            self.lineedit_name.text(),
            self.lineedit_username.text(),
            self.lineedit_email.text(),
            self.lineedit_password.text(),
            self.textedit_extra.toPlainText()
        )

    def on_toggle_visibitily(self):
        if self.lineedit_password.echoMode() == QLineEdit.EchoMode.Password:
            self.lineedit_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.lineedit_password.setEchoMode(QLineEdit.EchoMode.Password)

class ConfirmRemoveWindow(QWidget):
    closed = Signal()

    def __init__(self, manager:PWManager, entry:PWField):
        super().__init__()
        self.setWindowTitle("Confirm")
        self.manager = manager
        self.entry = entry
        layout_main = QVBoxLayout()
        layout_buttons = QHBoxLayout()
        self.setLayout(layout_main)

        label = QLabel(f'Are you sure you want to remove "{entry.name}"')

        button_yes = QPushButton("Yes")
        button_yes.clicked.connect(self.on_yes)
        button_yes.setAutoDefault(True)
        button_no = QPushButton("No")
        button_no.clicked.connect(self.on_no)
        button_no.setAutoDefault(True)

        layout_buttons.addWidget(button_yes)
        layout_buttons.addWidget(button_no)
        layout_main.addWidget(label)
        layout_main.addLayout(layout_buttons)

    def closeEvent(self, event: QCloseEvent, /) -> None:
        self.closed.emit()
        return super().closeEvent(event)

    def on_yes(self):
        self.manager.remove_entry(self.entry.uuid)
        self.close()

    def on_no(self):
        self.close()
