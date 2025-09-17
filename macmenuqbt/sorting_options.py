import json
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel
)

CONFIG_FILE = os.path.expanduser("~/Library/Application Support/MMqBt/qbt_menu_config.json")


class SortingOptions(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚙️ Display and Sorting Options")
        self.setGeometry(100, 100, 700, 450)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        lists_layout = QHBoxLayout()

        self.available_list = QListWidget()
        self.available_list.setDragDropMode(QListWidget.InternalMove)
        self.available_list.setSelectionMode(QListWidget.MultiSelection)

        self.selected_list = QListWidget()
        self.selected_list.setDragDropMode(QListWidget.InternalMove)
        self.selected_list.setSelectionMode(QListWidget.SingleSelection)
        self.selected_list.currentItemChanged.connect(self.update_preview)
        self.selected_list.model().rowsInserted.connect(self.update_preview)
        self.selected_list.model().rowsRemoved.connect(self.update_preview)
        self.selected_list.model().rowsMoved.connect(self.update_preview)

        arrow_layout = QVBoxLayout()
        arrow_layout.setAlignment(Qt.AlignCenter)
        btn_right = QPushButton("→")
        btn_left = QPushButton("←")
        btn_all_right = QPushButton(">>")
        btn_all_left = QPushButton("<<")
        btn_right.clicked.connect(self.move_right)
        btn_left.clicked.connect(self.move_left)
        btn_all_right.clicked.connect(self.move_all_right)
        btn_all_left.clicked.connect(self.move_all_left)
        arrow_layout.addWidget(btn_right)
        arrow_layout.addWidget(btn_left)
        arrow_layout.addSpacing(20)
        arrow_layout.addWidget(btn_all_right)
        arrow_layout.addWidget(btn_all_left)

        reorder_layout = QVBoxLayout()
        reorder_layout.setAlignment(Qt.AlignCenter)
        btn_up = QPushButton("↑")
        btn_down = QPushButton("↓")
        btn_top = QPushButton("⇑")
        btn_bottom = QPushButton("⇓")
        btn_up.clicked.connect(self.move_up)
        btn_down.clicked.connect(self.move_down)
        btn_top.clicked.connect(self.move_top)
        btn_bottom.clicked.connect(self.move_bottom)
        reorder_layout.addWidget(btn_up)
        reorder_layout.addWidget(btn_down)
        reorder_layout.addSpacing(20)
        reorder_layout.addWidget(btn_top)
        reorder_layout.addWidget(btn_bottom)

        lists_layout.addWidget(self.available_list)
        lists_layout.addLayout(arrow_layout)
        lists_layout.addWidget(self.selected_list)
        lists_layout.addLayout(reorder_layout)

        main_layout.addLayout(lists_layout)

        self.preview_label = QLabel()
        self.preview_label.setText("Example 1")
        self.preview_label.setStyleSheet(
            "border: 1px solid gray; padding:5px; font-family: 'Courier New'; font-size: 14pt;"
        )
        main_layout.addWidget(QLabel("Preview (emojis are not displayed here):"))
        main_layout.addWidget(self.preview_label)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save")
        self.btn_done = QPushButton("Done")
        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addWidget(self.btn_save)
        bottom_layout.addWidget(self.btn_done)
        main_layout.addLayout(bottom_layout)

        self.btn_cancel.clicked.connect(self.close)
        self.btn_save.clicked.connect(self.save)
        self.btn_done.clicked.connect(self.done)

        self.load_config()
        self.update_preview()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)

        self.available_list.clear()
        self.selected_list.clear()

        for entry in config_data:
            name = entry["name"]
            state = entry["state"]
            item = QListWidgetItem(name)
            item.setTextAlignment(Qt.AlignCenter)
            if state:
                self.selected_list.addItem(item)
            else:
                self.available_list.addItem(item)

    def save_config(self):
        data = []
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            data.append({"name": item.text(), "state": True})
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            data.append({"name": item.text(), "state": False})

        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def save(self):
        self.save_config()

    def done(self):
        self.save_config()
        self.close()

    def move_right(self):
        for item in self.available_list.selectedItems():
            row = self.available_list.row(item)
            self.available_list.takeItem(row)
            self.selected_list.addItem(item)
        self.update_preview()

    def move_left(self):
        for item in self.selected_list.selectedItems():
            row = self.selected_list.row(item)
            self.selected_list.takeItem(row)
            self.available_list.addItem(item)
        self.update_preview()

    def move_all_right(self):
        while self.available_list.count() > 0:
            item = self.available_list.takeItem(0)
            self.selected_list.addItem(item)
        self.update_preview()

    def move_all_left(self):
        while self.selected_list.count() > 0:
            item = self.selected_list.takeItem(0)
            self.available_list.addItem(item)
        self.update_preview()

    def move_up(self):
        row = self.selected_list.currentRow()
        if row > 0:
            item = self.selected_list.takeItem(row)
            self.selected_list.insertItem(row - 1, item)
            self.selected_list.setCurrentRow(row - 1)
            self.update_preview()

    def move_down(self):
        row = self.selected_list.currentRow()
        if row < self.selected_list.count() - 1 and row != -1:
            item = self.selected_list.takeItem(row)
            self.selected_list.insertItem(row + 1, item)
            self.selected_list.setCurrentRow(row + 1)
            self.update_preview()

    def move_top(self):
        row = self.selected_list.currentRow()
        if row > 0:
            item = self.selected_list.takeItem(row)
            self.selected_list.insertItem(0, item)
            self.selected_list.setCurrentRow(0)
            self.update_preview()

    def move_bottom(self):
        row = self.selected_list.currentRow()
        if row != -1 and row < self.selected_list.count() - 1:
            item = self.selected_list.takeItem(row)
            self.selected_list.addItem(item)
            self.selected_list.setCurrentRow(self.selected_list.count() - 1)
            self.update_preview()

    def update_preview(self):
        preview_map = {
            "Status": "⬇",
            "DL/UP/Tot Size": "3.6 / 1.2 / 4.8 Go",
            "Progress (%)": "75%",
            "Ratio UP/DL": "33.3%",
            "DL speed": "1.2 MB/s",
            "UP speed": "1.2 MB/s",
            "ETA": "10 min",
            "Seeds/Leechers": "46/21",
            "Category": "Fun",
            "Added on": "2025-12-25-19:58"
        }
        parts = ["Example 1"]
        for i in range(self.selected_list.count()):
            text = self.selected_list.item(i).text()
            parts.append(preview_map.get(text, text))
        self.preview_label.setText(" | ".join(parts))


def main():
    d_s_app = QApplication(sys.argv)
    window = SortingOptions()
    window.show()
    sys.exit(d_s_app.exec_())
