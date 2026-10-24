import unittest

from fastapi.testclient import TestClient

from app import app


class ConfigurationTest(unittest.TestCase):
    def test_conversation_starters(self):
        with TestClient(app) as client:
            response = client.get(
                "/openai/deployments/essay-assistant-app/configuration",
                headers={"api-key": "test-key"},
            )

        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertNotIn("starter", schema.get("required", []))
        buttons = schema["properties"]["starter"]
        self.assertEqual(buttons["dial:widget"], "buttons")
        self.assertEqual(
            [
                (button["const"], button["title"], button["dial:widgetOptions"]["populateText"])
                for button in buttons["oneOf"]
            ],
            [
                (1, "About elephant in space", "Generate me one about elephant in space"),
                (2, "About dog that can sing", "Generate essay about dog that can sing"),
            ],
        )
        for button in buttons["oneOf"]:
            self.assertFalse(button["dial:widgetOptions"]["submit"])
