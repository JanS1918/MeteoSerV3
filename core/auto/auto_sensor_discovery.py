import asyncio
import json
import os
import ssl
import threading
import time
from typing import Any, Dict, Optional

from core.logger import get_logger

try:
    import serial
    from serial.tools import list_ports
except Exception:  # pragma: no cover
    serial = None
    list_ports = None

try:
    from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
except Exception:  # pragma: no cover
    Zeroconf = None
    ServiceBrowser = None
    ServiceStateChange = None

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover
    mqtt = None

try:
    from bleak import BleakScanner, BleakClient
except Exception:  # pragma: no cover
    BleakScanner = None
    BleakClient = None


ENV_SERVICE_UUID = "0000181A-0000-1000-8000-00805f9b34fb"
CHAR_TEMPERATURE = "00002A6E-0000-1000-8000-00805f9b34fb"
CHAR_HUMIDITY = "00002A6F-0000-1000-8000-00805f9b34fb"
CHAR_PRESSURE = "00002A6D-0000-1000-8000-00805f9b34fb"


class AutoSensorDiscovery:
    def __init__(
        self,
        system,
        mqtt_host: str = "127.0.0.1",
        mqtt_port: int = 8883,
        enable_mqtt: bool = True,
        enable_mdns: bool = True,
        enable_serial: bool = True,
        enable_ble: bool = True,
        mqtt_username: Optional[str] = None,
        mqtt_password: Optional[str] = None,
        mqtt_use_tls: bool = True,
        mqtt_ca_cert: Optional[str] = None,
        mqtt_client_cert: Optional[str] = None,
        mqtt_client_key: Optional[str] = None,
        mqtt_tls_insecure: bool = False,
    ):
        self.system = system
        self.log = get_logger("AutoSensorDiscovery")
        self._stop_event = threading.Event()
        self._threads = []
        self._zeroconf = None
        self._mqtt_client = None
        self._mqtt_host = mqtt_host
        self._mqtt_port = mqtt_port
        self._enable_mqtt = enable_mqtt
        self._enable_mdns = enable_mdns
        self._enable_serial = enable_serial
        self._enable_ble = enable_ble
        self._mqtt_username = mqtt_username
        self._mqtt_password = mqtt_password
        self._mqtt_use_tls = mqtt_use_tls
        self._mqtt_ca_cert = mqtt_ca_cert
        self._mqtt_client_cert = mqtt_client_cert
        self._mqtt_client_key = mqtt_client_key
        self._mqtt_tls_insecure = mqtt_tls_insecure

    async def start(self) -> None:
        if self._enable_mdns:
            self._start_mdns()
        if self._enable_mqtt:
            self._start_mqtt()
        if self._enable_serial:
            self._start_serial()
        if self._enable_ble and BleakScanner is not None:
            asyncio.create_task(self._ble_loop())

    def stop(self) -> None:
        self._stop_event.set()
        if self._mqtt_client is not None:
            try:
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
            except Exception:
                pass
        if self._zeroconf is not None:
            try:
                self._zeroconf.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _safe_float(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except Exception:
            return None

    def _canonical_name(self, nombre: str) -> Optional[str]:
        if not nombre:
            return None
        n = nombre.lower()
        n = n.replace("-", "_")
        if "icasa" in n and "co2" in n:
            return "co2"
        if "meter" in n and "co2" in n:
            return "co2"
        if "nddir" in n or "ndir" in n:
            return "co2"
        if "co2" in n:
            return "co2"
        if "carbon" in n and "dioxide" in n:
            return "co2"
        if "temp" in n or "temperatura" in n:
            return "temperatura"
        if "hum" in n or "humidity" in n:
            return "humedad"
        if "pres" in n or "pressure" in n or "baro" in n:
            return "presion"
        if "pm25" in n or "pm2" in n:
            return "pm25"
        if "wind" in n or "viento" in n:
            return "viento"
        if "rain" in n or "lluv" in n:
            return "lluvia"
        if "uv" in n:
            return "uv"
        if "light" in n or "luz" in n:
            return "luz"
        if "noise" in n or "ruido" in n:
            return "ruido"
        if "voc" in n:
            return "voc"
        if "pm10" in n:
            return "pm10"
        if "pm1" in n:
            return "pm1"
        return None

    def _normalize_value(
        self, canonical: Optional[str], value: Any, unit: Optional[str]
    ):
        try:
            v = float(value)
        except Exception:
            return value, unit
        if canonical == "temperatura":
            if unit and unit.upper() == "F":
                return (v - 32.0) * 5.0 / 9.0, "C"
            return v, "C"
        if canonical == "humedad":
            return v, "%"
        if canonical == "presion":
            if unit and unit.lower() == "inhg":
                return v * 33.8639, "hPa"
            return v, "hPa"
        if canonical == "viento":
            if unit and unit.lower() in ["mph"]:
                return v * 1.60934, "km/h"
            if unit and unit.lower() in ["m/s", "ms"]:
                return v * 3.6, "km/h"
            return v, "km/h"
        if canonical == "lluvia":
            if unit and unit.lower() in ["in", "inch", "in/hr", "in/h"]:
                return v * 25.4, "mm"
            return v, "mm"
        if canonical in ("pm25", "pm10", "pm1"):
            return v, "µg/m³"
        if canonical == "co2":
            return v, "ppm"
        return v, unit

    def _apply_reading(
        self,
        nombre: str,
        valor: Any,
        tipo: str,
        unidad: Optional[str],
        fuente: str,
        origen: str,
        fiabilidad: float = 85.0,
        map_to: Optional[str] = None,
    ) -> None:
        if unidad is None:
            canonical = map_to or self._canonical_name(nombre)
            if canonical == "temperatura":
                unidad = "C"
            elif canonical == "humedad":
                unidad = "%"
            elif canonical == "presion":
                unidad = "hPa"
            elif canonical in ("pm25", "pm10", "pm1"):
                unidad = "µg/m³"
            elif canonical == "co2":
                unidad = "ppm"
            elif canonical == "viento":
                unidad = "km/h"
            elif canonical == "lluvia":
                unidad = "mm"
        self.system.registrar_sensor_metadata(
            nombre,
            tipo=tipo,
            unidad=unidad,
            fuente=fuente,
            origen=origen,
            fiabilidad=fiabilidad,
        )
        self.system.actualizar_sensor(nombre, valor)
        if map_to is None:
            map_to = self._canonical_name(nombre)
        if map_to:
            try:
                norm_val, norm_unit = self._normalize_value(map_to, valor, unidad)
                if self.system.obtener_sensor(map_to) is None:
                    self.system.registrar_sensor_metadata(
                        map_to,
                        tipo=tipo,
                        unidad=norm_unit,
                        fuente=fuente,
                        origen=origen,
                        fiabilidad=fiabilidad,
                    )
                    self.system.actualizar_sensor(map_to, norm_val)
                else:
                    self.system.actualizar_sensor(map_to, norm_val)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # MQTT
    # ------------------------------------------------------------------
    def _start_mqtt(self) -> None:
        if mqtt is None:
            self.log.warning("MQTT no disponible: instala paho-mqtt")
            return

        def _on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("meteoser/sensors/#")
                client.subscribe("sensors/#")
                self.log.info(
                    "MQTT conectado y suscrito a meteoser/sensors/# y sensors/#"
                )
            else:
                self.log.warning(f"MQTT error conexión: {rc}")

        def _on_message(client, userdata, msg):
            payload = msg.payload.decode("utf-8", errors="ignore")
            topic = msg.topic
            try:
                data = json.loads(payload)
                self._ingest_payload(data, fuente="mqtt", origen="externo")
                return
            except Exception:
                pass
            # fallback: key=value
            if "=" in payload:
                parts = payload.split("=")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    value = "=".join(parts[1:]).strip()
                    self._apply_reading(
                        name, value, name, None, "mqtt", "externo", 80.0
                    )
                    return
            # fallback: topic-based name
            name = topic.split("/")[-1]
            val = self._safe_float(payload) if payload else payload
            if name:
                self._apply_reading(name, val, name, None, "mqtt", "externo", 80.0)

        self._mqtt_client = mqtt.Client()
        if self._mqtt_username:
            self._mqtt_client.username_pw_set(self._mqtt_username, self._mqtt_password)

        if self._mqtt_use_tls:
            tls_kwargs = {
                "cert_reqs": ssl.CERT_REQUIRED,
                "tls_version": ssl.PROTOCOL_TLS_CLIENT,
            }
            if self._mqtt_ca_cert and os.path.exists(self._mqtt_ca_cert):
                tls_kwargs["ca_certs"] = self._mqtt_ca_cert
            else:
                self.log.warning(
                    "TLS habilitado pero no se encontró METEOSER_MQTT_TLS_CA; usando CA del sistema"
                )
            if self._mqtt_client_cert and self._mqtt_client_key:
                if os.path.exists(self._mqtt_client_cert) and os.path.exists(
                    self._mqtt_client_key
                ):
                    tls_kwargs["certfile"] = self._mqtt_client_cert
                    tls_kwargs["keyfile"] = self._mqtt_client_key
                else:
                    self.log.warning(
                        "Certificados cliente MQTT no encontrados; continuando sin auth mutua"
                    )
            self._mqtt_client.tls_set(**tls_kwargs)
            self._mqtt_client.tls_insecure_set(self._mqtt_tls_insecure)
            self.log.info(
                "MQTT TLS habilitado (ca=%s, mutual=%s)",
                self._mqtt_ca_cert or "system",
                bool(self._mqtt_client_cert and self._mqtt_client_key),
            )

        self._mqtt_client.on_connect = _on_connect
        self._mqtt_client.on_message = _on_message

        def _mqtt_connect_loop():
            backoff = 5
            while not self._stop_event.is_set():
                try:
                    if self._mqtt_client is None:
                        return
                    self._mqtt_client.connect(self._mqtt_host, self._mqtt_port, 60)
                    self._mqtt_client.loop_start()
                    self.log.info("MQTT conectado (reconectado)")
                    return
                except Exception as exc:
                    self.log.warning(
                        f"MQTT no disponible en {self._mqtt_host}:{self._mqtt_port}: {exc}"
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)

        t = threading.Thread(target=_mqtt_connect_loop, daemon=True)
        self._threads.append(t)
        t.start()

    def _ingest_payload(self, data: Dict[str, Any], fuente: str, origen: str) -> None:
        if not isinstance(data, dict):
            return
        readings = data.get("readings")
        if isinstance(readings, list):
            for item in readings:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or item.get("sensor")
                value = item.get("value")
                if name is None:
                    continue
                tipo = item.get("type") or name
                unidad = item.get("unit")
                fiabilidad = item.get("reliability", 85.0)
                map_to = item.get("map_to")
                self._apply_reading(
                    name, value, tipo, unidad, fuente, origen, fiabilidad, map_to
                )
            return

        name = data.get("name") or data.get("sensor")
        value = data.get("value")
        if name is None:
            return
        tipo = data.get("type") or name
        unidad = data.get("unit")
        fiabilidad = data.get("reliability", 85.0)
        map_to = data.get("map_to")
        self._apply_reading(
            name, value, tipo, unidad, fuente, origen, fiabilidad, map_to
        )

    # ------------------------------------------------------------------
    # mDNS
    # ------------------------------------------------------------------
    def _start_mdns(self) -> None:
        if Zeroconf is None or ServiceBrowser is None:
            self.log.warning("mDNS no disponible: instala zeroconf")
            return

        from zeroconf._exceptions import BadTypeInNameException

        class Listener:
            def __init__(self, outer):
                self.outer = outer

            def remove_service(self, zeroconf, service_type, name):
                pass

            def update_service(self, zeroconf, service_type, name):
                # Método requerido por zeroconf >=0.62.0
                pass

            def add_service(self, zeroconf, service_type, name):
                try:
                    info = zeroconf.get_service_info(service_type, name)
                except BadTypeInNameException as exc:
                    # No es necesario mostrar como WARNING porque ocurre frecuentemente en redes
                    self.outer.log.debug(
                        f"mDNS BadTypeInNameException: {exc} (service_type={service_type}, name={name})"
                    )
                    return
                except Exception as exc:
                    self.outer.log.warning(
                        f"mDNS error inesperado: {exc} (service_type={service_type}, name={name})"
                    )
                    return
                if not info:
                    return
                # Filtrar servicios comunes y solo registrar si parece un sensor/dispositivo relevante
                lname = (name or "").lower()
                allowed = (
                    "ecowitt",
                    "wh",
                    "meteohub",
                    "weather",
                    "sensor",
                    "meteo",
                    "esp",
                    "node",
                    "ble",
                    "co2",
                    "airvisual",
                    "netatmo",
                )
                if not any(k in lname for k in allowed):
                    self.outer.log.debug(
                        f"mDNS servicio ignorado: {name} (type={service_type})"
                    )
                    return
                servicio = name.replace(".", "_")
                self.outer.system.registrar_sensor_metadata(
                    servicio,
                    tipo="mdns_service",
                    unidad=None,
                    fuente="mdns",
                    origen="lan",
                    fiabilidad=70.0,
                )

        self._zeroconf = Zeroconf()
        self._threads.append(
            threading.Thread(
                target=lambda: ServiceBrowser(
                    self._zeroconf, "_services._dns-sd._udp.local.", Listener(self)
                ),
                daemon=True,
            )
        )
        self._threads[-1].start()

    # ------------------------------------------------------------------
    # SERIAL
    # ------------------------------------------------------------------
    def _start_serial(self) -> None:
        if serial is None or list_ports is None:
            self.log.warning("Serial no disponible: instala pyserial")
            return

        def _serial_loop():
            baud_rates = [9600, 115200]
            opened = {}
            while not self._stop_event.is_set():
                ports = [p.device for p in list_ports.comports()]
                for port in ports:
                    if port in opened:
                        continue
                    for baud in baud_rates:
                        try:
                            ser = serial.Serial(port, baudrate=baud, timeout=1)
                            opened[port] = ser
                            self.system.registrar_sensor_metadata(
                                f"serial_{port}",
                                tipo="serial_device",
                                unidad=None,
                                fuente="serial",
                                origen="usb",
                                fiabilidad=75.0,
                            )
                            break
                        except Exception:
                            continue
                # read lines
                for port, ser in list(opened.items()):
                    try:
                        line = ser.readline().decode("utf-8", errors="ignore").strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            self._ingest_payload(data, fuente="serial", origen="usb")
                            continue
                        except Exception:
                            pass
                        if "=" in line:
                            key, value = line.split("=", 1)
                            self._apply_reading(
                                key.strip(),
                                value.strip(),
                                key.strip(),
                                None,
                                "serial",
                                "usb",
                                75.0,
                            )
                    except Exception:
                        continue
                time.sleep(2)

        t = threading.Thread(target=_serial_loop, daemon=True)
        self._threads.append(t)
        t.start()

    # ------------------------------------------------------------------
    # BLE
    # ------------------------------------------------------------------
    async def _ble_loop(self) -> None:
        if BleakScanner is None:
            return
        while not self._stop_event.is_set():
            try:
                devices = await BleakScanner.discover(timeout=10.0)
                for device in devices:
                    name = device.name or device.address
                    self.system.registrar_sensor_metadata(
                        f"ble_{device.address}",
                        tipo="ble_device",
                        unidad=None,
                        fuente="ble",
                        origen="bluetooth",
                        fiabilidad=70.0,
                    )
                    if device.metadata and "uuids" in device.metadata:
                        if ENV_SERVICE_UUID.lower() not in [
                            u.lower() for u in device.metadata["uuids"]
                        ]:
                            continue
                    await self._ble_read_env(device.address, name)
            except Exception:
                pass
            await asyncio.sleep(30)

    async def _ble_read_env(self, address: str, name: str) -> None:
        if BleakClient is None:
            return
        try:
            async with BleakClient(address, timeout=10.0) as client:
                if not client.is_connected:
                    return
                # Temperature (0.01 deg C)
                if await client.is_connected():
                    if await client.get_services():
                        if CHAR_TEMPERATURE in client.services.characteristics:
                            raw = await client.read_gatt_char(CHAR_TEMPERATURE)
                            if raw:
                                temp = (
                                    int.from_bytes(raw, byteorder="little", signed=True)
                                    / 100.0
                                )
                                self._apply_reading(
                                    f"temperatura_ble_{address}",
                                    temp,
                                    "temperatura",
                                    "C",
                                    "ble",
                                    "bluetooth",
                                    80.0,
                                    map_to="temperatura",
                                )
                        if CHAR_HUMIDITY in client.services.characteristics:
                            raw = await client.read_gatt_char(CHAR_HUMIDITY)
                            if raw:
                                hum = (
                                    int.from_bytes(
                                        raw, byteorder="little", signed=False
                                    )
                                    / 100.0
                                )
                                self._apply_reading(
                                    f"humedad_ble_{address}",
                                    hum,
                                    "humedad",
                                    "%",
                                    "ble",
                                    "bluetooth",
                                    80.0,
                                    map_to="humedad",
                                )
                        if CHAR_PRESSURE in client.services.characteristics:
                            raw = await client.read_gatt_char(CHAR_PRESSURE)
                            if raw:
                                pres = (
                                    int.from_bytes(
                                        raw, byteorder="little", signed=False
                                    )
                                    / 10.0
                                )
                                self._apply_reading(
                                    f"presion_ble_{address}",
                                    pres,
                                    "presion",
                                    "hPa",
                                    "ble",
                                    "bluetooth",
                                    80.0,
                                    map_to="presion",
                                )
        except Exception:
            return
