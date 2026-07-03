"""Unit tests for SysCheck check functions."""
from syscheck import system_checks, network_checks, log_checks, config


def test_cpu_check_structure():
    result = system_checks.check_cpu()
    assert set(result) == {"name", "value", "status"}
    assert result["status"] in ("OK", "WARN")


def test_cpu_warn_threshold():
    # threshold of 0 forces a WARN on any machine
    assert system_checks.check_cpu(warn_at=0)["status"] == "WARN"


def test_memory_check():
    result = system_checks.check_memory()
    assert "%" in result["value"]


def test_disks_return_list():
    results = system_checks.check_disks()
    assert isinstance(results, list)
    for r in results:
        assert r["status"] in ("OK", "WARN")


def test_dns_failure_handled():
    result = network_checks.dns_lookup(
        "definitely-not-a-real-domain-xyz.invalid")
    assert result["status"] == "FAIL"


def test_port_check_structure():
    # port 9 (discard) on localhost is almost certainly closed;
    # either way the function must return a well-formed result
    result = network_checks.check_port("127.0.0.1", 9, "test")
    assert result["status"] in ("OK", "WARN")


def test_config_defaults_when_missing():
    cfg = config.load("no_such_file.json")
    assert cfg["thresholds"]["cpu_warn"] == 80
    assert cfg["network"]["ping_host"] == "8.8.8.8"


def test_config_merge(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"thresholds": {"cpu_warn": 50}}', encoding="utf-8")
    cfg = config.load(str(p))
    assert cfg["thresholds"]["cpu_warn"] == 50       # overridden
    assert cfg["thresholds"]["memory_warn"] == 80    # default kept


def test_bad_config_falls_back(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{not valid json", encoding="utf-8")
    cfg = config.load(str(p))
    assert cfg["thresholds"]["cpu_warn"] == 80


def test_log_reader_never_crashes():
    results = log_checks.recent_errors(5)
    assert isinstance(results, list)
    assert len(results) >= 1
    for r in results:
        assert r["status"] in ("OK", "WARN")
