"""Call orchestration for myClientEnedis - no HA dependency."""
from __future__ import annotations

import datetime
import logging
import sys
import traceback

try:
    from .const import __nameMyEnedis__, _ENEDIS_MyElectricData
except ImportError:
    from const import __nameMyEnedis__, _ENEDIS_MyElectricData  # type: ignore[no-redef]

from .exceptions import EnedisApiError, EnedisAuthError, EnedisDataError

log = logging.getLogger(__nameMyEnedis__)


def get_call_possible(client, trace=False):
    currentDateTime = datetime.datetime.now()

    horairePossible = client.getHorairePossible()
    lastCallHier = client.getLastCallHier()
    timeLastCall = client.getTimeLastCall()
    statusLastCall = client.getStatusLastCall()
    delayIsGood = client.getDelayIsGoodAfterError(currentDateTime)

    callpossible = horairePossible and (
        lastCallHier
        or (timeLastCall is None)
        or (statusLastCall is False and delayIsGood)
    )

    if client._forceCallJson:
        callpossible = True

    level = logging.ERROR if trace else logging.INFO
    log.log(
        level,
        "myEnedis ...callPossible=%s horaire=%s lastCallHier=%s timeLastCall=%s statusLastCall=%s delayIsGood=%s force=%s",
        callpossible,
        horairePossible,
        lastCallHier,
        timeLastCall,
        statusLastCall,
        delayIsGood,
        client._forceCallJson,
    )
    return callpossible


def call_consommation(client):
    if client.isConsommation():
        client._niemeAppel += 1
        _run_if_needed(client, "updateYesterday", client.updateYesterday)
        _run_if_needed(client, "updateCurrentWeek", client.updateCurrentWeek)
        _run_if_needed(client, "updateLastWeek", client.updateLastWeek)
        _run_if_needed(client, "updateLast7Days", client.updateLast7Days)
        _run_if_needed(client, "updateDataYesterdayHCHP", client.updateDataYesterdayHCHP)
        _run_if_needed(client, "updateLast7DaysDetails", client.updateLast7DaysDetails)
        _run_if_needed(client, "updateCurrentMonth", client.updateCurrentMonth)
        _run_if_needed(client, "updateLastMonth", client.updateLastMonth)
        _run_if_needed(client, "updateLastMonthLastYear", client.updateLastMonthLastYear)
        _run_if_needed(client, "updateCurrentYear", client.updateCurrentYear)
        _run_if_needed(client, "updateLastYear", client.updateLastYear)
        _run_if_needed(client, "updateYesterdayLastYear", client.updateYesterdayLastYear)
        _run_if_needed(client, "updateCurrentWeekLastYear", client.updateCurrentWeekLastYear)
        _run_if_needed(
            client,
            "updateYesterdayConsumptionMaxPower",
            client.updateYesterdayConsumptionMaxPower,
        )
        _run_if_needed(
            client,
            "updateCurrentMonthLastYear",
            client.updateCurrentMonthLastYear,
        )

        if not client._forceCallJson:
            client.updateTimeLastCall()
        client.updateStatusLastCall(True)
        log.info("mise à jour effectuee consommation")


def call_production(client):
    if client.isProduction():
        _run_if_needed(client, "updateYesterdayProduction", client.updateYesterdayProduction)
        client.updateTimeLastCall()
        client.updateStatusLastCall(True)
        log.info("mise à jour effectuee production")


def call_ecowatt(client):
    if (client.getStatusLastCall() or client.lastMethodCallError == "updateEcoWatt") and (
        client.getServiceEnedis() == _ENEDIS_MyElectricData
    ):
        client.updateEcoWatt()
    client.updateTimeLastCall()
    client.updateStatusLastCall(True)
    log.info("mise à jour effectuee EcoWatt")


def call_tempo(client):
    if (client.getStatusLastCall() or client.lastMethodCallError == "updateTempo") and (
        client.getServiceEnedis() == _ENEDIS_MyElectricData
    ):
        client.updateTempo()
    client.updateTimeLastCall()
    client.updateStatusLastCall(True)
    log.info("mise à jour effectuee Tempo")


def _run_if_needed(client, method_name, method_fn):
    if client.getStatusLastCall() or client.lastMethodCallError == method_name:
        method_fn()


def do_update(client):
    log.info("myEnedis ...new update ?? %s", client._PDL_ID)
    if client.contract.isLoaded:
        if get_call_possible(client):
            try:
                log.info(
                    "myEnedis(%s) ...%s update lancé,"
                    " status precedent : %s, lastMethodCall :%s, forcejson :%s",
                    client.getVersion(),
                    client.contract.get_PDL_ID(),
                    client.getStatusLastCall(),
                    client.lastMethodCallError,
                    client._forceCallJson,
                )
                client._nbCall = 0
                client.updateGitVersion()
                client.updateErrorLastCall("")
                client.lastMethodCall = ""
                client.setUpdateRealise(True)
                if not client._forceCallJson:
                    client.updateStatusLastCall(True)
                try:
                    call_consommation(client)
                    call_production(client)
                    call_ecowatt(client)
                    call_tempo(client)
                    if client._forceCallJson:
                        client._forceCallJson = False
                        client.setDataJsonDefault({})

                    log.info(
                        "myEnedis(%s) ... %s update termine,"
                        " status courant : %s, lastCall :%s, nbCall :%s",
                        client.getVersion(),
                        client.contract.get_PDL_ID(),
                        client.getStatusLastCall(),
                        client.lastMethodCallError,
                        client.getNbCall(),
                    )
                except Exception as inst:
                    _handle_update_exception(client, inst)
            except Exception as inst:
                if isinstance(inst, EnedisDataError):
                    log.error(
                        "%s - Erreur call",
                        client.contract.get_PDL_ID(),
                    )
                    client.updateTimeLastCall()
                    client.updateStatusLastCall(False)
                    message = "{} - {}".format(
                        str(inst),
                        client._myCalli.getLastAnswer(),
                    )
                    client.updateErrorLastCall(message)
                    log.error(
                        "%s - %s",
                        client.contract.get_PDL_ID(),
                        client.lastMethodCall,
                    )
                else:
                    log.error("Erreur inconnue call ERROR %s", inst)
                    log.error("Erreur last answer %s", inst)
                    log.error("Erreur last call %s", client.lastMethodCall)
                    log.error("Erreur last answer %s", client._myCalli.getLastAnswer())
                    log.error(traceback.format_exc())
                    log.error("-" * 60)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    log.warning(sys.exc_info())
                    client.updateStatusLastCall(False)
                    client.updateTimeLastCall()
                    client.updateErrorLastCall(str(inst))
                    log.error("LastMethodCall : %s", client.lastMethodCall)
        else:
            client.setUpdateRealise(False)
    else:
        client.setUpdateRealise(False)
        log.info(
            "%s update impossible contrat non trouve!!!",
            client.contract.get_PDL_ID(),
        )
    client.updateLastUpdate()
    return True


def _handle_update_exception(client, inst):
    if client._forceCallJson:
        client._forceCallJson = False
        client.setDataJsonDefault({})
    if isinstance(inst, EnedisApiError):
        log.error(
            "%s - Erreur call ERROR %s",
            client.contract.get_PDL_ID(),
            inst,
        )
        client.updateTimeLastCall()
        client.updateStatusLastCall(False)
        client.updateErrorLastCall(
            "{} - {}".format(str(inst), client._myCalli.getLastAnswer())
        )
        log.error(
            "%s - last call : %s",
            client.contract.get_PDL_ID(),
            client.lastMethodCall,
        )
        log.error(
            "myEnedis ...%s update termine, on retentera plus tard(A1)",
            client.contract.get_PDL_ID(),
        )
    elif isinstance(inst, EnedisAuthError):
        log.error(
            "%s - Erreur call ERROR %s",
            client.contract.get_PDL_ID(),
            inst,
        )
        client.updateTimeLastCall()
        client.updateStatusLastCall(False)
        client._myCalli.setLastAnswer("Enedis")
        client.updateErrorLastCall(
            "%s - %s" % (str(inst), client._myCalli.getLastAnswer())
        )
        log.error(
            "%s - last call : %s",
            client.contract.get_PDL_ID(),
            client.lastMethodCall,
        )
        log.error(
            "myEnedis ...%s update termine, on retentera plus tard(A2)",
            client.contract.get_PDL_ID(),
        )
    else:
        client.updateTimeLastCall()
        client.updateStatusLastCall(False)
        client.updateErrorLastCall(str(client._myCalli.getLastAnswer()))
        log.error(
            "%s - last call : %s",
            client.contract.get_PDL_ID(),
            client.lastMethodCall,
        )
        log.error(
            "myEnedis ...%s update termine, on retentera plus tard(B)",
            client.contract.get_PDL_ID(),
        )
        raise
