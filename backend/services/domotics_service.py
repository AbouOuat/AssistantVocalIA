"""Domotics Service — contrôle d'appareils connectés (mock → réel en V3)."""

import logging
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SmartDevice:
    def __init__(self, id: str, name: str, device_type: str, status: str = "off"):
        self.id = id
        self.name = name
        self.device_type = device_type
        self.status = status

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.device_type, "status": self.status}


class DomoticsService:
    def __init__(self):
        self.devices: dict[str, SmartDevice] = {}
        self._init_demo_devices()

    def _init_demo_devices(self):
        self.devices["light_salon"] = SmartDevice("light_salon", "Lumière Salon", "light", "on")
        self.devices["light_chambre"] = SmartDevice("light_chambre", "Lumière Chambre", "light", "off")
        self.devices["thermostat"] = SmartDevice("thermo_1", "Chauffage", "thermostat", "22°C")
        self.devices["lock_entree"] = SmartDevice("lock_1", "Porte d'entrée", "lock", "locked")

    async def get_devices(self) -> list[dict]:
        return [d.to_dict() for d in self.devices.values()]

    async def control_device(self, device_id: str, command: str, value: Optional[str] = None) -> bool:
        device = self.devices.get(device_id)
        if not device:
            logger.warning(f"Appareil inconnu: {device_id}")
            return False
        if command == "on":
            device.status = "on"
        elif command == "off":
            device.status = "off"
        elif command == "toggle":
            device.status = "on" if device.status == "off" else "off"
        elif command == "set_temperature" and value:
            device.status = f"{value}°C"
        elif command in ("unlock", "lock"):
            device.status = command + "ed"
        logger.info(f"✓ {device_id} → {command} (status: {device.status})")
        return True

    async def get_device_status(self, device_id: str) -> Optional[str]:
        device = self.devices.get(device_id)
        return device.status if device else None


domotics_service: Optional[DomoticsService] = None


def init_domotics():
    global domotics_service
    domotics_service = DomoticsService()
    logger.info("✓ Domotics service initialisé (4 appareils mock)")
