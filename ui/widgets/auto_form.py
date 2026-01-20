from dataclasses import fields, is_dataclass
from typing import List, Union, get_origin, get_args, Literal

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal

from ui.utils import get_real_type, create_default_instance
from ui.widgets.list_editor import ListEditor

try:
    from backend.models import snake_to_pascal
except ImportError:
    def snake_to_pascal(s): return s.title().replace("_", "")

class AutoForm(QWidget):
    content_changed = Signal()

    def __init__(self, data_obj, parent=None):
        super().__init__(parent)
        self.data_obj = data_obj
        self.layout = QFormLayout(self)
        self.layout.setLabelAlignment(Qt.AlignRight)
        self.layout.setContentsMargins(5, 5, 5, 5)

        if is_dataclass(data_obj):
            self.setup_ui()
        else:
            self.layout.addRow(QLabel("Non éditable (Type primitif dans liste)"))

    def setup_ui(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for f in fields(self.data_obj):
            field_name = f.name
            if field_name == "extra_attributes": continue

            field_label = snake_to_pascal(field_name)
            
            origin = get_origin(f.type)
            
            # 1. D'abord vérifier si c'est une LISTE (List[float], List[str], etc.)
            if origin in (list, List):
                current_value = getattr(self.data_obj, field_name)
                if current_value is None:
                    current_value = []
                    setattr(self.data_obj, field_name, current_value)
                
                item_type = get_args(f.type)[0]
                editor = ListEditor(current_value, item_type)
                
                editor.data_changed.connect(self.content_changed.emit)

                gb = QGroupBox(field_label)
                gb_ly = QVBoxLayout(gb)
                gb_ly.addWidget(editor)
                self.layout.addRow(gb)
                continue 

            # 2. Ensuite vérifier si c'est une UNION (Polymorphisme ou Optional)
            if origin is Union:
                current_value = getattr(self.data_obj, field_name)
                possible_types = [t for t in get_args(f.type) if t is not type(None)]
                
                if len(possible_types) == 1 and not is_dataclass(possible_types[0]):
                     pass 
                
                else:
                    container = QWidget()
                    cont_ly = QVBoxLayout(container)
                    cont_ly.setContentsMargins(0,0,0,0)

                    combo = QComboBox()
                    type_names = [t.__name__.split('.')[-1] for t in possible_types]
                    combo.addItems(type_names)

                    current_idx = 0
                    if current_value:
                        c_name = type(current_value).__name__
                        if c_name in type_names:
                            current_idx = type_names.index(c_name)
                    combo.setCurrentIndex(current_idx)

                    dynamic_area = QWidget()
                    dynamic_ly = QVBoxLayout(dynamic_area)
                    cont_ly.addWidget(combo)
                    cont_ly.addWidget(dynamic_area)

                    if current_value:
                        dynamic_ly.addWidget(AutoForm(current_value))

                    def on_poly_change(index, obj=self.data_obj, name=field_name, 
                                    types=possible_types, area=dynamic_ly):
                        new_cls = types[index]
                        new_inst = create_default_instance(new_cls)
                        setattr(obj, name, new_inst)
                        while area.count():
                            child = area.takeAt(0)
                            if child.widget(): child.widget().deleteLater()
                        area.addWidget(AutoForm(new_inst))

                    combo.currentIndexChanged.connect(on_poly_change)
                    self.layout.addRow(f"{field_label} (Type)", container)
                    continue

            field_type = get_real_type(f.type)
            current_value = getattr(self.data_obj, field_name)

            # 3. Gestion des Booléens
            if field_type is bool:
                widget = QCheckBox()
                widget.setChecked(bool(current_value))
                widget.stateChanged.connect(
                    lambda state, obj=self.data_obj, name=field_name: 
                    setattr(obj, name, bool(state))
                )
                self.layout.addRow(field_label, widget)

            # 4. Gestion des Nombres
            elif field_type in (int, float):
                if field_type is float:
                    widget = QDoubleSpinBox()
                    widget.setDecimals(6)
                    widget.setRange(-1e12, 1e12)
                else:
                    widget = QSpinBox()
                    widget.setRange(-int(1e9), int(1e9))
                
                val = current_value if current_value is not None else 0
                if isinstance(val, list): val = 0
                
                widget.setValue(val)
                widget.valueChanged.connect(
                    lambda val, obj=self.data_obj, name=field_name: 
                    setattr(obj, name, val)
                )
                self.layout.addRow(field_label, widget)

            # 5. Gestion des Chaînes
            elif field_type is str:
                widget = QLineEdit(str(current_value) if current_value is not None else "")
                widget.textChanged.connect(
                    lambda text, obj=self.data_obj, name=field_name: 
                    setattr(obj, name, text)
                )
                self.layout.addRow(field_label, widget)

            # 6. Gestion des Enums (Literal)
            elif get_origin(f.type) is Literal:
                widget = QComboBox()
                options = get_args(f.type)
                widget.addItems(options)
                if current_value in options:
                    widget.setCurrentText(current_value)
                widget.currentTextChanged.connect(
                    lambda text, obj=self.data_obj, name=field_name:
                    setattr(obj, name, text)
                )
                self.layout.addRow(field_label, widget)

            # 7. Objets Imbriqués simples (Dataclasses non Optionnelles)
            elif is_dataclass(field_type):
                if current_value is None:
                    current_value = create_default_instance(field_type)
                    setattr(self.data_obj, field_name, current_value)
                
                if current_value is None:
                    self.layout.addRow(field_label, QLabel("Erreur: Impossible de créer l'objet"))
                    continue
                
                gb = QGroupBox(field_label)
                gb.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; margin-top: 10px; }::title { subcontrol-origin: margin; left: 10px; }")
                gb_ly = QVBoxLayout(gb)
                sub_form = AutoForm(current_value)
                gb_ly.addWidget(sub_form)
                self.layout.addRow(gb)