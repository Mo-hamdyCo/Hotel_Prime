app_name = "hotel_prime"
app_title = "Hotel Mange"
app_publisher = "M.Hamdy"
app_description = "Help Hotels To Mange her WorkFlow"
app_email = "mohamedhamdy2539@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "hotel_prime",
# 		"logo": "/assets/hotel_prime/logo.png",
# 		"title": "Hotel Mange",
# 		"route": "/hotel_prime",
# 		"has_permission": "hotel_prime.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hotel_prime/css/hotel_prime.css"
# app_include_js = "/assets/hotel_prime/js/hotel_prime.js"

# include js, css files in header of web template
# web_include_css = "/assets/hotel_prime/css/hotel_prime.css"
# web_include_js = "/assets/hotel_prime/js/hotel_prime.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hotel_prime/public/scss/website"

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
# app_include_icons = "hotel_prime/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "hotel_prime.utils.jinja_methods",
# 	"filters": "hotel_prime.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "hotel_prime.install.before_install"
# after_install = "hotel_prime.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "hotel_prime.uninstall.before_uninstall"
# after_uninstall = "hotel_prime.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hotel_prime.utils.before_app_install"
# after_app_install = "hotel_prime.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "hotel_prime.utils.before_app_uninstall"
# after_app_uninstall = "hotel_prime.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hotel_prime.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
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
# 		"hotel_prime.tasks.all"
# 	],
# 	"daily": [
# 		"hotel_prime.tasks.daily"
# 	],
# 	"hourly": [
# 		"hotel_prime.tasks.hourly"
# 	],
# 	"weekly": [
# 		"hotel_prime.tasks.weekly"
# 	],
# 	"monthly": [
# 		"hotel_prime.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "hotel_prime.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hotel_prime.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "hotel_prime.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["hotel_prime.utils.before_request"]
# after_request = ["hotel_prime.utils.after_request"]

# Job Events
# ----------
# before_job = ["hotel_prime.utils.before_job"]
# after_job = ["hotel_prime.utils.after_job"]

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
# 	"hotel_prime.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

