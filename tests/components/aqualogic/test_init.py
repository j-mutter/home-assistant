"""Tests for the AquaLogic integration setup."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from homeassistant.components.aqualogic import AquaLogicProcessor
from homeassistant.components.aqualogic.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_load_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_processor: MagicMock,
) -> None:
    """Test loading and unloading the config entry starts and stops the processor."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    mock_processor.start.assert_called_once()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_processor.shutdown.assert_called_once()


async def test_shutdown_on_homeassistant_stop(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_processor: MagicMock,
) -> None:
    """Test the processor shuts down when Home Assistant stops."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    mock_processor.shutdown.assert_called_once()


async def test_processor_run_reconnects(hass: HomeAssistant) -> None:
    """Test the processor reconnects after a dropped connection."""
    processor = AquaLogicProcessor(hass, "1.2.3.4", 8899)

    connect_calls = 0

    def stop_on_second_connect(*args: object, **kwargs: object) -> None:
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls >= 2:
            processor._shutdown = True

    with (
        patch("homeassistant.components.aqualogic.RECONNECT_INTERVAL", timedelta(0)),
        patch("homeassistant.components.aqualogic.AquaLogic") as mock_al,
    ):
        mock_al.return_value.connect.side_effect = stop_on_second_connect
        processor.run()

    assert connect_calls == 2


async def test_import_from_yaml(
    hass: HomeAssistant,
    mock_processor: MagicMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test importing from YAML creates a config entry and a deprecation issue."""
    with patch(
        "homeassistant.components.aqualogic.config_flow._can_connect",
        return_value=True,
    ):
        assert await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {CONF_HOST: "1.2.3.4", CONF_PORT: 8899}},
        )
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].data == {CONF_HOST: "1.2.3.4", CONF_PORT: 8899}

    issue = issue_registry.async_get_issue(
        HOMEASSISTANT_DOMAIN, f"deprecated_yaml_{DOMAIN}"
    )
    assert issue is not None
    assert issue.issue_domain == DOMAIN
