"""Tests for coordinator entities (requires homeassistant)."""
import pytest

pytest.importorskip("homeassistant")

from homeassistant.util import dt as dt_util

from custom_components.myEnedis.base_enedis_coordinator import (
    BaseEnedisCoordinatorEntity,
)


class FakeCoordinator:
    """Minimal mock coordinator."""
    def __init__(self):
        self.data = {}
        self.config_entry_id = "test_entry"
        self.api = None


class FakeSensorDescription:
    key = "test_key"
    name = "Test Sensor"
    icon = "mdi:test"
    native_unit_of_measurement = "kWh"
    device_class = None
    state_class = None


class ConcreteEntity(BaseEnedisCoordinatorEntity):
    entity_domain = "sensor"

    def __init__(self, coordinator, sensor_description, pdl_id):
        super().__init__(coordinator, sensor_description, pdl_id)
        self.entity_id = f"{self.entity_domain}.{pdl_id}_{sensor_description.key}"

    def _update_state(self, data):
        return 42

    @property
    def unique_id(self):
        return f"{self._pdl_id}_{self.sensor_description.key}"

    @property
    def name(self):
        return self.sensor_description.name


class TestBaseEnedisCoordinatorEntity:
    def test_init(self):
        coord = FakeCoordinator()
        desc = FakeSensorDescription()
        entity = ConcreteEntity(coord, desc, "20000000000000")

        assert entity._pdl_id == "20000000000000"
        assert entity.sensor_description == desc
        assert entity.coordinator == coord
        assert entity.unique_id == "20000000000000_test_key"
        assert entity.name == "Test Sensor"

    def test_native_value_updates_from_coordinator(self):
        coord = FakeCoordinator()
        coord.data = {"meter_reading": {"interval_reading": [{"value": "100"}]}}
        desc = FakeSensorDescription()
        entity = ConcreteEntity(coord, desc, "20000000000000")

        entity._handle_coordinator_update()
        assert entity.native_value == 42

    def test_native_unit_of_measurement(self):
        coord = FakeCoordinator()
        desc = FakeSensorDescription()
        entity = ConcreteEntity(coord, desc, "20000000000000")

        assert entity.native_unit_of_measurement == "kWh"

    def test_icon_from_description(self):
        coord = FakeCoordinator()
        desc = FakeSensorDescription()
        entity = ConcreteEntity(coord, desc, "20000000000000")

        assert entity.icon == "mdi:test"

    def test_available_without_coordinator_data(self):
        coord = FakeCoordinator()
        coord.data = None
        desc = FakeSensorDescription()
        entity = ConcreteEntity(coord, desc, "20000000000000")

        assert entity.available is True
