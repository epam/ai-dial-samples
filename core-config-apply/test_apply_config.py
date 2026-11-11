"""Against a disposable Core: TEST_CORE_URL=http://localhost:18059 python3 -m unittest discover -s core-config-apply."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import urllib.error
import urllib.request
import uuid


@unittest.skipUnless(os.environ.get("TEST_CORE_URL"), "requires a disposable Core")
class ApplyConfigTest(unittest.TestCase):
    def test_scheduler_readers_can_call_routes_but_cannot_edit_the_application(self):
        base_url = os.environ["TEST_CORE_URL"].rstrip("/")
        admin_key = os.environ.get("TEST_CORE_API_KEY", "dial_admin_api_key")
        reader_key = os.environ.get("TEST_CORE_READER_KEY", "dial_api_key")
        name = "applications/public/scheduler-access-test-" + uuid.uuid4().hex
        scheduler = Path(__file__).resolve().parents[1] / "core/2-dial-advanced-setup/scheduler.json"
        spec = json.loads(scheduler.read_text())["manifests"][1]["spec"]
        # Exercise Core's real route authorization without dispatching a scheduled job.
        spec["routes"]["api"].pop("upstreams")
        spec["routes"]["api"]["response"] = {"status": 200, "body": "{}"}

        def request(method, path, body=None, key=admin_key, headers=None):
            req = urllib.request.Request(
                base_url + path,
                data=json.dumps(body).encode() if body is not None else None,
                headers={"Api-Key": key, "Content-Type": "application/json", **(headers or {})},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                return json.loads(data) if data else None

        result = request("POST", "/v1/admin/apply", {"manifests": [{
            "kind": "Application", "name": name, "spec": spec,
        }]})
        self.assertEqual(result["failed"], 0)
        try:
            self.assertEqual(request("POST", "/v1/deployments/" + name + "/route/v1/schedules/",
                                     {}, key=reader_key), {})
            with self.assertRaises(urllib.error.HTTPError) as denied:
                request("PUT", "/v1/" + name, {}, key=reader_key)
            self.assertEqual(denied.exception.code, 403)
            denied.exception.close()
        finally:
            metadata = request("GET", "/v1/metadata/" + name)
            request("DELETE", "/v1/" + name, headers={"If-Match": metadata["etag"]})

    def test_upgrade_imports_public_manifest_and_preserves_existing_edits(self):
        base_url = os.environ["TEST_CORE_URL"].rstrip("/")
        api_key = os.environ.get("TEST_CORE_API_KEY", "dial_admin_api_key")
        name = "import-test-" + uuid.uuid4().hex
        platform_id = "applications/platform/" + name
        public_id = "applications/public/" + name

        def request(method, path, body=None, headers=None):
            req = urllib.request.Request(
                base_url + path,
                data=json.dumps(body).encode() if body is not None else None,
                headers={"Api-Key": api_key, "Content-Type": "application/json", **(headers or {})},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                return json.loads(data) if data else None

        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            simple = folder / "simple.json"
            advanced = folder / "advanced.json"
            simple.write_text(json.dumps({"applications": {name: {
                "displayName": "Original", "endpoint": "http://unused/chat/completions",
            }}}))
            advanced.write_text(json.dumps({"manifests": [{
                "kind": "Application", "name": public_id,
                "spec": {"displayName": "Public app", "endpoint": "http://unused/chat/completions"},
            }]}))
            env = {**os.environ, "CORE_URL": base_url, "API_KEY": api_key,
                   "STATE_FILE": str(folder / "state.json"), "CONFIG_FILES": str(simple)}

            def apply():
                subprocess.run(["sh", str(Path(__file__).with_name("apply-config.sh"))],
                               env=env, check=True, capture_output=True, timeout=30)

            try:
                apply()
                result = request("POST", "/v1/admin/apply", {"manifests": [{
                    "kind": "Application", "name": platform_id,
                    "spec": {"displayName": "Admin edit", "endpoint": "http://unused/chat/completions"},
                }]})
                self.assertEqual(result["failed"], 0)
                env["CONFIG_FILES"] += " " + str(advanced)
                apply()
                self.assertEqual(request("GET", "/v1/" + platform_id)["display_name"], "Admin edit")
                self.assertEqual(request("GET", "/v1/" + public_id)["display_name"], "Public app")
                state = (folder / "state.json").read_text()
                apply()
                self.assertEqual((folder / "state.json").read_text(), state)
            finally:
                for entity_id in (platform_id, public_id):
                    try:
                        metadata = request("GET", "/v1/metadata/" + entity_id)
                    except urllib.error.HTTPError as error:
                        if error.code == 404:
                            continue
                        raise
                    request("DELETE", "/v1/" + entity_id, headers={"If-Match": metadata["etag"]})
