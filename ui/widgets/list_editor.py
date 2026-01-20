from dataclasses import is_dataclass
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal

from ui.utils import create_default_instance

class ListEditor(QWidget):
    # Signal émis quand la liste change (ajout/suppression/modif primitive)
    data_changed = Signal() 

    def __init__(self, data_list: list, item_type, parent=None):
        super().__init__(parent)
        self.data_list = data_list
        self.item_type = item_type
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        h_layout = QHBoxLayout()
        self.lbl_count = QLabel(f"Éléments: {len(self.data_list)}")
        btn_add = QPushButton("Ajouter (+)")
        btn_add.clicked.connect(self.add_item)
        
        h_layout.addWidget(self.lbl_count)
        h_layout.addWidget(btn_add)
        self.layout.addLayout(h_layout)
        
        # Container Items
        self.items_layout = QVBoxLayout()
        self.items_container = QWidget()
        self.items_container.setLayout(self.items_layout)
        self.layout.addWidget(self.items_container)
        
        self.refresh_list()

    def refresh_list(self):
        from ui.widgets.auto_form import AutoForm # Import local

        # Nettoyage
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for i, item in enumerate(self.data_list):
            row_layout = QHBoxLayout()
            
            # CAS 1 : DATACLASS (Objets complexes)
            if is_dataclass(self.item_type):
                name = getattr(item, 'name', f"Item {i+1}") or f"Item {i+1}"
                gb = QGroupBox(str(name))
                gb.setStyleSheet("QGroupBox { font-weight: bold; color: #333; margin-top: 5px; border: 1px solid #bbb; }")
                gb_ly = QVBoxLayout(gb)
                
                form = AutoForm(item)
                gb_ly.addWidget(form)
                
                container = QWidget()
                c_ly = QHBoxLayout(container)
                c_ly.addWidget(gb)
                
                btn_del = QPushButton("X")
                btn_del.setFixedWidth(30)
                btn_del.setStyleSheet("background-color: #ffcccc; color: red;")
                btn_del.clicked.connect(lambda _, idx=i: self.remove_item(idx))
                
                c_ly.addWidget(btn_del)
                self.items_layout.addWidget(container)

            # CAS 2 : PRIMITIF (Logs, Ints...)
            else:
                editor_widget = None
                if self.item_type is str:
                    editor_widget = QLineEdit(str(item))
                    editor_widget.textChanged.connect(lambda val, idx=i: self.update_primitive(idx, val))
                elif self.item_type is int:
                    editor_widget = QSpinBox()
                    editor_widget.setRange(-999999, 999999)
                    editor_widget.setValue(int(item))
                    editor_widget.valueChanged.connect(lambda val, idx=i: self.update_primitive(idx, val))
                elif self.item_type is float:
                    editor_widget = QDoubleSpinBox()
                    editor_widget.setValue(float(item))
                    editor_widget.valueChanged.connect(lambda val, idx=i: self.update_primitive(idx, val))
                
                if editor_widget:
                    btn_del = QPushButton("X")
                    btn_del.setFixedWidth(30)
                    btn_del.clicked.connect(lambda _, idx=i: self.remove_item(idx))
                    
                    row_layout.addWidget(editor_widget)
                    row_layout.addWidget(btn_del)
                    
                    w = QWidget()
                    w.setLayout(row_layout)
                    self.items_layout.addWidget(w)

        self.lbl_count.setText(f"Éléments: {len(self.data_list)}")

    def add_item(self):
        new_obj = create_default_instance(self.item_type)
        if new_obj is not None:
            self.data_list.append(new_obj)
            self.refresh_list()
            self.data_changed.emit()

    def remove_item(self, index):
        if 0 <= index < len(self.data_list):
            self.data_list.pop(index)
            self.refresh_list()
            self.data_changed.emit()

    def update_primitive(self, index, value):
        self.data_list[index] = value
        self.data_changed.emit()