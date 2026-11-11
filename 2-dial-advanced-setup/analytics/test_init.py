"""Run with: python3 -m unittest discover -s analytics -p 'test_*.py'."""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import init


class InitializationTest(unittest.TestCase):
    def test_catalog_order_and_restart_preserve_admin_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "initialized"
            with patch.object(init, "Path", return_value=marker), patch.object(init, "api") as api:
                marker.with_name("adas-catalog.json").write_text('{}')
                api.return_value = {"outcome": "completed"}
                init.initialize_catalog()
                self.assertEqual(
                    [call.args[0] for call in api.call_args_list],
                    ["catalog/import?resolution_policy=SKIP_IF_EXISTS",
                     "pipelines/usage-client-identity-live",
                     "pipelines/usage-request-baggage-live", "pipelines/sessions_rollup"],
                )
                init.initialize_catalog()
                self.assertEqual(api.call_count, 4)

    def test_failed_import_does_not_mark_initialization_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "initialized"
            with patch.object(init, "Path", return_value=marker), patch.object(init, "api") as api:
                marker.with_name("adas-catalog.json").write_text('{}')
                api.return_value = {"outcome": "rollback_failed"}
                with self.assertRaisesRegex(RuntimeError, "Catalog import failed"):
                    init.initialize_catalog()
                self.assertFalse(marker.exists())
                self.assertEqual(api.call_count, 1)

    def test_blob_creation_only_ignores_existing_container(self):
        with patch.dict(init.os.environ, {"ANALYTICS_BLOB_KEY": "bG9jYWw="}):
            for code, body, accepted in (
                (409, b"<Code>ContainerAlreadyExists</Code>", True),
                (409, b"<Code>OtherConflict</Code>", False),
                (403, b"<Code>AuthenticationFailed</Code>", False),
            ):
                error = HTTPError("http://blob", code, "error", {}, io.BytesIO(body))
                with self.subTest(code=code, body=body), patch.object(init, "urlopen", side_effect=error):
                    if accepted:
                        init.create_blob_container()
                    else:
                        with self.assertRaises(HTTPError):
                            init.create_blob_container()
                error.close()

    def test_api_sends_credential_and_json(self):
        response = io.BytesIO(b'{"outcome":"completed"}')
        with patch.dict(init.os.environ, {"DIAL_ANALYTICS_API_KEY": "test-key"}), \
                patch.object(init, "urlopen", return_value=response) as open_url:
            result = init.api("pipelines/test", b'{"enabled":true}', method="PATCH")
            request = open_url.call_args.args[0]
            self.assertEqual(request.method, "PATCH")
            self.assertEqual(request.get_header("Api-key"), "test-key")
            self.assertEqual(json.loads(request.data), {"enabled": True})
            self.assertEqual(result, {"outcome": "completed"})


if __name__ == "__main__":
    unittest.main()
