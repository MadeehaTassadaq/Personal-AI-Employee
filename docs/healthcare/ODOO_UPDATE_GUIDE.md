# Odoo Patient View Update - Quick Guide

## Changes Made

### 1. Enhanced `views/partner_views.xml`
- Added inherited view for standard Odoo contact form
- Shows medical fields when `is_patient = True`
- Hides business fields (Job Position, Tax ID, Website, etc.) for patients
- Added toggle button to switch between Contact/Patient mode

### 2. Updated `models/res_partner.py`
- Added `weight` and `height` fields
- Added `toggle_is_patient()` method for the button

### 3. Updated `__manifest__.py`
- Bumped version to `1.3.0`

---

## How to Update Odoo

### Option 1: Quick Update (Recommended)

```bash
# 1. Stop Odoo
sudo systemctl stop odoo

# OR kill the process:
sudo pkill -f odoo-bin

# 2. Update the module
cd /home/madeeha/Documents/Personal-AI-Employee
odoo-bin -c /etc/odoo/odoo.conf -d odoo -u medical_healthcare --stop-after-init

# 3. Start Odoo
sudo systemctl start odoo

# OR start manually:
odoo-bin -c /etc/odoo/odoo.conf -d odoo --dev
```

### Option 2: Update from Odoo UI

1. Go to **Apps** → **Remove 'Healthcare Management'**
2. Go to **Apps** → **Update Apps List**
3. Search for **Healthcare Management**
4. Click **Upgrade**

---

## Testing the Changes

### Test 1: Patient View via Healthcare Menu

1. Open http://localhost:8069
2. Login as admin
3. Go to **Healthcare** → **Patients**
4. Click **Create**
5. Fill in patient details:
   - **Name**: John Doe
   - **Date of Birth**: 1990-01-01
   - **Blood Type**: O+
   - **Allergies**: Penicillin
   - **Risk Category**: Low
6. Save
7. Verify medical fields are displayed correctly

### Test 2: Toggle Button on Standard Contact Form

1. Go to **Contacts**
2. Click **Create**
3. Fill in name: **Jane Smith**
4. Look for the **"Not Patient"** button in the header
5. Click it to toggle to **"Patient"**
6. Verify medical fields appear
7. Verify business fields disappear (Job Position, etc.)
8. Toggle back to verify it reverts

---

## What You Should See

### Standard Contact Form (Before Toggle)
```
┌─────────────────────────────────────┐
│ Contact                             │
├─────────────────────────────────────┤
│ Name: [John Doe]                    │
│ [Not Patient] button                │
├─────────────────────────────────────┤
│ Phone: [...]      | Title: [Manager] │
│ Email: [...]      | Website: [...]  │
│ ...                                  │
└─────────────────────────────────────┘
```

### Patient Form (After Toggle)
```
┌─────────────────────────────────────┐
│ Patient                             │
├─────────────────────────────────────┤
│ Name: [John Doe]                    │
│ [Patient] button                    │
├─────────────────────────────────────┤
│ Patient Information                 │
│ Date of Birth: [📅]  | Insurance: [...]│
│ Age: 35               | Policy #: [...]│
│ Blood Type: O+        | Member ID: [...]│
│ Risk: Low                              │
├─────────────────────────────────────┤
│ Medical Information Tab              │
│ - Allergies                           │
│ - Chronic Conditions                  │
│ - Past Surgeries                      │
│ - Women's Health                     │
└─────────────────────────────────────┘
```

---

## Troubleshooting

### Error: "Field does not exist"

**Solution:** Ensure module was updated with `-u medical_healthcare`

### Toggle button not appearing

**Solution:** Clear browser cache and refresh

### Medical fields not showing

**Solution:**
1. Verify `is_patient = True` in database
2. Check browser console for errors
3. Ensure view inheritance loaded correctly

---

## Files Modified

```
odoo_custom_modules/medical_healthcare/
├── __manifest__.py (updated version)
├── models/
│   └── res_partner.py (added weight, height, toggle_is_patient)
└── views/
    └── partner_views.xml (added inherited view)
```

---

## Next Steps

After confirming the update works:

1. Test creating a new patient
2. Test the toggle button on standard contact
3. Verify medical fields display correctly
4. Update existing patients with medical data
