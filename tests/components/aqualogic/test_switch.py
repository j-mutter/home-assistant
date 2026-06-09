"""Tests for the AquaLogic switch platform."""

from unittest.mock import MagicMock

from aqualogic.core import States
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.aqualogic.const import UPDATE_TOPIC
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, Platform, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from tests.common import MockConfigEntry, snapshot_platform


@pytest.fixture
def platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return [Platform.SWITCH]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_switches(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    mock_processor: MagicMock,
) -> None:
    """Test switch entities are created and report correct state."""
    async_dispatcher_send(hass, UPDATE_TOPIC)
    await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)


@pytest.mark.usefixtures("init_integration")
@pytest.mark.parametrize(
    ("service", "expected_state"),
    [
        pytest.param(SERVICE_TURN_ON, True, id="turn_on"),
        pytest.param(SERVICE_TURN_OFF, False, id="turn_off"),
    ],
)
async def test_turn(
    hass: HomeAssistant,
    mock_panel: MagicMock,
    service: str,
    expected_state: bool,
) -> None:
    """Test turning a switch on/off calls set_state on the panel."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        service,
        {ATTR_ENTITY_ID: "switch.aqualogic_lights"},
        blocking=True,
    )
    mock_panel.set_state.assert_called_once_with(States.LIGHTS, expected_state)
