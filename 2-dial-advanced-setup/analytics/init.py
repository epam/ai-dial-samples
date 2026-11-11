"""Initialize local blob storage and the recommended ADAS catalog, once per volume."""

import base64
import hashlib
import hmac
import json
import os
from email.utils import formatdate
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def create_blob_container():
    date = formatdate(usegmt=True)
    headers = {"x-ms-date": date, "x-ms-version": "2021-12-02"}
    canonical = f"x-ms-date:{date}\nx-ms-version:2021-12-02\n/dialanalytics/logs\nrestype:container"
    signature = hmac.new(
        base64.b64decode(os.environ["ANALYTICS_BLOB_KEY"], validate=True),
        ("PUT" + "\n" * 12 + canonical).encode(),
        hashlib.sha256,
    ).digest()
    headers["Authorization"] = "SharedKey dialanalytics:" + base64.b64encode(signature).decode()
    request = Request(
        "http://dialanalytics.analytics-blob:10000/logs?restype=container",
        headers=headers, method="PUT",
    )
    try:
        with urlopen(request, timeout=30):
            pass
    except HTTPError as error:
        if error.code != 409 or b"ContainerAlreadyExists" not in error.read():
            raise


def api(path, body, content_type="application/json", method="POST"):
    request = Request(
        "http://analytics:5000/v1/" + path, data=body, method=method,
        headers={"Content-Type": content_type, "Api-Key": os.environ["DIAL_ANALYTICS_API_KEY"]},
    )
    try:
        with urlopen(request, timeout=180) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"{method} {path}: HTTP {error.code}: {error.read().decode()}") from error


def initialize_catalog():
    marker = Path("/state/catalog-initialized")
    if marker.exists():
        return
    bundle = Path(__file__).with_name("adas-catalog.json").read_bytes()
    body = (
        b'--catalog\r\nContent-Disposition: form-data; name="file"; filename="adas-catalog.json"'
        b'\r\nContent-Type: application/json\r\n\r\n' + bundle + b"\r\n--catalog--\r\n"
    )
    result = api("catalog/import?resolution_policy=SKIP_IF_EXISTS", body, "multipart/form-data; boundary=catalog")
    if result["outcome"] != "completed":
        raise RuntimeError(f"Catalog import failed: {result}")
    # Enrichments must run before the session aggregate that depends on them.
    for name in ("usage-client-identity-live", "usage-request-baggage-live", "sessions_rollup"):
        api(f"pipelines/{name}", b'{"enabled":true}', method="PATCH")
    marker.write_text("0.23.0-rc.0\n")


if __name__ == "__main__":
    create_blob_container()
    initialize_catalog()
    print("Analytics storage and catalog are ready.")
