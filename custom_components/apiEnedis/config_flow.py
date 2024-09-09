""" Config flow """
import logging
import uuid

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (  # isort:skip
    DOMAIN,
    CONF_TOKEN,
    CONF_CODE,
    CONF_SERVICE_ENEDIS,
    HC_COST,
    HP_COST,
    HEURESCREUSES_ON,
    HEURES_CREUSES,
    _ENEDIS_EnedisGateway,
    _ENEDIS_MyElectricData,
)


_LOGGER = logging.getLogger(__name__)
all_repos_Gateway = [_ENEDIS_EnedisGateway, _ENEDIS_MyElectricData]


class myEnedisFlowHandler(  # type: ignore[call-arg]
    config_entries.ConfigFlow, domain=DOMAIN
):

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        self._errors = {}
        self._data = {}
        self._data["unique_id"] = str(uuid.uuid4())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return myEnedisOptionsFlowHandler(config_entry)

    @callback
    def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form to the user."""

        if user_input is None:
            user_input = {}
        token = ""
        code = ""
        serviceEnedis = "enedisGateway"
        val_hc_cost = "0.0"
        val_hp_cost = "0.0"
        val_heures_creuses = ""
        val_heurescreuses_on = True
        all_repos = all_repos_Gateway
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERVICE_ENEDIS,
                    default=user_input.get(CONF_SERVICE_ENEDIS, serviceEnedis),
                ): vol.In(all_repos),
                vol.Required(
                    CONF_TOKEN, default=user_input.get(CONF_TOKEN, token)
                ): str,
                vol.Required(CONF_CODE, default=user_input.get(CONF_CODE, code)): str,
                vol.Optional(
                    HC_COST, default=user_input.get(HC_COST, val_hc_cost)
                ): cv.string,
                vol.Optional(
                    HP_COST, default=user_input.get(HP_COST, val_hp_cost)
                ): cv.string,
                vol.Optional(
                    HEURESCREUSES_ON,
                    default=user_input.get(HEURESCREUSES_ON, val_heurescreuses_on),
                ): cv.boolean,
                vol.Optional(
                    HEURES_CREUSES,
                    default=user_input.get(HEURES_CREUSES, val_heures_creuses),
                ): cv.string,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):  # pylint: disable=unused-argument
        self._errors = {}
        if user_input is None:
            return self._show_setup_form(user_input, self._errors)

        token = user_input[CONF_TOKEN]  # Might be a city name or a postal code
        code = user_input.get(CONF_CODE)
        serviceEnedis = user_input.get(CONF_SERVICE_ENEDIS)
        hc_cost = user_input.get(HC_COST)
        hp_cost = user_input.get(HP_COST)
        heures_creuses_on = user_input.get(HEURESCREUSES_ON)
        heures_creuses = user_input.get(HEURES_CREUSES)

        # Check if already configured
        await self.async_set_unique_id(f"{code}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=code,
            data={
                CONF_TOKEN: token,
                CONF_CODE: code,
                CONF_SERVICE_ENEDIS: serviceEnedis,
                HC_COST: hc_cost,
                HP_COST: hp_cost,
                HEURESCREUSES_ON: heures_creuses_on,
                HEURES_CREUSES: heures_creuses,
            },
        )

    async def async_step_import(self, user_input):
        """Import a config entry."""
        return await self.async_step_user(user_input)


class myEnedisOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._data = {}
        self._data["unique_id"] = config_entry.options.get("unique_id")

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        token = "monToken"
        code = "monCode"
        serviceEnedis = "enedisGateway"
        val_heures_creuses = ""
        all_repos = all_repos_Gateway

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERVICE_ENEDIS,
                    default=self.config_entry.options.get(CONF_SERVICE_ENEDIS,
                                                          serviceEnedis),
                ): vol.In(all_repos),
                vol.Required(
                    CONF_TOKEN,
                    default=self.config_entry.options.get(CONF_TOKEN, token),
                ): str,
                vol.Required(
                    CONF_CODE,
                    default=self.config_entry.options.get(CONF_CODE, code),
                ): str,
                vol.Optional(
                    HC_COST,
                    default=self.config_entry.options.get(HC_COST, "0.0"),
                ): cv.string,
                vol.Optional(
                    HP_COST,
                    default=self.config_entry.options.get(HP_COST, "0.0"),
                ): cv.string,
                vol.Optional(
                    HEURESCREUSES_ON,
                    default=self.config_entry.options.get(HEURESCREUSES_ON, True),
                ): cv.boolean,
                vol.Optional(
                    HEURES_CREUSES,
                    default=self.config_entry.options.get(
                        HEURES_CREUSES, val_heures_creuses
                    ),
                ): cv.string,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
