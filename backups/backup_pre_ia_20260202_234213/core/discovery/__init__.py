"""
Discovery Module: Omnipotent Hardware Detection System V1.5
Detecta sensores por cualquier medio: USB/Serial, Bluetooth, WiFi, mDNS, Zigbee
"""

from .universal_scanner import UniversalHardwareScanner
from .driver_installer import DriverInstaller as DriverAutoInstaller
from .omnipotence_manager import OmnipotenceManager

__all__ = ['UniversalHardwareScanner', 'DriverAutoInstaller', 'OmnipotenceManager']
from .universal_orchestrator import UniversalOrchestrator

__all__ = [
    'USBScanner',
    'BLEScanner',
    'mDNSScanner',
    'DriverInstaller',
    'SensorAssimilator',
    'UniversalOrchestrator'
]
