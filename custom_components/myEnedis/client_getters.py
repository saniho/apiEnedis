"""Trivial data getters for myClientEnedis - no HA dependency."""


def get_version(client):
    return client._version


def get_update_realise(client):
    return client._updateRealise


def get_service_enedis(client):
    return client._serviceEnedis


def get_yesterday(client):
    return client._yesterday


def get_yesterday_last_year(client):
    return client._yesterdayLastYear


def get_yesterday_consumption_max_power(client):
    return client._yesterdayConsumptionMaxPower


def get_production_yesterday(client):
    return client._productionYesterday


def get_yesterday_hchp(client):
    return client._yesterdayHCHP


def get_last_month(client):
    return client._lastMonth


def get_last_month_last_year(client):
    return client._lastMonthLastYear


def get_last_week(client):
    return client._lastWeek


def get_last_7_days(client):
    return client._last7Days


def get_last_7_days_details(client):
    return client._last7DaysDetails


def get_current_week(client):
    return client._currentWeek


def get_current_week_last_year(client):
    return client._currentWeekLastYear


def get_current_month_last_year(client):
    return client._currentMonthLastYear


def get_current_month(client):
    return client._currentMonth


def get_last_year(client):
    return client._lastYear


def get_current_year(client):
    return client._currentYear


def get_ecowatt(client):
    return client._ecoWatt


def get_tempo(client):
    return client._tempo


def get_last_update(client):
    return client._lastUpdate


def get_time_last_call(client):
    return client._timeLastUpdate


def get_status_last_call(client):
    return client._statusLastCall


def get_nb_call(client):
    return client._nbCall


def get_error_last_call(client):
    return client._errorLastCall


def get_delay_error(client):
    return client._delay


def get_git_version(client):
    return client._gitVersion


def get_path_archive(client):
    return client._path


def get_hc_cost(client, val):
    return val * client._heuresCreusesCost


def get_hp_cost(client, val):
    return val * client._heuresPleinesCost
