# -*- coding: utf-8 -*-
"""Unit tests for structured `.env` line preservation in ConfigManager."""

import errno
import hashlib
import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.config_manager import ConfigManager, ConfigManagerPublicationUncertain
from src.services.system_config_service import ConfigConflictError, SystemConfigService


def _atomic_restore_apply_process(
    env_path: str,
    expected_version: str,
    value: str,
    label: str,
    pause_before_publish: bool,
    entered,
    release,
    started,
    finished,
    results,
) -> None:
    manager = ConfigManager(env_path=Path(env_path))
    service = SystemConfigService(manager=manager)
    if pause_before_publish:
        if hasattr(manager, "_publish_staged_bytes"):
            original_publish = manager._publish_staged_bytes
            method_name = "_publish_staged_bytes"
        else:
            original_publish = manager._atomic_replace_bytes
            method_name = "_atomic_replace_bytes"

        def pausing_publish(*args, **kwargs):
            entered.set()
            if not release.wait(timeout=15):
                raise TimeoutError("test did not release staged config publish")
            return original_publish(*args, **kwargs)

        setattr(manager, method_name, pausing_publish)
    started.set()
    try:
        service.apply_env_subset_atomically(
            expected_version=expected_version,
            values={"STOCK_LIST": value},
            managed_keys={"STOCK_LIST"},
            reload_now=False,
        )
    except ConfigConflictError:
        results.put((label, "conflict"))
    except Exception as exc:
        results.put((label, f"error:{type(exc).__name__}:{exc}"))
    else:
        results.put((label, "success"))
    finally:
        finished.set()


class ConfigManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        os.environ["ENV_FILE"] = str(self.env_path)
        self.manager = ConfigManager(env_path=self.env_path)

    def tearDown(self) -> None:
        os.environ.pop("ENV_FILE", None)
        self.temp_dir.cleanup()

    def test_apply_updates_preserves_comments_blank_lines_and_raw_lines(self) -> None:
        self.env_path.write_text(
            "\n".join(
                [
                    "# Core settings",
                    "STOCK_LIST=600519,000001",
                    "",
                    "export SHOULD_STAY_UNCHANGED",
                    "# Secrets",
                    "GEMINI_API_KEY=secret-key",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        self.manager.apply_updates(
            updates=[("STOCK_LIST", "600519,300750")],
            sensitive_keys=set(),
            mask_token="******",
        )

        env_content = self.env_path.read_text(encoding="utf-8")
        self.assertIn("# Core settings\n", env_content)
        self.assertIn("\n\nexport SHOULD_STAY_UNCHANGED\n", env_content)
        self.assertIn("# Secrets\nGEMINI_API_KEY=secret-key\n", env_content)
        self.assertIn("STOCK_LIST=600519,300750\n", env_content)

    def test_config_version_is_exact_content_generation_not_file_metadata(self) -> None:
        content = b"STOCK_LIST=600519\n"
        self.env_path.write_bytes(content)
        original_version = self.manager.get_config_version()

        os.utime(self.env_path, ns=(1_900_000_000_000_000_000,) * 2)
        self.assertEqual(self.manager.get_config_version(), original_version)
        self.env_path.write_bytes(content)
        self.assertEqual(self.manager.get_config_version(), original_version)

        self.env_path.write_bytes(b"STOCK_LIST=300750\n")
        self.assertNotEqual(self.manager.get_config_version(), original_version)
        self.env_path.unlink()
        missing_version = self.manager.get_config_version()
        self.env_path.write_bytes(b"")
        self.assertNotEqual(self.manager.get_config_version(), missing_version)

    def test_read_paths_work_when_advisory_lock_cannot_be_opened(self) -> None:
        content = b"# readable deployment config\nSTOCK_LIST=600519,AAPL\n"
        self.env_path.write_bytes(content)
        self.env_path.with_name(self.env_path.name + ".lock").mkdir()
        expected_version = "sha256:" + hashlib.sha256(
            b"present\0" + content
        ).hexdigest()

        self.assertEqual(
            self.manager.read_config_map(),
            {"STOCK_LIST": "600519,AAPL"},
        )
        self.assertEqual(self.manager.get_config_version(), expected_version)
        exported = SystemConfigService(manager=self.manager).export_env()
        self.assertEqual(exported["content"], content.decode("utf-8"))
        self.assertEqual(exported["config_version"], expected_version)
        self.assertIsNotNone(exported["updated_at"])

    def test_two_process_atomic_restore_writers_linearize_on_expected_generation(self) -> None:
        self.env_path.write_text("STOCK_LIST=600519\n", encoding="utf-8")
        expected_version = self.manager.get_config_version()
        context = multiprocessing.get_context(
            "spawn" if os.name == "nt" else "fork"
        )
        first_entered = context.Event()
        release_first = context.Event()
        first_started = context.Event()
        first_finished = context.Event()
        second_started = context.Event()
        second_finished = context.Event()
        results = context.Queue()
        first = context.Process(
            target=_atomic_restore_apply_process,
            args=(
                str(self.env_path),
                expected_version,
                "300750",
                "first",
                True,
                first_entered,
                release_first,
                first_started,
                first_finished,
                results,
            ),
        )
        second = context.Process(
            target=_atomic_restore_apply_process,
            args=(
                str(self.env_path),
                expected_version,
                "AAPL",
                "second",
                False,
                context.Event(),
                context.Event(),
                second_started,
                second_finished,
                results,
            ),
        )
        first.start()
        try:
            self.assertTrue(first_started.wait(timeout=10))
            self.assertTrue(first_entered.wait(timeout=10))
            second.start()
            self.assertTrue(second_started.wait(timeout=10))
            second_completed_while_first_locked = second_finished.wait(timeout=1)
        finally:
            release_first.set()
        first.join(timeout=15)
        second.join(timeout=15)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertFalse(second_completed_while_first_locked)
        outcomes = dict(results.get(timeout=5) for _ in range(2))
        self.assertEqual(outcomes, {"first": "success", "second": "conflict"})
        self.assertEqual(
            ConfigManager(env_path=self.env_path).read_config_map()["STOCK_LIST"],
            "300750",
        )

    def test_apply_updates_only_rewrites_last_duplicate_assignment(self) -> None:
        self.env_path.write_text(
            "\n".join(
                [
                    "STOCK_LIST=600519",
                    "# Keep the legacy duplicate for audit history",
                    "STOCK_LIST=000001",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        self.manager.apply_updates(
            updates=[("STOCK_LIST", "300750")],
            sensitive_keys=set(),
            mask_token="******",
        )

        env_lines = self.env_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(env_lines[0], "STOCK_LIST=600519")
        self.assertEqual(env_lines[1], "# Keep the legacy duplicate for audit history")
        self.assertEqual(env_lines[2], "STOCK_LIST=300750")

    def test_apply_updates_falls_back_to_in_place_rewrite(self) -> None:
        self.env_path.write_text("STOCK_LIST=600519\n", encoding="utf-8")

        with patch("src.core.config_manager.os.replace", side_effect=OSError(errno.EXDEV, "cross-device")):
            self.manager.apply_updates(
                updates=[("STOCK_LIST", "000001")],
                sensitive_keys=set(),
                mask_token="******",
            )

        self.assertEqual(self.env_path.read_text(encoding="utf-8"), "STOCK_LIST=000001\n")

    def test_custom_webhook_template_placeholders_are_escaped_for_compose(self) -> None:
        template = '{"title":$title_json,"content":$content_json,"raw":$content,"name":"$OTHER"}'

        self.manager.apply_updates(
            updates=[("CUSTOM_WEBHOOK_BODY_TEMPLATE", template)],
            sensitive_keys=set(),
            mask_token="******",
        )

        env_content = self.env_path.read_text(encoding="utf-8")
        self.assertIn(
            'CUSTOM_WEBHOOK_BODY_TEMPLATE={"title":$$title_json,"content":$$content_json,'
            '"raw":$$content,"name":"$OTHER"}',
            env_content,
        )
        self.assertEqual(
            self.manager.read_config_map()["CUSTOM_WEBHOOK_BODY_TEMPLATE"],
            template,
        )

    def test_custom_webhook_template_braced_placeholders_are_escaped_for_compose(self) -> None:
        template = '{"title":${title_json},"content":${content_json},"name":"${OTHER}"}'

        self.manager.apply_updates(
            updates=[("CUSTOM_WEBHOOK_BODY_TEMPLATE", template)],
            sensitive_keys=set(),
            mask_token="******",
        )

        env_content = self.env_path.read_text(encoding="utf-8")
        self.assertIn(
            'CUSTOM_WEBHOOK_BODY_TEMPLATE={"title":$${title_json},'
            '"content":$${content_json},"name":"${OTHER}"}',
            env_content,
        )
        self.assertEqual(
            self.manager.read_config_map()["CUSTOM_WEBHOOK_BODY_TEMPLATE"],
            template,
        )

    def test_custom_webhook_template_canonicalizes_unescaped_existing_value(self) -> None:
        self.env_path.write_text(
            'CUSTOM_WEBHOOK_BODY_TEMPLATE={"content":$content_json}\n',
            encoding="utf-8",
        )

        self.manager.apply_updates(
            updates=[("CUSTOM_WEBHOOK_BODY_TEMPLATE", '{"content":$content_json}')],
            sensitive_keys=set(),
            mask_token="******",
        )

        self.assertEqual(
            self.env_path.read_text(encoding="utf-8"),
            'CUSTOM_WEBHOOK_BODY_TEMPLATE={"content":$$content_json}\n',
        )

    def test_custom_webhook_template_does_not_double_escape_existing_value(self) -> None:
        self.env_path.write_text(
            'CUSTOM_WEBHOOK_BODY_TEMPLATE={"content":$$content_json}\n',
            encoding="utf-8",
        )

        self.manager.apply_updates(
            updates=[("CUSTOM_WEBHOOK_BODY_TEMPLATE", '{"content":$content_json}')],
            sensitive_keys=set(),
            mask_token="******",
        )

        self.assertEqual(
            self.env_path.read_text(encoding="utf-8"),
            'CUSTOM_WEBHOOK_BODY_TEMPLATE={"content":$$content_json}\n',
        )
        self.assertEqual(
            self.manager.read_config_map()["CUSTOM_WEBHOOK_BODY_TEMPLATE"],
            '{"content":$content_json}',
        )

    def test_custom_webhook_template_plain_json_is_not_changed(self) -> None:
        template = '{"content":"plain json string"}'

        self.manager.apply_updates(
            updates=[("CUSTOM_WEBHOOK_BODY_TEMPLATE", template)],
            sensitive_keys=set(),
            mask_token="******",
        )

        self.assertEqual(
            self.env_path.read_text(encoding="utf-8"),
            f"CUSTOM_WEBHOOK_BODY_TEMPLATE={template}\n",
        )

    def test_non_template_settings_keep_dotenv_interpolation_semantics(self) -> None:
        self.env_path.write_text(
            "\n".join(
                [
                    "API_PORT=8000",
                    "WEBUI_PORT=${API_PORT}",
                    'CUSTOM_WEBHOOK_BODY_TEMPLATE={"content":$${content_json}}',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        config_map = self.manager.read_config_map()

        self.assertEqual(config_map["API_PORT"], "8000")
        self.assertEqual(config_map["WEBUI_PORT"], "8000")
        self.assertEqual(
            config_map["CUSTOM_WEBHOOK_BODY_TEMPLATE"],
            '{"content":${content_json}}',
        )

        self.manager.apply_updates(
            updates=[("WEBUI_PORT", config_map["WEBUI_PORT"])],
            sensitive_keys=set(),
            mask_token="******",
        )

        self.assertIn(
            "WEBUI_PORT=${API_PORT}\n",
            self.env_path.read_text(encoding="utf-8"),
        )

    def test_render_without_keys_removes_all_sensitive_assignments_and_preserves_structure(self) -> None:
        self.env_path.write_text(
            "# Public settings\nSTOCK_LIST=600519\n\n"
            "# Credentials stay local\nOPENAI_API_KEY=first-fake\n"
            "OPENAI_API_KEY=second-fake\nexport ANTHROPIC_API_KEY=third-fake\nLOG_LEVEL=INFO\n",
            encoding="utf-8",
        )

        rendered = self.manager.render_without_keys({"OPENAI_API_KEY", "ANTHROPIC_API_KEY"})

        self.assertEqual(
            rendered,
            "# Public settings\nSTOCK_LIST=600519\n\n"
            "# Credentials stay local\nLOG_LEVEL=INFO\n",
        )
        self.assertIn("OPENAI_API_KEY", self.manager.read_config_map())

    def test_assignment_keys_detects_sensitive_names_even_when_dotenv_value_is_malformed(self) -> None:
        self.env_path.write_text(
            'OPENAI_API_KEY="unterminated\nSTOCK_LIST=600519\n',
            encoding="utf-8",
        )

        self.assertEqual(
            self.manager.get_assignment_keys(),
            {"OPENAI_API_KEY", "STOCK_LIST"},
        )

    def test_remove_keys_atomically_removes_duplicates_without_touching_other_values(self) -> None:
        self.env_path.write_text(
            "OPENAI_API_KEY=first-fake\nSTOCK_LIST=600519\nOPENAI_API_KEY=second-fake\n",
            encoding="utf-8",
        )

        removed, version = self.manager.remove_keys({"OPENAI_API_KEY"})

        self.assertEqual(removed, ["OPENAI_API_KEY"])
        self.assertEqual(version, self.manager.get_config_version())
        self.assertEqual(self.env_path.read_text(encoding="utf-8"), "STOCK_LIST=600519\n")


if __name__ == "__main__":
    unittest.main()
