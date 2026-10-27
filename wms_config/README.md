# WMS ERPNext Config (site config, in this repo)

Scripts for approximating Laravel WMS flows using ERPNext **site configuration**
(workflows, custom fields, notifications, workspace, permissions).

Canonical location: **`frappe-bench-fresh/apps/erpnext/wms_config/`** (this folder).

## Apply to `fresh.localhost`

```bash
cd ~/frappe-bench-fresh
bench --site fresh.localhost console
```

```python
import importlib.util
p = "/Users/fareehaamjad/frappe-bench-fresh/apps/erpnext/wms_config/apply_wms_config.py"
s = importlib.util.spec_from_file_location("wms_config", p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
m.apply()
```

Note: the running bench still uses `~/frappe-bench-fresh/apps/erpnext` (separate tree).
This folder is the source of truth for the config script in Cursor; applying it updates the site DB.

## What it configures

| Laravel area | ERPNext config |
|---|---|
| MRF 3-stage approval (header) | Workflow **MRF Approval** on Material Request (Purchase type) |
| Technician warehouse MR | Same workflow, alternate path for Material Issue / Transfer |
| PO → vendor accept/reject | Workflow **WMS Purchase Order** |
| GRN gate → QC → post | Workflow **WMS Goods Receipt** on Purchase Receipt |
| Issue / transfer / return stages | Workflow **WMS Stock Movement** on Stock Entry |
| Cycle count session | Workflow **WMS Cycle Count** on Stock Reconciliation |
| Extra tracking fields | Custom Fields `wms_*` |
| Alerts | Notifications to Estimation / Director / Budget / Vendor / Stock / QC |
| Navigation | Public workspace **WMS** |
| Whitelabel | **WareTrack** name, logo, favicon, footer, translation overrides |

## Still needs code / custom DocTypes later

- Per-line MRF approval + project item budget ledger
- Procurement desk, amendments, real vendor portal
- QR / gate enforcement / per-line QC / location tree
- True in-transit stock before submit
