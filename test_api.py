#!/usr/bin/env python3
"""Test myEnedis API calls + object parsing.

Usage:
  export PDL="20000000000000"
  export TOKEN="xxx"

  # Online — real HTTP call
  python test_api.py --offline contract

  # Offline — uses tests/Json/ files
  python test_api.py --offline contract
  python test_api.py --offline consumption
  python test_api.py --offline full
"""
import argparse
import json
import os
import sys
from pathlib import Path
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

sys.path.insert(0, str(Path(__file__).parent))

from custom_components.myEnedis.myCall import myCall
from custom_components.myEnedis.myContrat import myContrat
from custom_components.myEnedis.myDataEnedis import myDataEnedis
from custom_components.myEnedis.myDataEnedisByDay import myDataEnedisByDay
from custom_components.myEnedis.myDataEnedisByDayDetail import myDataEnedisByDayDetail
from custom_components.myEnedis.myDataEnedisMaxPower import myDataEnedisMaxPower
from custom_components.myEnedis.myDataEnedisProduction import myDataEnedisProduction
from custom_components.myEnedis.myDataEnedisEcoWatt import myDataEnedisEcoWatt
from custom_components.myEnedis.myDataEnedisTempo import myDataEnedisTempo
from custom_components.myEnedis.myCheckData import myCheckData
from custom_components.myEnedis.exceptions import EnedisError

PARSED_OK = "✓"
PARSED_ERR = "✗"
HERE = Path(__file__).parent
JSON_DIR = HERE / "tests" / "Json"


# ---------------------------------------------------------------------------
# Offline data loader
# ---------------------------------------------------------------------------

def _load(name):
    path = JSON_DIR / name
    with open(path) as f:
        return json.load(f)


def _load_or_fetch(call_or_none, fname, fetch_fn):
    if call_or_none is None:
        if fname is None:
            return None, True
        return _load(fname), True
    print(f"  Appel HTTP...")
    result = fetch_fn()
    if isinstance(result, tuple) and len(result) == 2:
        return result
    return result, True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_contract(call, pdl, token, offline=False):
    raw, _ = _load_or_fetch(call, "Contract/contract1.json",
                            lambda: call.getDataContract())
    if offline:
        pdl = raw["customer"]["usage_points"][0]["usage_point"]["usage_point_id"]
    print(f"\nRaw JSON keys: {list(raw.keys())}")
    print(f"Raw (truncated): {json.dumps(raw, indent=2, default=str)[:2000]}")

    contrat = myContrat(call or myCall(), token, pdl, "0.0.0", True, None)
    contrat._contract = {}
    contrat.updateContract(data=raw)
    contrat.updateHCHP()

    print(f"\nParsed contract:")
    print(f"  subscribed_power : {contrat.getsubscribed_power()}")
    print(f"  offpeak_hours    : {contrat.getoffpeak_hours()}")
    print(f"  last_activation  : {contrat.getLastActivationDate()}")
    print(f"  usage_point_stat : {contrat.getUsagePointStatus()}")
    print(f"  type_PDL         : {contrat.getTypePDL()}")
    print(f"  is_loaded        : {contrat.isLoaded}")
    return contrat


def _test_data(call, contrat, pdl, token, label, fname, fetch_fn):
    print(f"\n--- {label} ---")
    raw, done = _load_or_fetch(call, fname, fetch_fn)
    if raw is None:
        print(f"  {PARSED_ERR} No test data available")
        return None
    status = PARSED_OK if done else PARSED_ERR
    print(f"  Raw call: {status}")
    if isinstance(raw, dict):
        print(f"  Raw keys: {list(raw.keys())}")
    return raw


def _parse_consommation(call, contrat, token, raw, start, end):
    d = myDataEnedis(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedis    : {PARSED_OK if v > 0 else PARSED_ERR} value={v} Wh ({v/1000:.3f} kWh)")
    return v


def _parse_max_power(call, contrat, token, raw, start, end):
    d = myDataEnedisMaxPower(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedisMaxPower: {PARSED_OK if v > 0 else PARSED_ERR} value={v} VA")
    return v


def _parse_production(call, contrat, token, raw, start, end):
    d = myDataEnedisProduction(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedisProduction: {PARSED_OK if v > 0 else PARSED_ERR} value={v} Wh ({v/1000:.3f} kWh)")
    return v


def _parse_ecowatt(call, contrat, token, raw, start, end):
    d = myDataEnedisEcoWatt(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedisEcoWatt: {PARSED_OK if v else PARSED_ERR}")
    return v


def _parse_tempo(call, contrat, token, raw, start, end):
    d = myDataEnedisTempo(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedisTempo: {PARSED_OK if v else PARSED_ERR}")
    return v


def _parse_by_day(call, contrat, token, raw, start, end):
    d = myDataEnedisByDay(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedisByDay: {PARSED_OK if v > 0 else PARSED_ERR} value={v} Wh ({v/1000:.3f} kWh)")
    return v


def _parse_by_day_detail(call, contrat, token, raw, start, end):
    d = myDataEnedisByDayDetail(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    hp = d.getHP() or 0
    hc = d.getHC() or 0
    total = hp + hc
    print(f"  myDataEnedisByDayDetail: {PARSED_OK if total > 0 else PARSED_ERR} HP={hp} HC={hc} total={total} Wh")
    return d


def _parse_month(call, contrat, token, raw, start, end):
    d = myDataEnedis(call or myCall(), token, "0.0.0", contrat)
    d.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v = d.getValue()
    print(f"  myDataEnedis (month): {PARSED_OK if v > 0 else PARSED_ERR} value={v} Wh ({v/1000:.3f} kWh)")

    d2 = myDataEnedisByDay(call or myCall(), token, "0.0.0", contrat)
    d2.updateData("test", data=raw, dateDeb=start, dateFin=end)
    v2 = d2.getValue()
    print(f"  myDataEnedisByDay  : {PARSED_OK if v2 > 0 else PARSED_ERR} value={v2} Wh ({v2/1000:.3f} kWh)")
    return v


def _parse_production_offline(raw):
    from custom_components.myEnedis.myCheckData import myCheckData
    ck = myCheckData()
    try:
        if ck.checkDataPeriod(raw) is False:
            print(f"  checkDataPeriod: {PARSED_OK} acceptable error (UNKERROR_002)")
            return True
        print(f"  checkDataPeriod: {PARSED_ERR} unexpected pass")
        return False
    except EnedisError as e:
        print(f"  checkDataPeriod: {PARSED_OK} raised {type(e).__name__}: {e}")
        return True


def _parse_error(label, raw, check_fn=myCheckData().checkData):
    try:
        result = check_fn(raw)
        if result is False:
            print(f"  {label}: {PARSED_OK} acceptable error (returned False)")
            return True
        print(f"  {label}: {PARSED_ERR} unexpected pass (returned {result})")
        return False
    except EnedisError as e:
        print(f"  {label}: {PARSED_OK} raised {type(e).__name__}: {e}")
        return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Test myEnedis API + parsing")
    parser.add_argument("--pdl", default=os.environ.get("PDL"))
    parser.add_argument("--token", default=os.environ.get("TOKEN"))

    sub = parser.add_subparsers(dest="command", required=True)

    def add_opts(p):
        p.add_argument("--service", default="enedisGateway",
                       choices=["enedisGateway", "myElectricalData"])
        p.add_argument("--test", action="store_true",
                       help="Force ha_sensor_myenedis_version=test_saniho")
        p.add_argument("--start", default=None)
        p.add_argument("--end", default=None)

    p = sub.add_parser("contract")
    add_opts(p)
    p = sub.add_parser("consumption")
    add_opts(p)
    p = sub.add_parser("full")
    add_opts(p)
    p = sub.add_parser("ecowatt")
    add_opts(p)
    p = sub.add_parser("tempo")
    add_opts(p)
    p = sub.add_parser("production")
    add_opts(p)
    p = sub.add_parser("maxpower")
    add_opts(p)
    p = sub.add_parser("detail")
    add_opts(p)
    p = sub.add_parser("month")
    add_opts(p)
    p = sub.add_parser("errors")
    add_opts(p)

    # --offline accepted anywhere in argv
    offline = "--offline" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--offline"]

    args = parser.parse_args(argv)

    if not offline and (not args.pdl or not args.token):
        parser.error(
            "Online mode requires PDL and TOKEN "
            "(set env vars or pass --pdl/--token). "
            "Use --offline to use test JSON files."
        )

    test_mode = getattr(args, "test", False)

    if not offline:
        import custom_components.myEnedis.myCall as mc_mod
        mc_mod.INITIAL_CALL_DELAY = 0.1
        mc_mod.NEXT_MIN_CALL_DELAY = 0.1
        mc_mod.MAX_CALL_DELAY = 0.5
        call = myCall()
        version = "test_saniho" if test_mode else "0.0.0"
        call.setParam(args.pdl, args.token, version, args.service)
        if test_mode:
            print(f"  Header ha_sensor_myenedis_version → test_saniho")
    else:
        call = None
        print(f"  Mode offline — lectures depuis {JSON_DIR}")

    print(f"\n{'='*60}")
    print(f"{args.command.upper()} — {'offline' if offline else args.service}")
    print(f"{'='*60}")

    contrat = test_contract(call, args.pdl, args.token, offline=offline)

    cmd = args.command
    if cmd == "contract":
        pass

    elif cmd == "consumption":
        raw = _test_data(call, contrat, args.pdl, args.token,
                         f"Consommation {args.start}→{args.end}",
                         "Yesterday/yesterday1.json",
                         lambda: call.getDataPeriod(args.start, args.end))
        if raw is not None:
            _parse_consommation(call, contrat, args.token, raw, args.start, args.end)

    elif cmd == "full":
        for label, fname, parse_fn, fetch_fn in [
            ("Yesterday", "Yesterday/yesterday1.json",
             lambda r: _parse_consommation(call, contrat, args.token, r, "2024-01-01", "2024-01-02"),
             lambda: call.getDataPeriod("2024-01-01", "2024-01-02")),
            ("ByDay (Week1)", "Week/week1.json",
             lambda r: _parse_by_day(call, contrat, args.token, r, "2020-12-03", "2020-12-09"),
             lambda: call.getDataPeriod("2020-12-03", "2020-12-09")),
            ("ByDay (Week2 15min)", "Week/week2.json",
             lambda r: _parse_by_day(call, contrat, args.token, r, "2022-03-01", "2022-03-07"),
             lambda: call.getDataPeriod("2022-03-01", "2022-03-07")),
            ("ByDayDetail (30min)", "Yesterday/yesterdayDetail1.json",
             lambda r: _parse_by_day_detail(call, contrat, args.token, r, "2020-12-02", "2020-12-09"),
             lambda: call.getDataPeriod("2020-12-02", "2020-12-09")),
            ("ByDayDetail (15min)", "Week/week2.json",
             lambda r: _parse_by_day_detail(call, contrat, args.token, r, "2022-03-01", "2022-03-07"),
             lambda: call.getDataPeriod("2022-03-01", "2022-03-07")),
            ("Month", "Month/currentMonth1.json",
             lambda r: _parse_month(call, contrat, args.token, r, "2020-11-30", "2020-12-06"),
             lambda: call.getDataPeriod("2020-11-30", "2020-12-06")),
            ("Max Power", None,
             lambda r: _parse_max_power(call, contrat, args.token, r, "2024-01-01", "2024-01-02"),
             lambda: call.getDataPeriodConsumptionMaxPower("2024-01-01", "2024-01-02")),
            ("Production (error2)", "Production/error2.json",
             lambda r: _parse_production_offline(r),
             lambda: call.getDataProductionPeriod("2024-01-01", "2024-01-02")),
            ("Production (error1)", "Production/error1.json",
             lambda r: _parse_production_offline(r),
             lambda: call.getDataProductionPeriod("2024-01-01", "2024-01-02")),
            ("EcoWatt", "EcoWatt/updateEcoWatt.json",
             lambda r: _parse_ecowatt(call, contrat, args.token, r, "2024-01-01", "2024-01-02"),
             lambda: call.getDataEcoWatt("2024-01-01", "2024-01-02")),
            ("Tempo", None,
             lambda r: _parse_tempo(call, contrat, args.token, r, "2024-01-01", "2024-01-02"),
             lambda: call.getDataTempo("2024-01-01", "2024-01-02")),
        ]:
            raw = _test_data(call, contrat, args.pdl, args.token, label, fname, fetch_fn)
            if raw is not None:
                parse_fn(raw)

    elif cmd == "detail":
        for fname, start, end in [
            ("Week/week1.json", "2020-12-03", "2020-12-09"),
            ("Week/week2.json", "2022-03-01", "2022-03-07"),
        ]:
            raw = _test_data(call, contrat, args.pdl, args.token,
                             f"ByDay ({Path(fname).name})", fname,
                             lambda: call.getDataPeriod(start, end))
            if raw is not None:
                _parse_by_day(call, contrat, args.token, raw, start, end)

        for fname, start, end in [
            ("Yesterday/yesterdayDetail1.json", "2020-12-02", "2020-12-09"),
            ("Week/week2.json", "2022-03-01", "2022-03-07"),
        ]:
            raw = _test_data(call, contrat, args.pdl, args.token,
                             f"ByDayDetail ({Path(fname).name})", fname,
                             lambda: call.getDataPeriod(start, end))
            if raw is not None:
                _parse_by_day_detail(call, contrat, args.token, raw, start, end)

    elif cmd == "ecowatt":
        raw = _test_data(call, contrat, args.pdl, args.token,
                         f"EcoWatt {args.start}→{args.end}",
                         "EcoWatt/updateEcoWatt.json",
                         lambda: call.getDataEcoWatt(args.start, args.end))
        if raw is not None:
            _parse_ecowatt(call, contrat, args.token, raw, args.start, args.end)

    elif cmd == "tempo":
        raw = _test_data(call, contrat, args.pdl, args.token,
                         f"Tempo {args.start}→{args.end}",
                         None,
                         lambda: call.getDataTempo(args.start, args.end))
        if raw is not None:
            _parse_tempo(call, contrat, args.token, raw, args.start, args.end)

    elif cmd == "production":
        for fname in ("Production/error2.json", "Production/error1.json"):
            raw = _test_data(call, contrat, args.pdl, args.token,
                             f"Production ({Path(fname).name})", fname,
                             lambda: call.getDataProductionPeriod(args.start or "2024-01-01",
                                                                  args.end or "2024-01-02"))
            if raw is not None:
                _parse_production_offline(raw)

    elif cmd == "maxpower":
        raw = _test_data(call, contrat, args.pdl, args.token,
                         f"Max Power {args.start}→{args.end}",
                         None,
                         lambda: call.getDataPeriodConsumptionMaxPower(args.start, args.end))
        if raw is not None:
            _parse_max_power(call, contrat, args.token, raw, args.start, args.end)

    elif cmd == "month":
        for fname, start, end in [
            ("Month/currentMonth1.json", "2020-11-30", "2020-12-06"),
            ("Month/month1.json", "2020-11-01", "2020-11-30"),
            ("Month/currentMonthError1.json", "2024-01-01", "2024-01-02"),
        ]:
            raw = _test_data(call, contrat, args.pdl, args.token,
                             f"Month ({Path(fname).name})", fname,
                             lambda: call.getDataPeriod(start, end))
            if raw is not None:
                _parse_month(call, contrat, args.token, raw, start, end)

    elif cmd == "errors":
        ck = myCheckData()
        for fname in sorted((JSON_DIR / "Error").iterdir()):
            if fname.suffix != ".json":
                continue
            raw = _load(f"Error/{fname.name}")
            print(f"\n--- {fname.name} ---")
            print(f"  Keys: {list(raw.keys())}")
            _parse_error(fname.name, raw)

    print(f"\n{'='*60}")
    print("Done.")


if __name__ == "__main__":
    main()
