from pathlib import Path

from werkzeug.wrappers import Response

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer


class SalesServiceWorkerPage(BaseRenderer):
    def can_render(self):
        return self.path == "sales-worker.js"

    def render(self):
        worker_path = Path(frappe.get_app_path("sales_executive_app", "www", "sales-worker.js"))
        response = Response(worker_path.read_bytes(), mimetype="application/javascript")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Service-Worker-Allowed"] = "/"
        return response
