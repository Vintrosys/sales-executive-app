app_name = "sales_executive_app"
app_title = "Sales Executive App"
app_publisher = "Vintrosys"
app_description = "A sales management application for managing sales activities, customer details, orders, and sales reports."
app_email = "raji.frappe@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "sales_executive_app",
# 		"logo": "/assets/sales_executive_app/logo.png",
# 		"title": "Sales Executive App",
# 		"route": "/sales_executive_app",
# 		"has_permission": "sales_executive_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sales_executive_app/css/sales_executive_app.css"
# app_include_js = "/assets/sales_executive_app/js/sales_executive_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/sales_executive_app/css/sales_executive_app.css"
# web_include_js = "/assets/sales_executive_app/js/sales_executive_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sales_executive_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sales_executive_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sales_executive_app.utils.jinja_methods",
# 	"filters": "sales_executive_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sales_executive_app.install.before_install"
# after_install = "sales_executive_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sales_executive_app.uninstall.before_uninstall"
# after_uninstall = "sales_executive_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sales_executive_app.utils.before_app_install"
# after_app_install = "sales_executive_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sales_executive_app.utils.before_app_uninstall"
# after_app_uninstall = "sales_executive_app.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "sales_executive_app.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sales_executive_app.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["sales_executive_app.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sales_executive_app.tasks.all"
# 	],
# 	"daily": [
# 		"sales_executive_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"sales_executive_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sales_executive_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sales_executive_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sales_executive_app.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "sales_executive_app.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sales_executive_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sales_executive_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sales_executive_app.utils.before_request"]
# after_request = ["sales_executive_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["sales_executive_app.utils.before_job"]
# after_job = ["sales_executive_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sales_executive_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "=", "Customer"],
            ["fieldname", "in", [
                "custom_shop_name",
                "custom_contact_person",
                "custom_shop_location_details",
                "custom_shop_latitude",
                "custom_geofence_radius",
                "custom_column_break_jdisr",
                "custom_shop_longitude",
                "custom_assigned_employee"
            ]],
        ],
    }
]