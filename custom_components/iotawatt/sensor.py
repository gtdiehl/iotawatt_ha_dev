"""Support for IoTaWatt Energy monitor."""
import logging

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_WATT_HOUR,
    POWER_WATT,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt

from . import IotaWattEntity
from .const import COORDINATOR, DOMAIN, SIGNAL_ADD_DEVICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    entities = []

    for idx, ent in enumerate(coordinator.data["sensors"]):
        entity = IotaWattSensor(
            coordinator=coordinator,
            entity=ent,
            mac_address=coordinator.data["sensors"][ent].hub_mac_address,
            name=coordinator.data["sensors"][ent].getName(),
        )
        entities.append(entity)

    async_add_entities(entities)

    async def async_new_entities(sensor_info):
        """Remove an entity."""
        ent = sensor_info["entity"]
        hub_mac_address = sensor_info["mac_address"]
        name = sensor_info["name"]

        entity = IotaWattSensor(
            coordinator=coordinator,
            entity=ent,
            mac_address=hub_mac_address,
            name=name,
        )
        entities = [entity]
        async_add_entities(entities)

    async_dispatcher_connect(hass, SIGNAL_ADD_DEVICE, async_new_entities)


class IotaWattSensor(IotaWattEntity):
    """Defines a IoTaWatt Energy Sensor."""

    def __init__(self, coordinator, entity, mac_address, name):
        """Initialize the sensor."""
        super().__init__(
            coordinator=coordinator, entity=entity, mac_address=mac_address, name=name
        )

        sensor = self.coordinator.data["sensors"][entity]
        self._ent = entity
        self._name = name
        self._io_type = sensor.getType()
        self._state = None
        self._attr_state_class = STATE_CLASS_MEASUREMENT

        unit = sensor.getUnit()
        if unit == "Watts":
            self._attr_unit_of_measurement = POWER_WATT
            self._attr_device_class = DEVICE_CLASS_POWER
        elif unit == "WattHours":
            self._attr_unit_of_measurement = ENERGY_WATT_HOUR
            self._attr_device_class = DEVICE_CLASS_ENERGY
        elif unit == "Volts":
            self._attr_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT
            self._attr_device_class = DEVICE_CLASS_VOLTAGE
        else:
            self._attr_unit_of_measurement = unit

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        if self._io_type == "Input":
            channel = self.coordinator.data["sensors"][self._ent].getChannel()
        else:
            channel = "N/A"

        attrs = {"type": self._io_type, "channel": channel}

        if last_reset := self.last_reset:
            attrs["last_reset"] = last_reset.isoformat()
        return attrs

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["sensors"][self._ent].getValue()

    @property
    def last_reset(self):
        """Return the time when the sensor was last reset, if any."""
        last_reset = self.coordinator.data["sensors"][self._ent].getBegin()
        if last_reset is None:
            return None
        return dt.parse_datetime(last_reset)

    @property
    def name(self):
        """Return the name of the sensor."""
        name = (
            "IoTaWatt "
            + str(self._io_type)
            + " "
            + str(self.coordinator.data["sensors"][self._ent].getName())
        )
        return name

    @property
    def unique_id(self) -> str:
        """Return the Uniqie ID for the sensor."""
        return self.coordinator.data["sensors"][self._ent].getSensorID()