# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

"""
General Ledger Service Layer

This service class encapsulates core business logic for general ledger processing.
Introduced as part of service layer extraction refactoring to improve modularity
and reduce tight coupling in the accounts module.
"""

import copy

import frappe
from frappe.model.meta import get_field_precision
from frappe.utils import flt
from frappe.utils.caching import request_cache

import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from erpnext.accounts.doctype.budget.budget import validate_expense_against_budget


class GeneralLedgerService:
	"""
	Service class for General Ledger operations.
	
	This class provides a service layer for processing GL entries,
	helping to decouple business logic from direct database operations
	and improving testability and maintainability.
	"""

	@staticmethod
	def process_gl_map(gl_map, merge_entries=True, precision=None, from_repost=False):
		"""
		Process General Ledger Map entries.
		
		This method performs the following operations on GL entries:
		1. Distributes GL entries based on cost center allocation
		2. Merges similar entries to reduce redundancy
		3. Toggles debit/credit for negative values
		
		Args:
			gl_map (list): List of GL entry dictionaries
			merge_entries (bool): Whether to merge similar entries (default: True)
			precision (int): Decimal precision for calculations (default: None)
			from_repost (bool): Whether called from reposting process (default: False)
			
		Returns:
			list: Processed GL map entries
			
		Note:
			This method maintains all existing logic and behavior.
			No business rules or database interactions have been modified.
		"""
		if not gl_map:
			return []

		# Skip cost center distribution for Period Closing Vouchers
		if gl_map[0].voucher_type != "Period Closing Voucher":
			gl_map = GeneralLedgerService._distribute_gl_based_on_cost_center_allocation(
				gl_map, precision, from_repost
			)

		# Merge similar entries if requested
		if merge_entries:
			gl_map = GeneralLedgerService._merge_similar_entries(gl_map, precision)

		# Handle negative debit/credit values
		gl_map = GeneralLedgerService._toggle_debit_credit_if_negative(gl_map)

		return gl_map

	@staticmethod
	def _distribute_gl_based_on_cost_center_allocation(gl_map, precision=None, from_repost=False):
		"""
		Distribute GL entries based on cost center allocation percentages.
		
		When a cost center has allocation rules defined, this method splits
		the GL entry across multiple sub-cost centers based on the allocation
		percentages.
		
		Args:
			gl_map (list): List of GL entry dictionaries
			precision (int): Decimal precision for calculations
			from_repost (bool): Whether called from reposting process
			
		Returns:
			list: GL map with entries distributed across cost centers
		"""
		round_off_account, default_currency = frappe.get_cached_value(
			"Company", gl_map[0].company, ["round_off_account", "default_currency"]
		)
		
		if not precision:
			precision = get_field_precision(
				frappe.get_meta("GL Entry").get_field("debit"),
				currency=default_currency,
			)

		new_gl_map = []
		for d in gl_map:
			cost_center = d.get("cost_center")

			cost_center_allocation = GeneralLedgerService._get_cost_center_allocation_data(
				gl_map[0]["company"], gl_map[0]["posting_date"], cost_center
			)

			# No allocation rules, keep original entry
			if not cost_center_allocation:
				new_gl_map.append(d)
				continue

			# Validate budget against main cost center
			if not from_repost:
				validate_expense_against_budget(
					d, expense_amount=flt(d.debit, precision) - flt(d.credit, precision)
				)

			# Round-off account should not be split across cost centers
			if d.account == round_off_account:
				d.cost_center = cost_center_allocation[0][0]
				new_gl_map.append(d)
				continue

			# Split entry across allocated cost centers
			for sub_cost_center, percentage in cost_center_allocation:
				gle = copy.deepcopy(d)
				gle.cost_center = sub_cost_center
				for field in ("debit", "credit", "debit_in_account_currency", "credit_in_account_currency"):
					gle[field] = flt(flt(d.get(field)) * percentage / 100, precision)
				new_gl_map.append(gle)

		return new_gl_map

	@staticmethod
	@request_cache
	def _get_cost_center_allocation_data(company, posting_date, cost_center):
		"""
		Fetch cost center allocation data from database.
		
		Retrieves the allocation percentages for sub-cost centers
		based on the most recent valid allocation rules.
		
		Args:
			company (str): Company name
			posting_date (date): Posting date to check validity
			cost_center (str): Main cost center to get allocation for
			
		Returns:
			list: List of tuples (sub_cost_center, percentage)
		"""
		cost_center_allocation = frappe.db.get_value(
			"Cost Center Allocation",
			{
				"docstatus": 1,
				"company": company,
				"valid_from": ("<=", posting_date),
				"main_cost_center": cost_center,
			},
			pluck=True,
			order_by="valid_from desc",
		)

		if not cost_center_allocation:
			return []

		records = frappe.db.get_all(
			"Cost Center Allocation Percentage",
			{"parent": cost_center_allocation},
			["cost_center", "percentage"],
			as_list=True,
		)

		return records

	@staticmethod
	def _merge_similar_entries(gl_map, precision=None):
		"""
		Merge GL entries with identical account and dimension combinations.
		
		This reduces the number of GL entries by combining entries that
		have the same account, cost center, party, and accounting dimensions.
		
		Args:
			gl_map (list): List of GL entry dictionaries
			precision (int): Decimal precision for calculations
			
		Returns:
			list: Merged GL map with combined entries
		"""
		merged_gl_map = []
		accounting_dimensions = get_accounting_dimensions()
		merge_properties = GeneralLedgerService._get_merge_properties(accounting_dimensions)

		for entry in gl_map:
			# Skip entries marked to not be merged
			if entry._skip_merge:
				merged_gl_map.append(entry)
				continue

			# Create unique merge key based on account and dimensions
			entry.merge_key = GeneralLedgerService._get_merge_key(entry, merge_properties)
			
			# Check if similar entry already exists
			same_head = GeneralLedgerService._check_if_in_list(entry, merged_gl_map)
			if same_head:
				# Merge amounts into existing entry
				same_head.debit = flt(same_head.debit) + flt(entry.debit)
				same_head.debit_in_account_currency = flt(same_head.debit_in_account_currency) + flt(
					entry.debit_in_account_currency
				)
				same_head.debit_in_transaction_currency = flt(same_head.debit_in_transaction_currency) + flt(
					entry.debit_in_transaction_currency
				)
				same_head.credit = flt(same_head.credit) + flt(entry.credit)
				same_head.credit_in_account_currency = flt(same_head.credit_in_account_currency) + flt(
					entry.credit_in_account_currency
				)
				same_head.credit_in_transaction_currency = flt(same_head.credit_in_transaction_currency) + flt(
					entry.credit_in_transaction_currency
				)
			else:
				merged_gl_map.append(entry)

		company = gl_map[0].company if gl_map else erpnext.get_default_company()
		company_currency = erpnext.get_company_currency(company)

		if not precision:
			precision = get_field_precision(
				frappe.get_meta("GL Entry").get_field("debit"), currency=company_currency
			)

		# Filter out entries with zero debit and credit (except Exchange Gain/Loss Journal Entries)
		merged_gl_map = filter(
			lambda x: flt(x.debit, precision) != 0
			or flt(x.credit, precision) != 0
			or (
				x.voucher_type == "Journal Entry"
				and frappe.get_cached_value("Journal Entry", x.voucher_no, "voucher_type")
				== "Exchange Gain Or Loss"
			),
			merged_gl_map,
		)
		merged_gl_map = list(merged_gl_map)

		return merged_gl_map

	@staticmethod
	def _get_merge_properties(dimensions=None):
		"""
		Get list of fields to use for merging entries.
		
		Returns the field names that define when two entries are
		considered "similar" and can be merged.
		
		Args:
			dimensions (list): List of accounting dimensions
			
		Returns:
			list: Field names to use for merge key
		"""
		merge_properties = [
			"account",
			"cost_center",
			"party",
			"party_type",
			"voucher_detail_no",
			"against_voucher",
			"against_voucher_type",
			"project",
			"finance_book",
			"voucher_no",
			"advance_voucher_type",
			"advance_voucher_no",
		]
		if dimensions:
			merge_properties.extend(dimensions)
		return merge_properties

	@staticmethod
	def _get_merge_key(entry, merge_properties):
		"""
		Generate unique merge key for a GL entry.
		
		Args:
			entry (dict): GL entry dictionary
			merge_properties (list): List of fields to include in key
			
		Returns:
			tuple: Unique key identifying the entry combination
		"""
		merge_key = []
		for fieldname in merge_properties:
			merge_key.append(entry.get(fieldname, ""))

		return tuple(merge_key)

	@staticmethod
	def _check_if_in_list(gle, gl_map):
		"""
		Check if a GL entry with the same merge key exists in the list.
		
		Args:
			gle (dict): GL entry to check
			gl_map (list): List of existing GL entries
			
		Returns:
			dict or None: Matching entry if found, None otherwise
		"""
		for e in gl_map:
			if e.merge_key == gle.merge_key:
				return e
		return None

	@staticmethod
	def _toggle_debit_credit_if_negative(gl_map):
		"""
		Handle negative values in debit and credit fields.
		
		Converts negative debits to credits and vice versa,
		ensuring all values are positive in the correct column.
		Also handles net value posting scenarios.
		
		Args:
			gl_map (list): List of GL entry dictionaries
			
		Returns:
			list: GL map with corrected debit/credit values
		"""
		debit_credit_field_map = {
			"debit": "credit",
			"debit_in_account_currency": "credit_in_account_currency",
			"debit_in_transaction_currency": "credit_in_transaction_currency",
		}

		for entry in gl_map:
			# Process each debit/credit field pair
			for debit_field, credit_field in debit_credit_field_map.items():
				debit = flt(entry.get(debit_field))
				credit = flt(entry.get(credit_field))

				# If both are negative and equal, make them positive
				if debit < 0 and credit < 0 and debit == credit:
					debit *= -1
					credit *= -1

				# If debit is negative, move to credit
				if debit < 0:
					credit = credit - debit
					debit = 0.0

				# If credit is negative, move to debit
				if credit < 0:
					debit = debit - credit
					credit = 0.0

				# Handle net value posting
				# In some scenarios net value needs to be shown in the ledger
				# This method updates net values as debit or credit
				if entry.post_net_value and debit and credit:
					if debit > credit:
						debit = debit - credit
						credit = 0.0
					else:
						credit = credit - debit
						debit = 0.0

				entry[debit_field] = debit
				entry[credit_field] = credit

		return gl_map
