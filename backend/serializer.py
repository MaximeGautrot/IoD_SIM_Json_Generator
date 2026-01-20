import json
import re
from dataclasses import is_dataclass, fields
from typing import Any, Dict, List, Type, Union, get_origin, get_args
from backend.models import *

# --- Gestionnaires de Casse ---

def to_camel_case(snake_str: str) -> str:
    """net_devices -> netDevices"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def camel_to_snake(camel_str: str) -> str:
    """netDevices -> net_devices"""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()

def pascal_to_snake(pascal_str: str) -> str:
    """RxGain -> rx_gain"""
    if not pascal_str: return ""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', pascal_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# --- Encoder JSON ---

class ScenarioEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            # 1. Gestion spéciale des objets Ns3Model (Structure polymorphique)
            if isinstance(obj, Ns3Model):
                return {
                    "name": obj.name,
                    "attributes": obj.get_ns3_attributes()
                }

            # 2. Gestion spéciale pour PhyLocalConfig (Sortie direct PascalCase)
            if isinstance(obj, PhyLocalConfig):
                res = {}
                for f in fields(obj):
                    val = getattr(obj, f.name)
                    if val is not None:
                        res[snake_to_pascal(f.name)] = val
                return res

            # 3. Gestion spéciale pour IrsPatch (Sortie spécifique PascalCase)
            if isinstance(obj, IrsPatch):
                return {
                    "Size": obj.size,
                    "PhaseX": obj.phase_x,
                    "PhaseY": obj.phase_y
                }

            # 4. Gestion Standard (CamelCase)
            result = {}
            for field in fields(obj):
                value = getattr(obj, field.name)
                
                if value is None or field.name == "extra_attributes":
                    continue
                
                if field.name == "ZSPs": key = "ZSPs"
                elif field.name == "staticNs3Config": key = "staticNs3Config"
                elif field.name == "rest_time": key = "restTime" # Exception FlightPoint
                elif isinstance(obj, FlightPoint): key = field.name # position, interest
                else:
                    key = to_camel_case(field.name)

                result[key] = value
            return result
            
        return super().default(obj)

# --- Decoder JSON ---

def _populate_ns3_model(instance: Ns3Model, attrs_list: List[Dict[str, Any]]):
    field_map = {f.name: f for f in fields(instance)}
    
    for item in attrs_list:
        attr_name = item['name'] 
        attr_value = item['value']
        
        python_key = pascal_to_snake(attr_name)
        
        if attr_name == "RoITrigger": python_key = "ro_i_trigger"
        if attr_name == "LiIonEnergySourceInitialEnergyJ": python_key = "li_ion_energy_source_initial_energy_j"

        if python_key in field_map:
            field_type = field_map[python_key].type
            
            if python_key == "flight_plan" and isinstance(attr_value, list):
                val = [dict_to_dataclass(FlightPoint, fp) for fp in attr_value]
                setattr(instance, python_key, val)
            elif python_key == "patches" and isinstance(attr_value, list):
                val = [dict_to_dataclass(IrsPatch, p) for p in attr_value]
                setattr(instance, python_key, val)
            else:
                setattr(instance, python_key, attr_value)
        else:
            instance.extra_attributes[attr_name] = attr_value

def _resolve_ns3_class(data: Dict[str, Any], target_type: Type) -> Any:
    name = data.get("name", "")
    attrs = data.get("attributes", [])
    instance = None
    
    if "MobilityModel" in name:
        if "ConstantPosition" in name: instance = ConstantPositionMobilityModel(name=name)
        elif "ParametricSpeed" in name: instance = ParametricSpeedDroneMobilityModel(name=name)
    elif "EnergySource" in name: instance = LiIonEnergySource(name=name)
    elif "Mechanics" in name or name == "ns3::Drone": instance = DroneMechanics(name=name)
    elif "WifiManager" in name: instance = RemoteStationManager(name=name)
    elif "Application" in name or "UdpEcho" in name: instance = ApplicationConfig(name=name)
    elif "Peripheral" in name or "Irs" in name:
        if "Storage" in name: instance = StoragePeripheral(name=name)
        elif "Input" in name: instance = InputPeripheral(name=name)
        elif "Irs" in name: instance = IrsPeripheral(name=name)
        else: instance = Peripheral(name=name)
    
    if instance is None:
        instance = Ns3AttributeModel(name=name)
        
    _populate_ns3_model(instance, attrs)
    return instance

def dict_to_dataclass(cls: Type, data: Any) -> Any:
    if data is None: return None
    
    origin = get_origin(cls)
    args = get_args(cls)

    # 1. Listes
    if origin is list or origin is List:
        return [dict_to_dataclass(args[0], item) for item in data]
    
    # 2. Unions (C'est ici que ça plantait pour WorldDefinition)
    if origin is Union:
        non_none_types = [t for t in args if t is not type(None)]
        
        if len(non_none_types) == 1:
            target_type = non_none_types[0]
            if is_dataclass(target_type):
                return dict_to_dataclass(target_type, data)
            return data

        if isinstance(data, dict) and "name" in data and "attributes" in data:
            return _resolve_ns3_class(data, Ns3Model)
            
        return data

    # 3. Primitifs
    if not is_dataclass(cls):
        return data

    # 4. Ns3Model
    if issubclass(cls, Ns3Model) and isinstance(data, dict) and "attributes" in data:
        return _resolve_ns3_class(data, cls)

    # 5. Dataclass Standard
    init_args = {}
    for field in fields(cls):
        if field.name == "ZSPs": 
            json_key = "ZSPs"
        elif field.name == "staticNs3Config": 
            json_key = "staticNs3Config"
        elif cls is IrsPatch:
            if field.name == "size": 
                json_key = "Size"
            elif field.name == "phase_x": 
                json_key = "PhaseX"
            elif field.name == "phase_y": 
                json_key = "PhaseY"
        elif cls is FlightPoint:
            if field.name == "rest_time": 
                json_key = "restTime"
            else: 
                json_key = field.name
        elif cls is PhyLocalConfig:
            json_key = snake_to_pascal(field.name)
        else:
            json_key = to_camel_case(field.name)

        if json_key in data:
            init_args[field.name] = dict_to_dataclass(field.type, data[json_key])
            
    return cls(**init_args)

# --- API ---

def load_scenario(file_path: str) -> Scenario:
    with open(file_path, 'r') as f:
        return dict_to_dataclass(Scenario, json.load(f))

def save_scenario(scenario: Scenario, file_path: str):
    with open(file_path, 'w') as f:
        json.dump(scenario, f, cls=ScenarioEncoder, indent=4)