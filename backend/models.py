from dataclasses import dataclass, field, fields
from typing import List, Optional, Union, Literal, Dict, Any

# --- Utilitaires ---
def snake_to_pascal(snake_str: str) -> str:
    """Convertit snake_case vers PascalCase (pour les attributs ns-3 et PhyLocal)."""
    return ''.join(word.capitalize() for word in snake_str.split('_'))

# --- Base Hybride ---
@dataclass
class Ns3Model:
    """Classe de base capturant les attributs typés et les champs inconnus (extra_attributes)."""
    name: str = field(default="")
    extra_attributes: Dict[str, Any] = field(default_factory=dict, repr=False)

    def get_ns3_attributes(self) -> List[Dict[str, Any]]:
        attrs = []
        for f in fields(self):
            if f.name in ["name", "extra_attributes"]: continue
            val = getattr(self, f.name)
            if val is not None:
                # Conversion standard vers PascalCase pour les attributs ns-3
                ns3_name = snake_to_pascal(f.name)
                attrs.append({"name": ns3_name, "value": val})
        
        for key, val in self.extra_attributes.items():
            attrs.append({"name": key, "value": val})
        return attrs

# --- Monde ---
@dataclass
class Building:
    """Définition d'un bâtiment (Obstacle)."""
    type: Literal["residential", "office", "commercial"]
    walls: Literal["wood", "concreteWithWindows", "concreteWithoutWindows", "stoneBlocks"]
    boundaries: List[float]
    floors: int
    rooms: List[int]

@dataclass
class WorldDefinition:
    """Conteneur des objets physiques."""
    size: Optional[Dict[str, str]] = None
    buildings: List[Building] = field(default_factory=list)
    regionsOfInterest: List[List[float]] = field(default_factory=list)

# --- Configuration Réseau Globale ---
@dataclass
class Ns3AttributeModel(Ns3Model):
    """Fallback pour tout modèle ns-3 non explicitement mappé."""
    pass

@dataclass
class ChannelConfig:
    """Configuration du canal de propagation."""
    propagationDelayModel: Optional[Ns3AttributeModel] = None
    propagationLossModel: Optional[Ns3AttributeModel] = None
    spectrumModel: Optional[Ns3AttributeModel] = None

@dataclass
class PhyLayerConfig:
    """Configuration globale de la couche physique."""
    type: Literal["wifi", "lte"]
    channel: Optional[ChannelConfig] = None
    standard: Optional[str] = None
    attributes: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class RemoteStationManager(Ns3Model):
    """Gestionnaire de station Wi-Fi."""
    data_mode: Optional[str] = None
    control_mode: Optional[str] = None
    fragmentation_threshold: Optional[str] = None
    rts_cts_threshold: Optional[str] = None
    non_unicast_mode: Optional[str] = None

@dataclass
class MacLayerConfig:
    """Configuration globale de la couche MAC."""
    type: Literal["wifi", "lte"]
    ssid: Optional[str] = None
    remoteStationManager: Optional[RemoteStationManager] = None

@dataclass
class NetworkLayerConfig:
    """Configuration globale IP."""
    type: Literal["ipv4"]
    address: str
    mask: str
    gateway: str

# --- Composants Internes ---
@dataclass
class FlightPoint:
    """Point de passage pour le FlightPlan."""
    position: List[float]
    interest: int
    rest_time: Optional[float] = None # Sera mappé vers restTime

@dataclass
class ConstantPositionMobilityModel(Ns3Model):
    """Mobilité stationnaire."""
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])

@dataclass
class ParametricSpeedDroneMobilityModel(Ns3Model):
    """Mobilité dynamique de drone."""
    speed_coefficients: List[float] = field(default_factory=list)
    flight_plan: List[FlightPoint] = field(default_factory=list)
    curve_step: float = 0.01

MobilityModelType = Union[ConstantPositionMobilityModel, ParametricSpeedDroneMobilityModel, Ns3AttributeModel]

# --- LTE ---
@dataclass
class LteBitrate:
    """Débit simple (DL/UL)."""
    downlink: float 
    uplink: float

@dataclass
class LteBitrateConfig:
    """Structure GBR/MBR pour LTE."""
    guaranteed: LteBitrate
    maximum: LteBitrate

@dataclass
class LteBearer:
    """Configuration QoS LTE."""
    type: str
    bitrate: Optional[LteBitrateConfig] = None

# --- NetDevices ---
@dataclass
class PhyLocalConfig:
    """Configuration PHY locale (override). Les champs seront convertis en PascalCase."""
    tx_power: Optional[float] = None
    enable_uplink_power_control: Optional[bool] = None

@dataclass
class NetDeviceConfig:
    """Interface réseau d'un nœud."""
    type: Literal["wifi", "lte"]
    # network_layer est parfois local (int) ici
    network_layer: Optional[int] = None 
    mac_layer: Optional[Union[Ns3AttributeModel, Dict[str, Any]]] = None
    
    # LTE Specifics
    role: Optional[Literal["UE", "eNB"]] = None
    bearers: List[LteBearer] = field(default_factory=list)
    
    # Overrides
    phy: Optional[PhyLocalConfig] = None 
    antenna_model: Optional[Ns3AttributeModel] = None

# --- Applications ---
@dataclass
class ApplicationConfig(Ns3Model):
    """Applications réseau génératrices de trafic."""
    start_time: Optional[float] = None
    stop_time: Optional[float] = None
    destination_ipv4_address: Optional[str] = None
    remote_address: Optional[str] = None
    transmission_interval: Optional[float] = None
    interval: Optional[float] = None
    packet_size: Optional[int] = None
    payload_size: Optional[int] = None

# --- Hardware Drone ---
@dataclass
class DroneMechanics(Ns3Model):
    """Propriétés physiques du drone."""
    mass: float = 1.0
    rotor_disk_area: float = 0.2
    drag_coefficient: float = 0.1

@dataclass
class LiIonEnergySource(Ns3Model):
    """Batterie Li-Ion."""
    li_ion_energy_source_initial_energy_j: float = 0.0
    li_ion_energy_low_battery_threshold: float = 0.0
    periodic_energy_update_interval: Optional[str] = None

# --- Périphériques ---
@dataclass
class Peripheral(Ns3Model):
    """Périphérique générique."""
    power_consumption: List[float] = field(default_factory=list)
    ro_i_trigger: Optional[List[int]] = None

@dataclass
class StoragePeripheral(Peripheral):
    """Périphérique de stockage."""
    capacity: int = 0

@dataclass
class InputPeripheral(Peripheral):
    """Capteur/Entrée."""
    data_rate: float = 0.0
    has_storage: Optional[bool] = None

@dataclass
class IrsPatch:
    """Patch pour surface intelligente (IRS)."""
    size: List[int]    # JSON: Size
    phase_x: float     # JSON: PhaseX
    phase_y: float     # JSON: PhaseY

@dataclass
class IrsPeripheral(Peripheral):
    """Périphérique IRS complet."""
    rows: int = 0
    columns: int = 0
    pru_x: float = 0.0
    pru_y: float = 0.0
    roto_axis: List[str] = field(default_factory=list)
    roto_angles: List[float] = field(default_factory=list)
    patches: List[IrsPatch] = field(default_factory=list)

PeripheralType = Union[StoragePeripheral, InputPeripheral, IrsPeripheral, Peripheral]

# --- Entités ---
@dataclass
class NodeConfig:
    """Nœud générique (Drone, ZSP, Remote)."""
    # Renommage en snake_case pour mapping correct
    net_devices: List[NetDeviceConfig] = field(default_factory=list)
    mobility_model: Optional[MobilityModelType] = None
    applications: List[ApplicationConfig] = field(default_factory=list)
    
    # Parfois networkLayer est défini au niveau du Node (ex: remotes)
    network_layer: Optional[int] = None 
    name: Optional[str] = None

@dataclass
class DroneConfig(NodeConfig):
    """Extension Drone avec physique et énergie."""
    mechanics: Optional[DroneMechanics] = None
    battery: Optional[LiIonEnergySource] = None
    peripherals: List[PeripheralType] = field(default_factory=list)

# --- Racine ---
@dataclass
class Ns3StaticConfig:
    """Configuration statique ns-3."""
    name: str
    value: str

@dataclass
class Scenario:
    """Objet racine du fichier de configuration."""
    name: str
    resultsPath: str
    duration: float
    logOnFile: bool
    phyLayer: List[PhyLayerConfig]
    macLayer: List[MacLayerConfig]
    networkLayer: List[NetworkLayerConfig]
    
    dryRun: bool = False
    staticNs3Config: List[Ns3StaticConfig] = field(default_factory=list)
    world: Optional[WorldDefinition] = None
    
    drones: List[DroneConfig] = field(default_factory=list)
    ZSPs: List[NodeConfig] = field(default_factory=list)
    remotes: List[NodeConfig] = field(default_factory=list)
    nodes: List[NodeConfig] = field(default_factory=list)
    
    radioMapParameters: List[Union[str, float]] = field(default_factory=list)
    logComponents: List[str] = field(default_factory=list)
    analytics: List[Dict[str, Any]] = field(default_factory=list)