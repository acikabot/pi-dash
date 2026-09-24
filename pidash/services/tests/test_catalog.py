"""The catalogue turns the config file into services with sensible units."""

from pidash.services.catalog import get_service, services, services_with


def test_every_service_is_loaded():
    assert [s.id for s in services()] == ["always", "timed", "web"]


def test_units_follow_the_kind():
    always, timed, _web = services()
    # A scheduled service is controlled through its timer, a resident one directly.
    assert always.control_unit == "always-bot.service"
    assert timed.control_unit == "timed-bot.timer"
    assert always.service_unit == "always-bot.service"
    assert timed.timer_unit == "timed-bot.timer"


def test_a_manual_run_is_its_own_unit():
    always, timed, _web = services()
    assert always.run_unit("test") == "always-bot@test.service"
    assert timed.run_unit("") == "timed-bot.service"  # no mode: the plain unit
    assert always.has_run("test") and not always.has_run("nonsense")


def test_logs_and_prompts_resolve_to_paths():
    always = get_service("always")
    assert always.log_path.name == "always.log"
    assert always.prompts_dir.name == "prompts"
    assert always.prompt("style").label == "Style"
    assert always.prompt("nope") is None


def test_pages_can_ask_for_the_services_they_need():
    assert [s.id for s in services_with("prompts")] == ["always"]
    assert [s.id for s in services_with("config")] == ["timed"]
    assert [s.id for s in services_with("email")] == ["always"]
