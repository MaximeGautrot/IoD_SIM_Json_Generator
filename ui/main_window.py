# ui/main_window.py
import os
from dataclasses import is_dataclass
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from backend import serializer
from backend.models import *
from ui.widgets.list_editor import ListEditor
from ui.widgets.auto_form import AutoForm

class ScenarioTree(QTreeWidget):
    def __init__(self, main_window_ref):
        super().__init__()
        self.setHeaderLabel("Hiérarchie du Scénario")
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.main_window = main_window_ref
        self.current_scenario = None

    def populate(self, scenario):
        self.current_scenario = scenario
        self.clear()
        if not scenario: return

        root = QTreeWidgetItem(self, [scenario.name])
        root.setData(0, Qt.UserRole, scenario)
        
        # --- Helper Générique ---
        def add_category(parent, title, data_list, item_type):
            node = QTreeWidgetItem(parent, [title])
            node.setData(0, Qt.UserRole, {"list": data_list, "type": item_type})
            
            for i, item in enumerate(data_list):
                if is_dataclass(item):
                    name = getattr(item, 'name', None) or f"Item {i+1}"
                    child = QTreeWidgetItem(node, [str(name)])
                    child.setData(0, Qt.UserRole, item)
        
        # 1. Configuration Statique & Logs (Les "Administratifs")
        add_category(root, "Static NS3 Config", scenario.staticNs3Config, Ns3StaticConfig)
        
        log_node = QTreeWidgetItem(root, ["Log Components"])
        log_node.setData(0, Qt.UserRole, {"list": scenario.logComponents, "type": str})

        # 2. Le Monde
        if scenario.world:
            w_node = QTreeWidgetItem(root, ["World"])
            w_node.setData(0, Qt.UserRole, scenario.world)
            add_category(w_node, "Buildings", scenario.world.buildings, Building)

        # 3. Les Entités
        add_category(root, "Drones", scenario.drones, DroneConfig)
        add_category(root, "ZSPs", scenario.ZSPs, NodeConfig)
        add_category(root, "Remotes", scenario.remotes, NodeConfig)
        add_category(root, "Nodes", scenario.nodes, NodeConfig)

        add_category(root, "Phy Layers", scenario.phyLayer, type(scenario.phyLayer[0]) if scenario.phyLayer else object)
        
        root.setExpanded(True)
        root.setExpanded(True)

    def open_menu(self, position):
        item = self.itemAt(position)
        if not item: return
        
        data = item.data(0, Qt.UserRole)
        
        if isinstance(data, dict) and "list" in data and "type" in data:
            menu = QMenu()
            type_name = data["type"].__name__
            action = QAction(f"Ajouter {type_name}", self)
            action.triggered.connect(lambda: self.add_item_to_list(data["list"], data["type"], item))
            menu.addAction(action)
            menu.exec(self.viewport().mapToGlobal(position))

    def add_item_to_list(self, target_list, item_type, tree_item):
        new_obj = create_default_instance(item_type)
        if new_obj:
            if hasattr(new_obj, 'name'):
                new_obj.name = f"{item_type.__name__}_{len(target_list)+1}"
                
            target_list.append(new_obj)
            
            self.populate(self.current_scenario)
            
            tree_item.setExpanded(True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IoD-Sim Editor Pro")
        self.resize(1280, 800)
        
        self.current_scenario = None
        self.current_path = None
        
        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Horizontal)
        
        self.tree = ScenarioTree(self)
        self.tree.itemClicked.connect(self.on_tree_select)
        splitter.addWidget(self.tree)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.editor_placeholder = QLabel("Sélectionnez un élément pour l'éditer")
        self.editor_placeholder.setAlignment(Qt.AlignCenter)
        self.scroll.setWidget(self.editor_placeholder)
        splitter.addWidget(self.scroll)
        
        splitter.setSizes([300, 980])
        layout.addWidget(splitter)

    def setup_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("Fichier")
        
        file_menu.addAction("Ouvrir...", self.open_file, "Ctrl+O")
        file_menu.addAction("Enregistrer", self.save_file, "Ctrl+S")
        file_menu.addAction("Enregistrer sous...", self.save_file_as, "Ctrl+Shift+S")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir JSON", "", "JSON Files (*.json)")
        if path:
            try:
                self.current_scenario = serializer.load_scenario(path)
                self.current_path = path
                self.tree.populate(self.current_scenario)
                self.setWindowTitle(f"IoD-Sim Editor - {os.path.basename(path)}")
                self.scroll.setWidget(QLabel("Scénario chargé. Sélectionnez un élément."))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de charger:\n{e}")

    def save_file(self):
        if self.current_path:
            self._do_save(self.current_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        if not self.current_scenario: return
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder JSON", "", "JSON Files (*.json)")
        if path:
            self._do_save(path)

    def _do_save(self, path):
        try:
            serializer.save_scenario(self.current_scenario, path)
            self.current_path = path
            self.setWindowTitle(f"IoD-Sim Editor - {os.path.basename(path)}")
            QMessageBox.information(self, "Succès", "Fichier sauvegardé !")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Echec sauvegarde:\n{e}")

    def on_tree_select(self, item, col):
        data = item.data(0, Qt.UserRole)
        
        if isinstance(data, dict) and "list" in data:
            target_list = data["list"]
            item_type = data["type"]
            
            editor = ListEditor(target_list, item_type)
            
            editor.data_changed.connect(lambda: self.tree.populate(self.current_scenario))
            
            self.set_scroll_content(editor, f"Édition Liste : {item.text(0)}")

        elif is_dataclass(data):
            form = AutoForm(data)
            self.set_scroll_content(form, f"Édition : {type(data).__name__}")
            
        else:
            self.scroll.setWidget(QLabel("Élément non éditable."))

    def set_scroll_content(self, widget, title_str):
        container = QWidget()
        ly = QVBoxLayout(container)
        
        lbl = QLabel(title_str)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #444;")
        ly.addWidget(lbl)
        ly.addWidget(widget)
        ly.addStretch()
        
        self.scroll.setWidget(container)