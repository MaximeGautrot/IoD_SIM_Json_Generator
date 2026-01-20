from dataclasses import fields, is_dataclass, field, MISSING
from typing import List, Union, get_origin, get_args, Literal

def get_real_type(typing_type):
    """Extrait le type réel d'un Optional ou d'une liste simple."""
    origin = get_origin(typing_type)
    args = get_args(typing_type)
    
    if origin is Union:
        non_none_args = [t for t in args if t is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
        return typing_type 
    
    if origin is list or origin is List:
        return args[0]
        
    return typing_type

def create_default_instance(cls):
    """
    Crée une instance robuste en remplissant les champs obligatoires.
    """
    if cls is int: return 0
    if cls is float: return 0.0
    if cls is str: return ""
    if cls is bool: return False
    
    if get_origin(cls) is Literal:
        return get_args(cls)[0]

    if is_dataclass(cls):
        try:
            return cls()
        except TypeError:
            kwargs = {}
            for f in fields(cls):
                if f.default is MISSING and f.default_factory is MISSING:
                    
                    if get_origin(f.type) is Literal:
                        kwargs[f.name] = get_args(f.type)[0]
                    elif get_origin(f.type) in (list, List):
                        kwargs[f.name] = []
                    else:
                        real_type = get_real_type(f.type)
                        kwargs[f.name] = create_default_instance(real_type)
            
            try:
                return cls(**kwargs)
            except Exception as e:
                print(f"[ERREUR] Impossible d'instancier {cls.__name__}: {e}")
                return None
            
    return None