"""Run: python3 -m unittest discover -s core-config-apply -p 'test_*.py'."""

import json
from pathlib import Path
import subprocess
import unittest


class ModelProviderMigrationTest(unittest.TestCase):
    def test_advertised_responses_gets_an_upstream_without_replacing_custom_one(self):
        model = {
            "interfaces": {"openaiResponses": {"mode": "passthrough"}},
            "upstreams": [
                {"interfaces": {"openaiChatCompletions": {"endpoint": "http://ollama:11434/v1/chat/completions"}}},
                {"interfaces": {
                    "openaiChatCompletions": {"endpoint": "http://ollama:11434/v1/chat/completions"},
                    "openaiResponses": {"endpoint": "http://custom/responses"},
                }},
            ],
        }
        migrate = Path(__file__).with_name("model-provider-migration.jq")
        actual = json.loads(subprocess.check_output(["jq", "-f", str(migrate)], input=json.dumps(model).encode()))
        self.assertEqual(actual["upstreams"][0]["interfaces"]["openaiResponses"]["endpoint"], "http://ollama:11434/v1/responses")
        self.assertEqual(actual["upstreams"][1], model["upstreams"][1])
        model["upstreams"] = None
        actual = json.loads(subprocess.check_output(["jq", "-f", str(migrate)], input=json.dumps(model).encode()))
        self.assertIsNone(actual["upstreams"])

    def test_prefixes_preserve_custom_settings_and_upstream_keys(self):
        original = {
            "displayName": "My edited model",
            "baseUrl": "http://adapter-dial-openai:5000",
            "interfaces": {"openaiEmbeddings": {"base_url": "http://adapter-dial-openai:5000/"}},
            "endpoint": "http://adapter-dial-bedrock:5000/openai/deployments/claude/chat/completions",
            "features": {"configurationEndpoint": "http://adapter-dial-vertexai:5000/configuration"},
            "upstreams": [{"endpoint": "http://ollama:11434/v1/chat/completions", "key": "unchanged-key"}],
            "custom": "http://adapter-dial-openai:50000/do-not-change",
            "key": "http://adapter-dial-openai:5000/credential-do-not-change",
            "userRoles": ["my-role"],
        }
        migrate = Path(__file__).with_name("model-provider-migration.jq")

        def run(value):
            return json.loads(subprocess.check_output(["jq", "-f", str(migrate)], input=json.dumps(value).encode()))

        actual = run(original)
        self.assertEqual(actual["baseUrl"], "http://model-provider:5000/compat/openai")
        self.assertEqual(actual["interfaces"]["openaiEmbeddings"]["base_url"], "http://model-provider:5000/compat/openai/")
        self.assertEqual(actual["endpoint"], "http://model-provider:5000/compat/bedrock/openai/deployments/claude/chat/completions")
        self.assertEqual(actual["features"]["configurationEndpoint"], "http://model-provider:5000/compat/vertexai/configuration")
        for field in ("displayName", "upstreams", "custom", "userRoles", "key"):
            self.assertEqual(actual[field], original[field])
        self.assertEqual(run(actual), actual)


if __name__ == "__main__":
    unittest.main()
