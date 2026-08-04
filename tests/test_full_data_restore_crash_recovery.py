"""Durable crash recovery for the cross-resource full-data restore."""

from __future__ import annotations

import hashlib
import importlib
import json
import multiprocessing
import os
import stat
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from src.config import Config, setup_env
from src.core.config_manager import ConfigManager
from src.services.full_data_backup_service import (
    BACKUP_CONFIG_ALLOWLIST,
    FullDataBackupService,
)
from src.services.full_data_restore_journal import FullDataRestoreJournal
from src.services.system_config_service import SystemConfigService
from src.storage import AnalysisHistory, CURRENT_SCHEMA_VERSION, DatabaseManager


APPLICATION_VERSION = "test-app-7.4.1"
JOURNAL_FORMAT = "pp02.full-data.restore-transaction"
JOURNAL_FILENAME = ".pp02-full-data-restore-transaction.json"
LOCK_FILENAME = ".pp02-full-data-restore.lock"
PROCESS_START_TIMEOUT = 30


def _canonical_digest(document: dict) -> str:
    envelope = dict(document)
    integrity = dict(envelope["integrity"])
    integrity.pop("value", None)
    envelope["integrity"] = integrity
    return hashlib.sha256(
        json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _write_env(
    path: Path,
    db_path: Path,
    stock_list: str,
    secret: str,
    *,
    sqlite_settings: dict[str, str] | None = None,
) -> None:
    content = (
        f"STOCK_LIST={stock_list}\n"
        f"OPENAI_API_KEY={secret}\n"
        f"DATABASE_PATH={db_path}\n"
    )
    for key, value in sorted((sqlite_settings or {}).items()):
        content += f"{key}={value}\n"
    path.write_text(content, encoding="utf-8")


def _open_install(env_path: Path, db_path: Path):
    DatabaseManager.reset_instance()
    Config.reset_instance()
    os.environ["ENV_FILE"] = str(env_path)
    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ["PP02_APPLICATION_VERSION"] = APPLICATION_VERSION
    setup_env(override=True)
    db = DatabaseManager.get_instance()
    config = SystemConfigService(manager=ConfigManager(env_path=env_path))
    return db, FullDataBackupService(
        db_manager=db,
        config_service=config,
        application_version=APPLICATION_VERSION,
    )


def _seed_history(db: DatabaseManager, row_id: int, query_id: str, summary: str) -> None:
    with db.get_session() as session:
        session.add(
            AnalysisHistory(
                id=row_id,
                query_id=query_id,
                code="600519" if row_id == 101 else "000001",
                name="Synthetic",
                report_type="stock",
                analysis_summary=summary,
                created_at=datetime(2026, 8, 1, 9, 0, 0),
            )
        )
        session.commit()


def _restore_child(
    env_path: str,
    db_path: str,
    backup_path: str,
    crash_phase: str,
) -> None:
    env = Path(env_path)
    database = Path(db_path)
    backup = json.loads(Path(backup_path).read_text(encoding="utf-8"))
    _, service = _open_install(env, database)

    def hard_exit(phase: str) -> None:
        if phase == crash_phase:
            os._exit(81 if phase == "after_config_publish" else 82)

    service = FullDataBackupService(
        db_manager=service.db,
        config_service=service.config_service,
        application_version=APPLICATION_VERSION,
        crash_test_hook=hard_exit,
    )
    preview = service.preview_restore(backup)
    service.restore_backup(backup, preview_token=preview["preview_token"])
    os._exit(83)


def _journal_for_paths(env_path: Path, db_path: Path) -> tuple[FullDataRestoreJournal, object]:
    engine = create_engine(f"sqlite:///{db_path}")
    manager = SimpleNamespace(_engine=engine)
    config = SystemConfigService(manager=ConfigManager(env_path=env_path))
    return (
        FullDataRestoreJournal(
            db_manager=manager,
            config_service=config,
            application_version=APPLICATION_VERSION,
            database_schema_version=CURRENT_SCHEMA_VERSION,
            managed_keys=set(BACKUP_CONFIG_ALLOWLIST),
            value_validator=FullDataBackupService._validate_config_value,
        ),
        engine,
    )


def _hold_restore_lock_then_exit(
    env_path: str,
    db_path: str,
    attempting,
    acquired,
    release,
    exit_code: int,
) -> None:
    journal, engine = _journal_for_paths(Path(env_path), Path(db_path))
    attempting.set()
    with journal.transaction_lock():
        acquired.set()
        release.wait(timeout=20)
        engine.dispose()
        os._exit(exit_code)


def _pause_inside_finish(
    env_path: str,
    db_path: str,
    tx_id: str,
    at_clear_boundary,
    release,
) -> None:
    journal, engine = _journal_for_paths(Path(env_path), Path(db_path))
    original_clear = journal._clear_journal

    def clear_after_barrier() -> None:
        at_clear_boundary.set()
        release.wait(timeout=30)
        original_clear()

    journal._clear_journal = clear_after_barrier
    with journal.transaction_lock():
        journal.finish(tx_id)
    engine.dispose()


def _startup_recovery_observer(
    env_path: str,
    db_path: str,
    started,
    completed,
    result_queue,
) -> None:
    started.set()
    db, _ = _open_install(Path(env_path), Path(db_path))
    with db.get_session() as session:
        ids = [row.id for row in session.query(AnalysisHistory).all()]
    stock_list = ConfigManager(env_path=Path(env_path)).read_config_map()["STOCK_LIST"]
    result_queue.put((ids, stock_list))
    completed.set()


def _cli_proxy_recovery_observer(
    env_path: str,
    db_path: str,
    initial_proxy_env: dict[str, str],
    result_queue,
) -> None:
    proxy_keys = (
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "no_proxy",
        "NO_PROXY",
    )
    for key in proxy_keys:
        os.environ.pop(key, None)
    os.environ.update(initial_proxy_env)
    os.environ["ENV_FILE"] = env_path
    os.environ["DATABASE_PATH"] = db_path
    os.environ["PP02_APPLICATION_VERSION"] = APPLICATION_VERSION
    main_module = importlib.import_module("main")
    before_database = {key: os.environ.get(key) for key in proxy_keys}
    DatabaseManager.reset_instance()
    Config.reset_instance()
    DatabaseManager.get_instance()
    main_module._synchronize_process_proxy_after_recovery()
    after_recovery = {key: os.environ.get(key) for key in proxy_keys}
    result_queue.put((before_database, after_recovery))


@pytest.fixture(autouse=True)
def _reset_runtime(monkeypatch):
    original = dict(os.environ)
    yield
    DatabaseManager.reset_instance()
    Config.reset_instance()
    os.environ.clear()
    os.environ.update(original)


def _prepare_crash_case(
    tmp_path: Path,
    *,
    source_sqlite_settings: dict[str, str] | None = None,
    destination_sqlite_settings: dict[str, str] | None = None,
):
    source_env = tmp_path / "source.env"
    source_db_path = tmp_path / "source.db"
    _write_env(
        source_env,
        source_db_path,
        "600519,AAPL",
        "source-secret-not-journaled",
        sqlite_settings=source_sqlite_settings,
    )
    source_db, source_service = _open_install(source_env, source_db_path)
    _seed_history(source_db, 101, "source-query-101", "source exact content")
    backup_path = tmp_path / "incoming-backup.json"
    backup_path.write_text(
        json.dumps(source_service.export_backup(), ensure_ascii=False),
        encoding="utf-8",
    )

    destination_env = tmp_path / "destination.env"
    destination_db_path = tmp_path / "destination.db"
    _write_env(
        destination_env,
        destination_db_path,
        "000001",
        "destination-secret-not-journaled",
        sqlite_settings=destination_sqlite_settings,
    )
    destination_db, _ = _open_install(destination_env, destination_db_path)
    _seed_history(destination_db, 202, "destination-query-202", "destination exact content")
    DatabaseManager.reset_instance()
    return destination_env, destination_db_path, backup_path


@pytest.mark.parametrize(
    (
        "crash_phase",
        "exit_code",
        "concurrent_stock_list",
        "expected_id",
        "expected_stock_list",
    ),
    (
        ("after_config_publish", 81, None, 202, "000001"),
        ("after_config_publish", 81, "300750", 202, "300750"),
        ("after_db_commit", 82, None, 101, "600519,AAPL"),
        ("after_db_commit", 82, "300750", 101, "300750"),
    ),
)
def test_hard_exit_restore_recovers_exact_state_on_repeated_startup(
    tmp_path,
    crash_phase,
    exit_code,
    concurrent_stock_list,
    expected_id,
    expected_stock_list,
) -> None:
    destination_env, destination_db_path, backup_path = _prepare_crash_case(tmp_path)
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=_restore_child,
        args=(
            str(destination_env),
            str(destination_db_path),
            str(backup_path),
            crash_phase,
        ),
    )
    process.start()
    process.join(timeout=20)
    assert not process.is_alive()
    assert process.exitcode == exit_code

    journal_path = (
        destination_db_path.parent
        / f"{destination_db_path.stem}_restore_recovery"
        / JOURNAL_FILENAME
    )
    assert journal_path.is_file()
    if os.name != "nt":
        assert stat.S_IMODE(journal_path.stat().st_mode) == 0o600
    raw_journal = journal_path.read_text(encoding="utf-8")
    assert str(destination_db_path) not in raw_journal
    assert "source exact content" not in raw_journal
    assert "destination exact content" not in raw_journal
    assert "source-secret-not-journaled" not in raw_journal
    assert "destination-secret-not-journaled" not in raw_journal
    if concurrent_stock_list is not None:
        manager = ConfigManager(env_path=destination_env)
        SystemConfigService(manager=manager).update(
            config_version=manager.get_config_version(),
            items=[{"key": "STOCK_LIST", "value": concurrent_stock_list}],
            reload_now=False,
        )

    restarted_db, _ = _open_install(destination_env, destination_db_path)
    with restarted_db.get_session() as session:
        rows = session.query(AnalysisHistory).all()
        assert [(row.id, row.query_id, row.analysis_summary) for row in rows] == [
            (
                expected_id,
                "source-query-101" if expected_id == 101 else "destination-query-202",
                "source exact content" if expected_id == 101 else "destination exact content",
            )
        ]
    assert ConfigManager(env_path=destination_env).read_config_map()["STOCK_LIST"] == (
        expected_stock_list
    )
    assert os.environ["STOCK_LIST"] == expected_stock_list
    assert Config.get_instance().stock_list == expected_stock_list.split(",")
    assert not journal_path.exists()

    DatabaseManager.reset_instance()
    Config.reset_instance()
    second_db, _ = _open_install(destination_env, destination_db_path)
    with second_db.get_session() as session:
        assert [row.id for row in session.query(AnalysisHistory).all()] == [expected_id]
    assert ConfigManager(env_path=destination_env).read_config_map()["STOCK_LIST"] == (
        expected_stock_list
    )


def test_marker_absent_recovery_rebuilds_database_runtime_from_prior_config(tmp_path) -> None:
    prior_settings = {
        "SQLITE_BUSY_TIMEOUT_MS": "1234",
        "SQLITE_WAL_ENABLED": "false",
        "SQLITE_WRITE_RETRY_BASE_DELAY": "0.25",
        "SQLITE_WRITE_RETRY_MAX": "7",
    }
    incoming_settings = {
        "SQLITE_BUSY_TIMEOUT_MS": "8765",
        "SQLITE_WAL_ENABLED": "true",
        "SQLITE_WRITE_RETRY_BASE_DELAY": "0.01",
        "SQLITE_WRITE_RETRY_MAX": "1",
    }
    destination_env, destination_db_path, backup_path = _prepare_crash_case(
        tmp_path,
        source_sqlite_settings=incoming_settings,
        destination_sqlite_settings=prior_settings,
    )
    backup_document = json.loads(backup_path.read_text(encoding="utf-8"))
    backup_values = backup_document["data"]["configuration"]["values"]
    assert set(incoming_settings) <= BACKUP_CONFIG_ALLOWLIST
    assert {key: backup_values[key] for key in incoming_settings} == incoming_settings
    assert backup_document["manifest"]["categories"]["configuration"][
        "row_count"
    ] == len(backup_values)
    process = multiprocessing.get_context("spawn").Process(
        target=_restore_child,
        args=(
            str(destination_env),
            str(destination_db_path),
            str(backup_path),
            "after_config_publish",
        ),
    )
    process.start()
    process.join(timeout=20)
    assert process.exitcode == 81
    published_values = ConfigManager(env_path=destination_env).read_config_map()
    assert {key: published_values[key] for key in incoming_settings} == incoming_settings

    restarted_db, _ = _open_install(destination_env, destination_db_path)

    assert restarted_db._sqlite_wal_enabled is False
    assert restarted_db._sqlite_busy_timeout_ms == 1234
    assert restarted_db._sqlite_write_retry_max == 7
    assert restarted_db._sqlite_write_retry_base_delay == pytest.approx(0.25)
    with restarted_db.get_session() as session:
        connection = session.connection()
        assert str(connection.exec_driver_sql("PRAGMA journal_mode").scalar()).lower() == "delete"
        assert int(connection.exec_driver_sql("PRAGMA busy_timeout").scalar()) == 1234
    assert Config.get_instance().sqlite_wal_enabled is False
    assert Config.get_instance().sqlite_busy_timeout_ms == 1234


def test_api_lifespan_recovers_custom_database_from_env_file_without_process_path(
    tmp_path,
    monkeypatch,
) -> None:
    destination_env, destination_db_path, backup_path = _prepare_crash_case(tmp_path)
    crash = multiprocessing.get_context("spawn").Process(
        target=_restore_child,
        args=(
            str(destination_env),
            str(destination_db_path),
            str(backup_path),
            "after_config_publish",
        ),
    )
    crash.start()
    crash.join(timeout=20)
    assert crash.exitcode == 81
    journal_path = (
        destination_db_path.parent
        / f"{destination_db_path.stem}_restore_recovery"
        / JOURNAL_FILENAME
    )
    assert journal_path.is_file()
    assert ConfigManager(env_path=destination_env).read_config_map()["STOCK_LIST"] == (
        "600519,AAPL"
    )

    DatabaseManager.reset_instance()
    Config.reset_instance()
    monkeypatch.setenv("ENV_FILE", str(destination_env))
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("PP02_APPLICATION_VERSION", APPLICATION_VERSION)
    monkeypatch.setenv("DSA_RUNTIME_SCHEDULER_SUPPRESS_START", "1")

    from api import app as app_module

    class InertRuntimeScheduler:
        def __init__(self, **_kwargs) -> None:
            pass

        def stop(self) -> None:
            pass

    monkeypatch.setattr(
        app_module,
        "RuntimeSchedulerService",
        InertRuntimeScheduler,
    )
    monkeypatch.setattr(
        app_module,
        "_schedule_stock_index_background_refresh",
        lambda *_args, **_kwargs: None,
    )
    static_dir = tmp_path / "empty-static"
    static_dir.mkdir()
    with TestClient(app_module.create_app(static_dir=static_dir)) as client:
        assert client.get("/api/health").status_code == 200
        restarted_db = DatabaseManager.get_instance()
        assert Path(restarted_db._engine.url.database).resolve() == destination_db_path
        with restarted_db.get_session() as session:
            rows = session.query(AnalysisHistory).all()
            assert [(row.id, row.query_id) for row in rows] == [
                (202, "destination-query-202")
            ]

    assert ConfigManager(env_path=destination_env).read_config_map()["STOCK_LIST"] == (
        "000001"
    )
    assert os.environ["DATABASE_PATH"] == str(destination_db_path)
    assert Config.get_instance().stock_list == ["000001"]
    assert not journal_path.exists()


@pytest.mark.parametrize(
    ("prior_proxy", "incoming_proxy", "initial_proxy_env", "expected_proxy"),
    (
        (
            {"USE_PROXY": "false", "PROXY_HOST": "prior.invalid", "PROXY_PORT": "10809"},
            {"USE_PROXY": "true", "PROXY_HOST": "incoming.invalid", "PROXY_PORT": "18080"},
            {},
            None,
        ),
        (
            {"USE_PROXY": "true", "PROXY_HOST": "prior.invalid", "PROXY_PORT": "10809"},
            {"USE_PROXY": "false", "PROXY_HOST": "incoming.invalid", "PROXY_PORT": "18080"},
            {},
            "http://prior.invalid:10809",
        ),
        (
            {"USE_PROXY": "true", "PROXY_HOST": "prior.invalid", "PROXY_PORT": "10809"},
            {"USE_PROXY": "false", "PROXY_HOST": "incoming.invalid", "PROXY_PORT": "18080"},
            {
                "HTTP_PROXY": "http://explicit.invalid:9000",
                "HTTPS_PROXY": "http://explicit.invalid:9001",
                "NO_PROXY": "explicit.invalid",
            },
            "http://prior.invalid:10809",
        ),
    ),
)
def test_cli_defers_proxy_sync_until_after_recovery_and_preserves_process_overrides(
    tmp_path,
    prior_proxy,
    incoming_proxy,
    initial_proxy_env,
    expected_proxy,
) -> None:
    destination_env, destination_db_path, backup_path = _prepare_crash_case(
        tmp_path,
        source_sqlite_settings=incoming_proxy,
        destination_sqlite_settings=prior_proxy,
    )
    crash = multiprocessing.get_context("spawn").Process(
        target=_restore_child,
        args=(
            str(destination_env),
            str(destination_db_path),
            str(backup_path),
            "after_config_publish",
        ),
    )
    crash.start()
    crash.join(timeout=20)
    assert crash.exitcode == 81

    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    observer = context.Process(
        target=_cli_proxy_recovery_observer,
        args=(
            str(destination_env),
            str(destination_db_path),
            initial_proxy_env,
            result_queue,
        ),
    )
    observer.start()
    observer.join(timeout=30)
    assert observer.exitcode == 0
    before_database, after_recovery = result_queue.get(timeout=2)
    assert before_database == {
        "http_proxy": None,
        "https_proxy": None,
        "HTTP_PROXY": initial_proxy_env.get("HTTP_PROXY"),
        "HTTPS_PROXY": initial_proxy_env.get("HTTPS_PROXY"),
        "no_proxy": None,
        "NO_PROXY": initial_proxy_env.get("NO_PROXY"),
    }
    if initial_proxy_env:
        assert after_recovery["HTTP_PROXY"] == initial_proxy_env["HTTP_PROXY"]
        assert after_recovery["HTTPS_PROXY"] == initial_proxy_env["HTTPS_PROXY"]
        assert after_recovery["NO_PROXY"] == initial_proxy_env["NO_PROXY"]
    else:
        assert after_recovery["HTTP_PROXY"] == expected_proxy
        assert after_recovery["HTTPS_PROXY"] == expected_proxy
        assert after_recovery["NO_PROXY"] is None
    assert after_recovery["http_proxy"] == expected_proxy
    assert after_recovery["https_proxy"] == expected_proxy
    assert after_recovery["no_proxy"] is None


@pytest.mark.parametrize("journal_kind", ("corrupt", "incompatible"))
def test_invalid_journal_aborts_startup_without_mutation(tmp_path, journal_kind) -> None:
    env_path = tmp_path / "current.env"
    db_path = tmp_path / "current.db"
    _write_env(env_path, db_path, "000001", "current-secret-not-journaled")
    db, _ = _open_install(env_path, db_path)
    _seed_history(db, 202, "destination-query-202", "destination exact content")
    DatabaseManager.reset_instance()
    before_env = env_path.read_bytes()
    with __import__("sqlite3").connect(db_path) as connection:
        before_dump = "\n".join(connection.iterdump())

    journal_path = db_path.parent / f"{db_path.stem}_restore_recovery" / JOURNAL_FILENAME
    journal_path.parent.mkdir()
    if journal_kind == "corrupt":
        journal_path.write_text("{not-json", encoding="utf-8")
    else:
        prior = {"STOCK_LIST": "000001"}
        incoming = {"STOCK_LIST": "600519,AAPL"}
        document = {
            "format": JOURNAL_FORMAT,
            "format_version": 1,
            "project_id": "PP02",
            "application_version": "incompatible-app",
            "database_schema_version": CURRENT_SCHEMA_VERSION,
            "tx_id": "a" * 64,
            "created_at": "2026-08-04T12:00:00Z",
            "managed_keys": ["STOCK_LIST"],
            "prior_values": prior,
            "incoming_values": incoming,
            "prior_digest": hashlib.sha256(
                json.dumps(prior, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "incoming_digest": hashlib.sha256(
                json.dumps(incoming, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "integrity": {"algorithm": "sha256", "value": ""},
        }
        document["integrity"]["value"] = _canonical_digest(document)
        journal_path.write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    journal_bytes = journal_path.read_bytes()

    with pytest.raises(RuntimeError, match="restore transaction journal"):
        _open_install(env_path, db_path)

    assert env_path.read_bytes() == before_env
    assert journal_path.read_bytes() == journal_bytes
    with __import__("sqlite3").connect(db_path) as connection:
        assert "\n".join(connection.iterdump()) == before_dump


def test_restore_lock_serializes_processes_and_hard_exit_releases_it(tmp_path) -> None:
    env_path = tmp_path / "lock.env"
    db_path = tmp_path / "lock.db"
    _write_env(env_path, db_path, "000001", "lock-secret-not-journaled")
    db, _ = _open_install(env_path, db_path)
    db._engine.dispose()
    DatabaseManager.reset_instance()
    context = multiprocessing.get_context("spawn")
    attempting_one = context.Event()
    acquired_one = context.Event()
    release_one = context.Event()
    attempting_two = context.Event()
    acquired_two = context.Event()
    release_two = context.Event()
    first = context.Process(
        target=_hold_restore_lock_then_exit,
        args=(str(env_path), str(db_path), attempting_one, acquired_one, release_one, 91),
    )
    second = context.Process(
        target=_hold_restore_lock_then_exit,
        args=(str(env_path), str(db_path), attempting_two, acquired_two, release_two, 92),
    )

    first.start()
    assert attempting_one.wait(timeout=PROCESS_START_TIMEOUT), (
        f"first child did not enter helper; exitcode={first.exitcode}"
    )
    assert acquired_one.wait(timeout=PROCESS_START_TIMEOUT), (
        f"first child did not acquire lock; exitcode={first.exitcode}"
    )
    second.start()
    assert attempting_two.wait(timeout=PROCESS_START_TIMEOUT), (
        f"second child did not enter helper; exitcode={second.exitcode}"
    )
    assert not acquired_two.wait(timeout=1)
    release_one.set()
    first.join(timeout=PROCESS_START_TIMEOUT)
    assert first.exitcode == 91, f"first child exitcode={first.exitcode}"
    assert acquired_two.wait(timeout=PROCESS_START_TIMEOUT), (
        f"second child did not acquire released lock; exitcode={second.exitcode}"
    )
    release_two.set()
    second.join(timeout=PROCESS_START_TIMEOUT)
    assert second.exitcode == 92, f"second child exitcode={second.exitcode}"

    lock_path = db_path.parent / f"{db_path.stem}_restore_recovery" / LOCK_FILENAME
    assert lock_path.is_file()
    if os.name != "nt":
        assert stat.S_IMODE(lock_path.stat().st_mode) == 0o600


def test_finish_and_startup_recovery_cannot_interleave(tmp_path) -> None:
    destination_env, destination_db_path, backup_path = _prepare_crash_case(tmp_path)
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    db, service = _open_install(destination_env, destination_db_path)

    def interrupt_after_commit(phase: str) -> None:
        if phase == "after_db_commit":
            raise KeyboardInterrupt("leave one committed restore journal")

    interrupted = FullDataBackupService(
        db_manager=db,
        config_service=service.config_service,
        application_version=APPLICATION_VERSION,
        crash_test_hook=interrupt_after_commit,
    )
    preview = interrupted.preview_restore(backup)
    with pytest.raises(KeyboardInterrupt, match="committed restore journal"):
        interrupted.restore_backup(backup, preview_token=preview["preview_token"])
    journal_path = (
        destination_db_path.parent
        / f"{destination_db_path.stem}_restore_recovery"
        / JOURNAL_FILENAME
    )
    tx_id = json.loads(journal_path.read_text(encoding="utf-8"))["tx_id"]
    DatabaseManager.reset_instance()

    context = multiprocessing.get_context("spawn")
    at_clear_boundary = context.Event()
    release_finish = context.Event()
    startup_started = context.Event()
    startup_completed = context.Event()
    result_queue = context.Queue()
    finisher = context.Process(
        target=_pause_inside_finish,
        args=(
            str(destination_env),
            str(destination_db_path),
            tx_id,
            at_clear_boundary,
            release_finish,
        ),
    )
    recovery = context.Process(
        target=_startup_recovery_observer,
        args=(
            str(destination_env),
            str(destination_db_path),
            startup_started,
            startup_completed,
            result_queue,
        ),
    )

    finisher.start()
    assert at_clear_boundary.wait(timeout=10)
    recovery.start()
    assert startup_started.wait(timeout=20)
    assert not startup_completed.wait(timeout=1)
    release_finish.set()
    finisher.join(timeout=10)
    recovery.join(timeout=20)
    assert finisher.exitcode == 0
    assert recovery.exitcode == 0
    assert result_queue.get(timeout=2) == ([101], "600519,AAPL")
    assert not journal_path.exists()
