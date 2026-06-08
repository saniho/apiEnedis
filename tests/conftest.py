"""HA module stubs for testing without homeassistant installed."""
import sys
from unittest.mock import MagicMock

_modules = {
    "homeassistant": MagicMock(),
    "homeassistant.const": MagicMock(),
    "homeassistant.core": MagicMock(),
    "homeassistant.util": MagicMock(),
    "homeassistant.components": MagicMock(),
    "homeassistant.config_entries": MagicMock(),
    "homeassistant.exceptions": MagicMock(),
    "homeassistant.helpers": MagicMock(),
    "homeassistant.helpers.typing": MagicMock(),
    "homeassistant.helpers.config_validation": MagicMock(),
    "homeassistant.helpers.restore_state": MagicMock(),
    "homeassistant.helpers.update_coordinator": MagicMock(),
    "homeassistant.components.sensor": MagicMock(),
}
for k, v in _modules.items():
    sys.modules[k] = v
