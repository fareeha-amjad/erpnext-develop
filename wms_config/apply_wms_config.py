"""
Site-level ERPNext config approximating Laravel WMS flows.
Lives in this repo under wms_config/ (not under sites/.../private).

Applies Custom Fields, Workflows, Notifications, Workspace, perms to a site DB.
Does not patch erpnext DocType Python.

Run against the live bench site:

  cd ~/frappe-bench-fresh
  bench --site fresh.localhost console

  >>> import importlib.util
  >>> p = "/Users/fareehaamjad/frappe-bench-fresh/apps/erpnext/wms_config/apply_wms_config.py"
  >>> s = importlib.util.spec_from_file_location("wms_config", p)
  >>> m = importlib.util.module_from_spec(s); s.loader.exec_module(m); m.apply()
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def apply():
	frappe.connect()
	_ensure_roles()
	_custom_fields()
	_workflows()
	_notifications()
	_permissions()
	_workspace()
	_branding()
	frappe.clear_cache()
	frappe.db.commit()
	print("WMS config applied successfully")


def _ensure_roles():
	for role in (
		"Estimation Manager",
		"Project Director",
		"Budget Controller",
		"Vendor",
		"Technician",
		"Manager",
		"Member",
	):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
			print("created role", role)


def _custom_fields():
	"""WMS-ish tracking fields (status stages still driven by Workflow)."""
	fields = {
		"Material Request": [
			{
				"fieldname": "wms_section",
				"fieldtype": "Section Break",
				"label": "WMS",
				"insert_after": "schedule_date",
			},
			{
				"fieldname": "wms_flow",
				"fieldtype": "Select",
				"label": "WMS Flow",
				"options": "\nMRF Purchase\nWarehouse Issue\nWarehouse Transfer",
				"insert_after": "wms_section",
				"description": "Set from Material Request Type; used by workflow conditions.",
			},
			{
				"fieldname": "wms_notes",
				"fieldtype": "Small Text",
				"label": "WMS Notes",
				"insert_after": "wms_flow",
			},
		],
		"Purchase Order": [
			{
				"fieldname": "wms_section",
				"fieldtype": "Section Break",
				"label": "WMS / Vendor",
				"insert_after": "schedule_date",
			},
			{
				"fieldname": "wms_receive_mode",
				"fieldtype": "Select",
				"label": "Receive Mode",
				"options": "Partial Allowed\nFull Only",
				"default": "Partial Allowed",
				"insert_after": "wms_section",
			},
			{
				"fieldname": "wms_sent_to_vendor_on",
				"fieldtype": "Datetime",
				"label": "Sent to Vendor On",
				"insert_after": "wms_receive_mode",
				"read_only": 1,
			},
			{
				"fieldname": "wms_vendor_ack_on",
				"fieldtype": "Datetime",
				"label": "Vendor Acknowledged On",
				"insert_after": "wms_sent_to_vendor_on",
				"read_only": 1,
			},
			{
				"fieldname": "wms_vendor_column",
				"fieldtype": "Column Break",
				"insert_after": "wms_vendor_ack_on",
			},
			{
				"fieldname": "wms_mrf_reference",
				"fieldtype": "Link",
				"label": "Source Material Request",
				"options": "Material Request",
				"insert_after": "wms_vendor_column",
			},
			{
				"fieldname": "wms_vendor_remarks",
				"fieldtype": "Small Text",
				"label": "Vendor Remarks",
				"insert_after": "wms_mrf_reference",
			},
		],
		"Purchase Receipt": [
			{
				"fieldname": "wms_section",
				"fieldtype": "Section Break",
				"label": "WMS Receiving",
				"insert_after": "supplier_delivery_note",
			},
			{
				"fieldname": "wms_truck_no",
				"fieldtype": "Data",
				"label": "Truck / Vehicle No",
				"insert_after": "wms_section",
			},
			{
				"fieldname": "wms_driver_name",
				"fieldtype": "Data",
				"label": "Driver Name",
				"insert_after": "wms_truck_no",
			},
			{
				"fieldname": "wms_gate_column",
				"fieldtype": "Column Break",
				"insert_after": "wms_driver_name",
			},
			{
				"fieldname": "wms_gate_scanned_on",
				"fieldtype": "Datetime",
				"label": "Gate Scanned On",
				"insert_after": "wms_gate_column",
				"read_only": 1,
			},
			{
				"fieldname": "wms_qc_summary",
				"fieldtype": "Select",
				"label": "QC Summary",
				"options": "\nPending\nAll Approved\nPartial On Hold\nHas Rejected",
				"insert_after": "wms_gate_scanned_on",
			},
			{
				"fieldname": "wms_receiving_notes",
				"fieldtype": "Small Text",
				"label": "Receiving Notes",
				"insert_after": "wms_qc_summary",
			},
		],
		"Stock Entry": [
			{
				"fieldname": "wms_section",
				"fieldtype": "Section Break",
				"label": "WMS",
				"insert_after": "stock_entry_type",
			},
			{
				"fieldname": "wms_reason",
				"fieldtype": "Select",
				"label": "WMS Reason",
				"options": "\nProject Issue\nReturn Usable\nReturn Damaged\nReturn Scrap\nRebalance Transfer\nProject Relocation\nCorrection\nCycle Count\nTransit Loss",
				"insert_after": "wms_section",
			},
			{
				"fieldname": "wms_source_mr",
				"fieldtype": "Link",
				"label": "Source Material Request",
				"options": "Material Request",
				"insert_after": "wms_reason",
			},
			{
				"fieldname": "wms_acknowledged_by",
				"fieldtype": "Data",
				"label": "Acknowledged By",
				"insert_after": "wms_source_mr",
			},
		],
		"Stock Reconciliation": [
			{
				"fieldname": "wms_section",
				"fieldtype": "Section Break",
				"label": "WMS Cycle Count",
				"insert_after": "purpose",
			},
			{
				"fieldname": "wms_count_scope",
				"fieldtype": "Select",
				"label": "Count Scope",
				"options": "Full Warehouse\nCategory\nLocation\nItem\nABC",
				"insert_after": "wms_section",
			},
			{
				"fieldname": "wms_blind_count",
				"fieldtype": "Check",
				"label": "Blind Count",
				"insert_after": "wms_count_scope",
			},
			{
				"fieldname": "wms_counter",
				"fieldtype": "Link",
				"label": "Primary Counter",
				"options": "User",
				"insert_after": "wms_blind_count",
			},
		],
		"Project": [
			{
				"fieldname": "wms_section",
				"fieldtype": "Section Break",
				"label": "WMS Budget",
				"insert_after": "estimated_costing",
			},
			{
				"fieldname": "wms_budget_currency",
				"fieldtype": "Link",
				"label": "Budget Currency",
				"options": "Currency",
				"insert_after": "wms_section",
			},
			{
				"fieldname": "wms_budget_status",
				"fieldtype": "Select",
				"label": "WMS Project Status",
				"options": "Draft\nActive\nOn Hold\nCompleted\nCancelled",
				"default": "Active",
				"insert_after": "wms_budget_currency",
			},
			{
				"fieldname": "wms_budget_notes",
				"fieldtype": "Small Text",
				"label": "Budget Notes",
				"insert_after": "wms_budget_status",
				"description": "Full project-item qty/reserved/used ledger needs custom DocTypes later.",
			},
		],
	}
	create_custom_fields(fields, update=True)
	print("custom fields upserted")


def _ensure_workflow_state(name: str, style: str | None = None):
	if frappe.db.exists("Workflow State", name):
		return
	doc = frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": name})
	if style:
		doc.style = style
	doc.insert(ignore_permissions=True)


def _ensure_workflow_action(name: str):
	if frappe.db.exists("Workflow Action Master", name):
		return
	frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": name}).insert(
		ignore_permissions=True
	)


def _replace_workflow(name: str, payload: dict):
	"""Create or fully replace a workflow definition."""
	for state in payload["states"]:
		_ensure_workflow_state(state["state"], state.get("style"))
	for tr in payload["transitions"]:
		_ensure_workflow_action(tr["action"])

	if frappe.db.exists("Workflow", name):
		frappe.delete_doc("Workflow", name, force=1, ignore_permissions=True)

	doc = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": name,
			"document_type": payload["document_type"],
			"is_active": 1,
			"override_status": 0,
			"send_email_alert": 1,
			"workflow_state_field": "workflow_state",
			"states": [
				{
					"state": s["state"],
					"doc_status": s.get("doc_status", "0"),
					"allow_edit": s.get("allow_edit", "All"),
					"update_field": s.get("update_field"),
					"update_value": s.get("update_value"),
				}
				for s in payload["states"]
			],
			"transitions": [
				{
					"state": t["state"],
					"action": t["action"],
					"next_state": t["next_state"],
					"allowed": t["allowed"],
					"allow_self_approval": 1,
					"condition": t.get("condition") or "",
				}
				for t in payload["transitions"]
			],
		}
	)
	doc.insert(ignore_permissions=True)
	print("workflow", name)


def _workflows():
	# --- Material Request: Purchase MRF ladder + Issue/Transfer warehouse path ---
	_replace_workflow(
		"MRF Approval",
		{
			"document_type": "Material Request",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": "Projects Manager", "style": "Primary"},
				{"state": "Pending Estimation", "doc_status": "0", "allow_edit": "Estimation Manager", "style": "Warning"},
				{"state": "Pending Director", "doc_status": "0", "allow_edit": "Project Director", "style": "Warning"},
				{"state": "Pending Budget", "doc_status": "0", "allow_edit": "Budget Controller", "style": "Warning"},
				{
					"state": "Pending Procurement",
					"doc_status": "1",
					"allow_edit": "Purchase User",
					"style": "Success",
				},
				{"state": "Pending Warehouse Approval", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Warning"},
				{"state": "Issue Approved", "doc_status": "1", "allow_edit": "Stock User", "style": "Success"},
				{"state": "Rejected", "doc_status": "0", "allow_edit": "Projects Manager", "style": "Danger"},
				{"state": "Cancelled", "doc_status": "0", "allow_edit": "Projects Manager", "style": "Inverse"},
			],
			"transitions": [
				# Purchase / MRF path
				{
					"state": "Draft",
					"action": "Submit for Estimation",
					"next_state": "Pending Estimation",
					"allowed": "Projects Manager",
					"condition": 'doc.material_request_type == "Purchase"',
				},
				{
					"state": "Pending Estimation",
					"action": "Approve Estimation",
					"next_state": "Pending Director",
					"allowed": "Estimation Manager",
					"condition": 'doc.material_request_type == "Purchase"',
				},
				{
					"state": "Pending Estimation",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Estimation Manager",
				},
				{
					"state": "Pending Director",
					"action": "Approve Director",
					"next_state": "Pending Budget",
					"allowed": "Project Director",
					"condition": 'doc.material_request_type == "Purchase"',
				},
				{
					"state": "Pending Director",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Project Director",
				},
				{
					"state": "Pending Budget",
					"action": "Approve Budget",
					"next_state": "Pending Procurement",
					"allowed": "Budget Controller",
					"condition": 'doc.material_request_type == "Purchase"',
				},
				{
					"state": "Pending Budget",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Budget Controller",
				},
				# Warehouse Issue / Transfer path (technician stock requests)
				{
					"state": "Draft",
					"action": "Submit for Warehouse Approval",
					"next_state": "Pending Warehouse Approval",
					"allowed": "Technician",
					"condition": 'doc.material_request_type in ("Material Issue", "Material Transfer")',
				},
				{
					"state": "Draft",
					"action": "Submit for Warehouse Approval",
					"next_state": "Pending Warehouse Approval",
					"allowed": "Stock User",
					"condition": 'doc.material_request_type in ("Material Issue", "Material Transfer")',
				},
				{
					"state": "Pending Warehouse Approval",
					"action": "Approve Issue",
					"next_state": "Issue Approved",
					"allowed": "Stock Manager",
					"condition": 'doc.material_request_type in ("Material Issue", "Material Transfer")',
				},
				{
					"state": "Pending Warehouse Approval",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Stock Manager",
				},
				# Cancels
				{"state": "Draft", "action": "Cancel", "next_state": "Cancelled", "allowed": "Projects Manager"},
				{
					"state": "Pending Estimation",
					"action": "Cancel",
					"next_state": "Cancelled",
					"allowed": "Projects Manager",
				},
				{
					"state": "Pending Director",
					"action": "Cancel",
					"next_state": "Cancelled",
					"allowed": "Projects Manager",
				},
				{
					"state": "Pending Budget",
					"action": "Cancel",
					"next_state": "Cancelled",
					"allowed": "Projects Manager",
				},
				{
					"state": "Pending Warehouse Approval",
					"action": "Cancel",
					"next_state": "Cancelled",
					"allowed": "Stock Manager",
				},
			],
		},
	)

	# --- Purchase Order vendor lifecycle (config approximation) ---
	_replace_workflow(
		"WMS Purchase Order",
		{
			"document_type": "Purchase Order",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": "Purchase User", "style": "Primary"},
				{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Purchase Manager", "style": "Warning"},
				{"state": "Approved", "doc_status": "1", "allow_edit": "Purchase User", "style": "Success"},
				{"state": "Vendor Pending", "doc_status": "1", "allow_edit": "Vendor", "style": "Warning"},
				{"state": "Vendor Accepted", "doc_status": "1", "allow_edit": "Vendor", "style": "Success"},
				{"state": "Vendor Rejected", "doc_status": "1", "allow_edit": "Purchase User", "style": "Danger"},
				{"state": "Closed", "doc_status": "1", "allow_edit": "Accounts User", "style": "Inverse"},
				{"state": "Cancelled", "doc_status": "0", "allow_edit": "Purchase Manager", "style": "Inverse"},
			],
			"transitions": [
				{
					"state": "Draft",
					"action": "Submit for Approval",
					"next_state": "Pending Approval",
					"allowed": "Purchase User",
				},
				{
					"state": "Pending Approval",
					"action": "Approve",
					"next_state": "Approved",
					"allowed": "Purchase Manager",
				},
				{
					"state": "Pending Approval",
					"action": "Reject",
					"next_state": "Draft",
					"allowed": "Purchase Manager",
				},
				{
					"state": "Approved",
					"action": "Send to Vendor",
					"next_state": "Vendor Pending",
					"allowed": "Purchase User",
				},
				{
					"state": "Vendor Pending",
					"action": "Vendor Accept",
					"next_state": "Vendor Accepted",
					"allowed": "Vendor",
				},
				{
					"state": "Vendor Pending",
					"action": "Vendor Reject",
					"next_state": "Vendor Rejected",
					"allowed": "Vendor",
				},
				{
					"state": "Vendor Accepted",
					"action": "Close PO",
					"next_state": "Closed",
					"allowed": "Accounts User",
				},
				{
					"state": "Approved",
					"action": "Close PO",
					"next_state": "Closed",
					"allowed": "Accounts User",
				},
				{"state": "Draft", "action": "Cancel", "next_state": "Cancelled", "allowed": "Purchase Manager"},
				{
					"state": "Pending Approval",
					"action": "Cancel",
					"next_state": "Cancelled",
					"allowed": "Purchase Manager",
				},
			],
		},
	)

	# --- Purchase Receipt receiving stages (stock posts only on final Complete) ---
	_replace_workflow(
		"WMS Goods Receipt",
		{
			"document_type": "Purchase Receipt",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": "Vendor", "style": "Primary"},
				{"state": "Dispatched", "doc_status": "0", "allow_edit": "Vendor", "style": "Warning"},
				{"state": "At Gate", "doc_status": "0", "allow_edit": "Stock User", "style": "Warning"},
				{"state": "Receiving", "doc_status": "0", "allow_edit": "Stock User", "style": "Warning"},
				{"state": "QC", "doc_status": "0", "allow_edit": "Quality Manager", "style": "Warning"},
				{"state": "Ready to Post", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Success"},
				{"state": "Completed", "doc_status": "1", "allow_edit": "Stock Manager", "style": "Success"},
				{"state": "Cancelled", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Inverse"},
			],
			"transitions": [
				{"state": "Draft", "action": "Dispatch", "next_state": "Dispatched", "allowed": "Vendor"},
				{"state": "Draft", "action": "Dispatch", "next_state": "Dispatched", "allowed": "Purchase User"},
				{"state": "Dispatched", "action": "Gate Scan", "next_state": "At Gate", "allowed": "Stock User"},
				{"state": "At Gate", "action": "Start Receiving", "next_state": "Receiving", "allowed": "Stock User"},
				{"state": "Receiving", "action": "Send to QC", "next_state": "QC", "allowed": "Stock User"},
				{"state": "QC", "action": "QC Complete", "next_state": "Ready to Post", "allowed": "Quality Manager"},
				{
					"state": "Ready to Post",
					"action": "Post Stock",
					"next_state": "Completed",
					"allowed": "Stock Manager",
				},
				{"state": "Draft", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{"state": "Dispatched", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{"state": "At Gate", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{"state": "Receiving", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{"state": "QC", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
			],
		},
	)

	# --- Stock Entry: issue / transfer / return operational stages ---
	_replace_workflow(
		"WMS Stock Movement",
		{
			"document_type": "Stock Entry",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": "Stock User", "style": "Primary"},
				{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Warning"},
				{"state": "In Transit", "doc_status": "0", "allow_edit": "Stock User", "style": "Warning"},
				{"state": "Pending Receive", "doc_status": "0", "allow_edit": "Stock User", "style": "Warning"},
				{"state": "Posted", "doc_status": "1", "allow_edit": "Stock Manager", "style": "Success"},
				{"state": "Cancelled", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Inverse"},
			],
			"transitions": [
				{
					"state": "Draft",
					"action": "Submit for Approval",
					"next_state": "Pending Approval",
					"allowed": "Stock User",
				},
				{
					"state": "Draft",
					"action": "Submit for Approval",
					"next_state": "Pending Approval",
					"allowed": "Technician",
				},
				{
					"state": "Pending Approval",
					"action": "Approve & Post",
					"next_state": "Posted",
					"allowed": "Stock Manager",
					"condition": 'doc.stock_entry_type in ("Material Issue", "Material Receipt")',
				},
				{
					"state": "Pending Approval",
					"action": "Dispatch",
					"next_state": "In Transit",
					"allowed": "Stock Manager",
					"condition": 'doc.stock_entry_type == "Material Transfer"',
				},
				{
					"state": "In Transit",
					"action": "Mark Arrived",
					"next_state": "Pending Receive",
					"allowed": "Stock User",
				},
				{
					"state": "Pending Receive",
					"action": "Receive & Post",
					"next_state": "Posted",
					"allowed": "Stock Manager",
				},
				{
					"state": "Pending Approval",
					"action": "Reject",
					"next_state": "Draft",
					"allowed": "Stock Manager",
				},
				{"state": "Draft", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{
					"state": "Pending Approval",
					"action": "Cancel",
					"next_state": "Cancelled",
					"allowed": "Stock Manager",
				},
				{"state": "In Transit", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
			],
		},
	)

	# --- Stock Reconciliation as cycle-count session ---
	_replace_workflow(
		"WMS Cycle Count",
		{
			"document_type": "Stock Reconciliation",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Primary"},
				{"state": "In Progress", "doc_status": "0", "allow_edit": "Stock User", "style": "Warning"},
				{"state": "Pending Review", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Warning"},
				{"state": "Approved", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Success"},
				{"state": "Posted", "doc_status": "1", "allow_edit": "Stock Manager", "style": "Success"},
				{"state": "Cancelled", "doc_status": "0", "allow_edit": "Stock Manager", "style": "Inverse"},
			],
			"transitions": [
				{"state": "Draft", "action": "Start Count", "next_state": "In Progress", "allowed": "Stock Manager"},
				{
					"state": "In Progress",
					"action": "Submit for Review",
					"next_state": "Pending Review",
					"allowed": "Stock User",
				},
				{
					"state": "Pending Review",
					"action": "Approve Count",
					"next_state": "Approved",
					"allowed": "Stock Manager",
				},
				{
					"state": "Pending Review",
					"action": "Send Back",
					"next_state": "In Progress",
					"allowed": "Stock Manager",
				},
				{"state": "Approved", "action": "Post Adjustment", "next_state": "Posted", "allowed": "Stock Manager"},
				{"state": "Draft", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{"state": "In Progress", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
				{"state": "Pending Review", "action": "Cancel", "next_state": "Cancelled", "allowed": "Stock Manager"},
			],
		},
	)


def _upsert_notification(name: str, values: dict):
	if frappe.db.exists("Notification", name):
		doc = frappe.get_doc("Notification", name)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Notification", "name": name, **values})
		doc.insert(ignore_permissions=True)
	print("notification", name)


def _notifications():
	common = {
		"channel": "Email",
		"enabled": 1,
		"send_system_notification": 1,
		"sender_email": None,
	}
	specs = [
		(
			"WMS MR Pending Estimation",
			{
				**common,
				"document_type": "Material Request",
				"event": "Value Change",
				"value_changed": "workflow_state",
				"condition": 'doc.workflow_state=="Pending Estimation"',
				"subject": "MRF {{ doc.name }} awaiting Estimation",
				"message": "Material Request <b>{{ doc.name }}</b> is Pending Estimation.",
				"recipients": [{"receiver_by_role": "Estimation Manager"}],
			},
		),
		(
			"WMS MR Pending Director",
			{
				**common,
				"document_type": "Material Request",
				"event": "Value Change",
				"value_changed": "workflow_state",
				"condition": 'doc.workflow_state=="Pending Director"',
				"subject": "MRF {{ doc.name }} awaiting Director",
				"message": "Material Request <b>{{ doc.name }}</b> is Pending Director approval.",
				"recipients": [{"receiver_by_role": "Project Director"}],
			},
		),
		(
			"WMS MR Pending Budget",
			{
				**common,
				"document_type": "Material Request",
				"event": "Value Change",
				"value_changed": "workflow_state",
				"condition": 'doc.workflow_state=="Pending Budget"',
				"subject": "MRF {{ doc.name }} awaiting Budget",
				"message": "Material Request <b>{{ doc.name }}</b> is Pending Budget approval.",
				"recipients": [{"receiver_by_role": "Budget Controller"}],
			},
		),
		(
			"WMS PO Vendor Pending",
			{
				**common,
				"document_type": "Purchase Order",
				"event": "Value Change",
				"value_changed": "workflow_state",
				"condition": 'doc.workflow_state=="Vendor Pending"',
				"subject": "PO {{ doc.name }} awaiting vendor response",
				"message": "Purchase Order <b>{{ doc.name }}</b> was sent and is Vendor Pending.",
				"recipients": [{"receiver_by_role": "Vendor"}],
			},
		),
		(
			"WMS PR At Gate",
			{
				**common,
				"document_type": "Purchase Receipt",
				"event": "Value Change",
				"value_changed": "workflow_state",
				"condition": 'doc.workflow_state=="At Gate"',
				"subject": "Receipt {{ doc.name }} at gate",
				"message": "Purchase Receipt <b>{{ doc.name }}</b> is At Gate — start receiving.",
				"recipients": [{"receiver_by_role": "Stock User"}],
			},
		),
		(
			"WMS PR QC",
			{
				**common,
				"document_type": "Purchase Receipt",
				"event": "Value Change",
				"value_changed": "workflow_state",
				"condition": 'doc.workflow_state=="QC"',
				"subject": "Receipt {{ doc.name }} awaiting QC",
				"message": "Purchase Receipt <b>{{ doc.name }}</b> is in QC.",
				"recipients": [{"receiver_by_role": "Quality Manager"}],
			},
		),
	]
	for name, values in specs:
		try:
			_upsert_notification(name, values)
		except Exception as e:
			print("notification skip", name, e)


def _set_perm(doctype: str, role: str, **rights):
	"""Set role permissions via Frappe helpers (Custom DocPerm)."""
	from frappe.permissions import add_permission, update_permission_property

	if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
		add_permission(doctype, role, 0)
	# always ensure read at minimum
	rights = {"read": 1, **rights}
	for prop, val in rights.items():
		update_permission_property(doctype, role, 0, prop, 1 if val else 0)


def _permissions():
	# Vendor: see/respond to PO + create draft receipts (shipments)
	_set_perm("Purchase Order", "Vendor", read=1, write=1, print=1, report=1, email=1, share=1)
	_set_perm("Purchase Receipt", "Vendor", read=1, write=1, create=1, print=1, report=1)
	_set_perm("Supplier", "Vendor", read=1, report=1, print=1)
	_set_perm("Item", "Vendor", read=1, report=1, print=1)

	# Technician: create issue MRs + view stock
	_set_perm("Material Request", "Technician", read=1, write=1, create=1, report=1, print=1)
	_set_perm("Stock Entry", "Technician", read=1, write=1, create=1, report=1)
	_set_perm("Item", "Technician", read=1, report=1)
	_set_perm("Warehouse", "Technician", read=1, report=1)
	_set_perm("Project", "Technician", read=1, report=1)

	# Estimation / Director / Budget: MR read + write for workflow edits
	for role in ("Estimation Manager", "Project Director", "Budget Controller"):
		_set_perm("Material Request", role, read=1, write=1, report=1, print=1)
		_set_perm("Project", role, read=1, report=1)
		_set_perm("Item", role, read=1, report=1)

	# Quality on PR
	_set_perm("Purchase Receipt", "Quality Manager", read=1, write=1, report=1, print=1, submit=1)

	# Stock manager full-ish on WMS docs
	for dt in ("Stock Entry", "Stock Reconciliation", "Purchase Receipt", "Material Request"):
		_set_perm(dt, "Stock Manager", read=1, write=1, create=1, submit=1, cancel=1, report=1, print=1)

	print("permissions updated")
	frappe.db.commit()
	frappe.clear_cache()


def _workspace():
	name = "WMS"
	if frappe.db.exists("Workspace", name):
		frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)

	links = [
		("Card Break", "MRF / Buying", None),
		("Link", "Material Request", "Material Request"),
		("Link", "Purchase Order", "Purchase Order"),
		("Link", "Purchase Receipt", "Purchase Receipt"),
		("Link", "Supplier", "Supplier"),
		("Link", "Project", "Project"),
		("Card Break", "Warehouse Ops", None),
		("Link", "Stock Entry", "Stock Entry"),
		("Link", "Stock Reconciliation", "Stock Reconciliation"),
		("Link", "Warehouse", "Warehouse"),
		("Link", "Item", "Item"),
		("Link", "Quality Inspection", "Quality Inspection"),
		("Card Break", "Setup", None),
		("Link", "Workflow", "Workflow"),
		("Link", "Role", "Role"),
		("Link", "Notification", "Notification"),
	]

	content = []
	# simple header + shortcut blocks using Workspace v2-ish structure
	doc = frappe.get_doc(
		{
			"doctype": "Workspace",
			"label": name,
			"title": name,
			"name": name,
			"public": 1,
			"is_hidden": 0,
			"module": "Stock",
			"icon": "stock",
			"content": frappe.as_json(
				[
					{"id": "wms_header", "type": "header", "data": {"text": "<span>WMS Flows (ERPNext config)</span>", "col": 12}},
					{
						"id": "wms_spacer",
						"type": "spacer",
						"data": {"col": 12},
					},
					{"id": "wms_card_mrf", "type": "card", "data": {"card_name": "MRF / Buying", "col": 4}},
					{"id": "wms_card_wh", "type": "card", "data": {"card_name": "Warehouse Ops", "col": 4}},
					{"id": "wms_card_setup", "type": "card", "data": {"card_name": "Setup", "col": 4}},
				]
			),
			"links": [
				{
					"label": label,
					"type": typ,
					"link_type": "DocType" if typ == "Link" else None,
					"link_to": link_to,
					"hidden": 0,
					"is_query_report": 0,
					"onboard": 0,
				}
				for typ, label, link_to in links
			],
		}
	)
	doc.insert(ignore_permissions=True)
	print("workspace WMS created")


if __name__ == "__main__":
	apply()


BRAND_NAME = "WareTrack"
BRAND_LOGO = "/assets/erpnext/images/waretrack-logo.svg"
BRAND_FAVICON = "/assets/erpnext/images/waretrack-favicon.svg"


def _branding():
	"""Whitelabel the site as WareTrack (titles, logos, favicon, and visible ERPNext/Frappe strings)."""
	frappe.db.set_single_value("System Settings", "app_name", BRAND_NAME)
	frappe.db.set_single_value(
		"Website Settings",
		{
			"app_name": BRAND_NAME,
			"app_logo": BRAND_LOGO,
			"banner_image": BRAND_LOGO,
			"splash_image": BRAND_LOGO,
			"favicon": BRAND_FAVICON,
			"footer_powered": f"Powered by {BRAND_NAME}",
			"hide_footer_signup": 1,
		},
	)
	frappe.db.set_single_value("Navbar Settings", "app_logo", BRAND_LOGO)

	# Replace remaining UI strings via English translation overrides
	for source in ("ERPNext", "Frappe", "Frappe Framework", "ERPNext Settings"):
		target = source.replace("ERPNext", BRAND_NAME).replace("Frappe Framework", BRAND_NAME).replace("Frappe", BRAND_NAME)
		name = frappe.db.get_value("Translation", {"language": "en", "source_text": source})
		doc = frappe.get_doc("Translation", name) if name else frappe.new_doc("Translation")
		doc.update({"language": "en", "source_text": source, "translated_text": target})
		doc.save(ignore_permissions=True)
	print("applied WareTrack branding")
