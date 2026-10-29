# Copyright (c) 2026, Vintrosys and Contributors
# See license.txt

# import frappe
from datetime import datetime
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from sales_executive_app.api import summarize_attendance


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestShopVisit(IntegrationTestCase):
	"""
	Integration tests for ShopVisit.
	Use this class for testing interactions between multiple components.
	"""

	pass


class TestAttendanceSessions(TestCase):
	def test_working_hours_add_across_multiple_sessions(self):
		checkins = [
			SimpleNamespace(log_type="IN", time=datetime(2026, 10, 29, 8, 0)),
			SimpleNamespace(log_type="OUT", time=datetime(2026, 10, 29, 12, 0)),
			SimpleNamespace(log_type="IN", time=datetime(2026, 10, 29, 13, 0)),
			SimpleNamespace(log_type="OUT", time=datetime(2026, 10, 29, 17, 0)),
		]

		result = summarize_attendance(checkins)

		assert result["clock_in"] == datetime(2026, 10, 29, 8, 0)
		assert result["clock_out"] == datetime(2026, 10, 29, 17, 0)
		assert result["working_hours"] == 8
		assert not result["is_on_duty"]

	def test_clock_in_after_clock_out_is_an_active_session(self):
		checkins = [
			SimpleNamespace(log_type="IN", time=datetime(2026, 10, 29, 8, 0)),
			SimpleNamespace(log_type="OUT", time=datetime(2026, 10, 29, 12, 0)),
			SimpleNamespace(log_type="IN", time=datetime(2026, 10, 29, 13, 0)),
		]

		with patch("sales_executive_app.api.now_datetime", return_value=datetime(2026, 10, 29, 14, 30)):
			result = summarize_attendance(checkins)

		assert result["first_clock_in"] == datetime(2026, 10, 29, 8, 0)
		assert result["clock_in"] == datetime(2026, 10, 29, 13, 0)
		assert result["clock_out"] is None
		assert result["working_hours"] == 5.5
		assert result["is_on_duty"]
