"""Test opentherm_gw select entities."""

from unittest.mock import AsyncMock, MagicMock

from pyotgw.vars import OTGW_GPIO_A, OTGW_GPIO_B
import pytest

from homeassistant.components.opentherm_gw import DOMAIN as OPENTHERM_DOMAIN
from homeassistant.components.opentherm_gw.const import (
    DATA_GATEWAYS,
    DATA_OPENTHERM_GW,
    OpenThermDeviceIdentifier,
)
from homeassistant.components.opentherm_gw.select import (
    OpenThermSelectGPIOMode,
    PyotgwGPIOMode,
)
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID, CONF_ID, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from tests.common import MockConfigEntry


@pytest.mark.parametrize(
    ("entity_key", "gpio_id"),
    [
        (OTGW_GPIO_A, "A"),
        (OTGW_GPIO_B, "B"),
    ],
)
async def test_gpio_mode_select(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_pyotgw: MagicMock,
    entity_key: str,
    gpio_id: str,
) -> None:
    """Test GPIO mode selector."""

    mock_pyotgw.return_value.set_gpio_mode = AsyncMock(return_value=PyotgwGPIOMode.VCC)
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        select_entity_id := entity_registry.async_get_entity_id(
            SELECT_DOMAIN,
            OPENTHERM_DOMAIN,
            f"{mock_config_entry.data[CONF_ID]}-{OpenThermDeviceIdentifier.GATEWAY}-{entity_key}",
        )
    ) is not None
    assert hass.states.get(select_entity_id).state == STATE_UNKNOWN

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: select_entity_id, ATTR_OPTION: OpenThermSelectGPIOMode.VCC},
        blocking=True,
    )
    assert hass.states.get(select_entity_id).state == OpenThermSelectGPIOMode.VCC

    mock_pyotgw.return_value.set_gpio_mode.assert_awaited_once_with(
        gpio_id, PyotgwGPIOMode.VCC.value
    )


@pytest.mark.parametrize(
    ("entity_key"),
    [
        (OTGW_GPIO_A),
        (OTGW_GPIO_B),
    ],
)
async def test_gpio_mode_state_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_pyotgw: MagicMock,
    entity_key: str,
) -> None:
    """Test GPIO mode selector."""

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        select_entity_id := entity_registry.async_get_entity_id(
            SELECT_DOMAIN,
            OPENTHERM_DOMAIN,
            f"{mock_config_entry.data[CONF_ID]}-{OpenThermDeviceIdentifier.GATEWAY}-{entity_key}",
        )
    ) is not None
    assert hass.states.get(select_entity_id).state == STATE_UNKNOWN

    gw_hub = hass.data[DATA_OPENTHERM_GW][DATA_GATEWAYS][
        mock_config_entry.data[CONF_ID]
    ]
    async_dispatcher_send(
        hass,
        gw_hub.update_signal,
        {
            OpenThermDeviceIdentifier.BOILER: {},
            OpenThermDeviceIdentifier.GATEWAY: {entity_key: 4},
            OpenThermDeviceIdentifier.THERMOSTAT: {},
        },
    )
    await hass.async_block_till_done()

    assert hass.states.get(select_entity_id).state == OpenThermSelectGPIOMode.LED_F
