"""
Support for reading SmartMeter data through Eneco's Toon thermostats.
Only works for rooted Toon.

configuration.yaml

sensor:
  - platform: toon_smartmeter
    host: IP_ADDRESS
    port: 10080
    scan_interval: 10
    resources:
      - gasused
      - gasusedcnt
      - elecusageflowlow
      - elecusagecntlow
      - elecusageflowhigh
      - elecusagecnthigh
      - elecprodflowlow
      - elecprodcntlow
      - elecprodflowhigh
      - elecprodcnthigh
"""
import logging
from datetime import timedelta
import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_RESOURCES)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

BASE_URL = 'http://{0}:{1}{2}'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

SENSOR_PREFIX = 'P1 '

SENSOR_TYPES = {
    'gasused': ['Gas Used Last Hour', 'm3', 'mdi:fire'],
    'gasusedcnt': ['Gas Used Cnt', 'm3', 'mdi:fire'],
    'elecusageflowlow': ['Power Use Low', 'Watt', 'mdi:flash'],
    'elecusageflowhigh': ['Power Use High', 'Watt', 'mdi:flash'],
    'elecprodflowlow': ['Power Prod Low', 'Watt', 'mdi:flash'],
    'elecprodflowhigh': ['Power Prod High', 'Watt', 'mdi:flash'],
    'elecusagecntlow': ['Power Use Cnt Low', 'kWh', 'mdi:flash'],
    'elecusagecnthigh': ['Power Use Cnt High', 'kWh', 'mdi:flash'],
    'elecprodcntlow': ['Power Prod Cnt Low', 'kWh', 'mdi:flash'],
    'elecprodcnthigh': ['Power Prod Cnt High', 'kWh', 'mdi:flash'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=10800): cv.positive_int,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Toon smartmeter sensors."""
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    try:
        data = ToonData(host, port)
    except requests.exceptions.HTTPError as error:
        _LOGGER.error(error)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:flash']

        entities.append(ToonSmartMeterSensor(data, sensor_type))

    add_entities(entities)


# pylint: disable=abstract-method
class ToonData(object):
    """Representation of a Toon thermostat."""

    def __init__(self, host, port):
        """Initialize the thermostat."""
        self._host = host
        self._port = port
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the thermostat."""
        try:
            self.data = requests.get(BASE_URL.format(self._host, self._port, '/hdrv_zwave?action=getDevices.json'), timeout=5).json()
            _LOGGER.debug("Data = %s", self.data)
        except requests.exceptions.RequestException:
            _LOGGER.error("Error occurred while fetching data.")
            self.data = None
            return False

 
class ToonSmartMeterSensor(Entity):
    """Representation of a SmartMeter connected to Toon."""

    def __init__(self, data, sensor_type):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[self.type][0]
        self._unit = SENSOR_TYPES[self.type][1]
        self._icon = SENSOR_TYPES[self.type][2]
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor. (total/current power consumption/production or total gas used)"""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        self.data.update()
        energy = self.data.data

        if self.type == 'gasused':
            self._state = float(energy["dev_6.1"]["CurrentGasFlow"])/100
        elif self.type == 'gasusedcnt':
            self._state = float(energy["dev_6.1"]["CurrentGasQuantity"])/1000

        elif self.type == 'elecusageflowlow':
            self._state = energy["dev_6.5"]["CurrentElectricityFlow"]
        elif self.type == 'elecusagecntlow':
            self._state = float(energy["dev_6.5"]["CurrentElectricityQuantity"])/1000

        elif self.type == 'elecusageflowhigh':
            self._state = energy["dev_6.3"]["CurrentElectricityFlow"]
        elif self.type == 'elecusagecnthigh':
            self._state = float(energy["dev_6.3"]["CurrentElectricityQuantity"])/1000

        elif self.type == 'elecprodflowlow':
            self._state = energy["dev_6.6"]["CurrentElectricityFlow"]
        elif self.type == 'elecprodcntlow':
            self._state = float(energy["dev_6.6"]["CurrentElectricityQuantity"])/1000

        elif self.type == 'elecprodflowhigh':
            self._state = energy["dev_6.4"]["CurrentElectricityFlow"]
        elif self.type == 'elecprodcnthigh':
            self._state = float(energy["dev_6.4"]["CurrentElectricityQuantity"])/1000
