# Odoo Patient View Configuration

## Overview

This guide shows how to customize the Odoo Partner (Contact) form to show medical fields for patients instead of generic business fields.

---

## Method 1: Create Custom Patient View (Recommended)

### Step 1: Create a new XML file

Create: `odoo_custom/views/patient_view.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Patient Form View -->
    <record id="view_patient_form" model="ir.ui.view">
        <field name="name">res.partner.patient.form</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <form string="Patient" position="attributes">
                <attribute name="string">Patient</attribute>
            </form>

            <!-- Replace business notebook with medical notebook -->
            <xpath expr="//page[@name='sales_purchases']" position="replace">
                <page string="Medical Information">
                    <group>
                        <group string="Basic Info">
                            <field name="is_patient" invisible="1"/>
                            <field name="medical_record_number" readonly="1"/>
                            <field name="date_of_birth"/>
                            <field name="age" readonly="1"/>
                            <field name="blood_type"/>
                            <field name="risk_category"/>
                        </group>
                        <group string="Medical History">
                            <field name="allergies" placeholder="Known allergies..."/>
                            <field name="chronic_conditions" placeholder="Chronic conditions..."/>
                            <field name="past_surgeries"/>
                            <field name="family_history"/>
                        </group>
                    </group>
                    <group>
                        <group string="Women's Health">
                            <field name="pregnancy_status"/>
                            <field name="expected_due_date" attrs="{'invisible': [('pregnancy_status', 'not in', ['pregnant', 'high_risk'])]}"/>
                            <field name="last_prenatal_checkup"/>
                        </group>
                        <group string="Emergency Contact">
                            <field name="emergency_contact_id"/>
                            <field name="emergency_contact_phone"/>
                        </group>
                    </group>
                </page>
            </xpath>

            <!-- Hide irrelevant tabs for patients -->
            <xpath expr="//page[@name='sales_purchases']" position="attributes">
                <attribute name="invisible">1</attribute>
            </xpath>
            <xpath expr="//page[@name='internal_notes']" position="attributes">
                <attribute name="string">Clinical Notes</attribute>
            </xpath>
        </field>
    </record>

    <!-- Patient Tree View -->
    <record id="view_patient_tree" model="ir.ui.view">
        <field name="name">res.partner.patient.tree</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_tree"/>
        <field name="arch" type="xml">
            <tree position="attributes">
                <attribute name="string">Patients</attribute>
            </tree>
            <field name="medical_record_number"/>
            <field name="blood_type"/>
            <field name="risk_category"/>
            <field name="last_visit_date"/>
        </field>
    </record>

    <!-- Patient Search View -->
    <record id="view_patients_search" model="ir.ui.view">
        <field name="name">res.partner.patient.search</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_res_partner_filter"/>
        <field name="arch" type="xml">
            <search position="inside">
                <filter name="is_patient" domain="[('is_patient', '=', True)]" string="Patients"/>
                <separator/>
                <filter name="high_risk" domain="[('risk_category', '=', 'high')]" string="High Risk"/>
                <filter name="pregnant" domain="[('pregnancy_status', 'in', ['pregnant', 'high_risk'])]" string="Pregnant"/>
                <separator/>
                <field name="medical_record_number"/>
            </search>
        </field>
    </record>

    <!-- Patient Action -->
    <record id="action_patients" model="ir.actions.act_window">
        <field name="name">Patients</field>
        <field name="res_model">res.partner</field>
        <field name="view_mode">tree,form</field>
        <field name="domain">[('is_patient', '=', True)]</field>
        <field name="context">{'default_is_patient': True}</field>
        <field name="view_id" ref="view_patient_tree"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Create your first patient!
            </p>
        </field>
    </record>

    <!-- Menu Item -->
    <menuitem id="menu_patients" name="Patients" parent="healthcare.root"
              action="action_patients" sequence="1"/>
</odoo>
```

### Step 2: Update __manifest__.py

```python
'data': [
    'views/patient_view.xml',
]
```

### Step 3: Update Apps

1. Go to Apps → Update Apps List
2. Update your custom module
3. Refresh browser

---

## Method 2: Modify Existing Healthcare Module

If you're using the Odoo Healthcare module, modify its views directly.

### File: `medical/views/patient_view.xml`

Add this to override the default form:

```xml
<record id="medical_patient_view_form" model="ir.ui.view">
    <field name="name">medical.patient.form</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">

        <!-- Show medical fields when is_patient = True -->
        <xpath expr="//field[@name='function']" position="before">
            <field name="is_patient" widget="boolean_button"/>
            <field name="medical_record_number" attrs="{'invisible': [('is_patient', '=', False)]"/>
        </xpath>

        <!-- Replace sales tab with medical info for patients -->
        <xpath expr="//page[@name='sales_purchases']" position="after">
            <page string="Medical Information" attrs="{'invisible': [('is_patient', '=', False)]}">
                <group>
                    <group string="Vitals &amp; Risk">
                        <field name="date_of_birth"/>
                        <field name="blood_type"/>
                        <field name="risk_category"/>
                        <field name="age" readonly="1"/>
                    </group>
                    <group string="Medical History">
                        <field name="allergies" placeholder="Known allergies"/>
                        <field name="chronic_conditions" placeholder="Chronic conditions"/>
                        <field name="pregnancy_status"/>
                    </group>
                </group>
            </page>
        </xpath>

        <!-- Hide business fields for patients -->
        <xpath expr="//field[@name='function']" position="attributes">
            <attribute name="attrs">{'invisible': [('is_patient', '=', True)]}</attribute>
        </xpath>

    </field>
</record>
```

---

## Field Definitions (models/medical_patient.py)

Ensure these fields exist in res.partner model:

```python
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Patient identification
    is_patient = fields.Boolean('Is Patient', default=False)
    medical_record_number = fields.Char('Medical Record #', readonly=True, copy=False)

    # Basic info
    date_of_birth = fields.Date('Date of Birth')
    age = fields.Integer('Age', compute='_compute_age')
    blood_type = fields.Selection([
        ('a_plus', 'A+'), ('a_minus', 'A-'),
        ('b_plus', 'B+'), ('b_minus', 'B-'),
        ('ab_plus', 'AB+'), ('ab_minus', 'AB-'),
        ('o_plus', 'O+'), ('o_minus', 'O-'),
        ('unknown', 'Unknown')
    ], 'Blood Type', default='unknown')

    # Risk assessment
    risk_category = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], 'Risk Category', default='low')

    # Medical history
    allergies = fields.Text('Allergies')
    chronic_conditions = fields.Text('Chronic Conditions')
    past_surgeries = fields.Text('Past Surgeries')
    family_history = fields.Text('Family History')

    # Women's health
    pregnancy_status = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('not_pregnant', 'Not Pregnant'),
        ('pregnant', 'Pregnant'),
        ('high_risk', 'High Risk Pregnancy')
    ], 'Pregnancy Status', default='not_applicable')
    expected_due_date = fields.Date('Expected Due Date')
    last_prenatal_checkup = fields.Date('Last Prenatal Checkup')

    # Emergency contact
    emergency_contact_id = fields.Many2one('res.partner', 'Emergency Contact')
    emergency_contact_phone = fields.Char('Emergency Contact Phone')

    # Visit tracking
    last_visit_date = fields.Date('Last Visit')
    next_appointment = fields.Datetime('Next Appointment')
    total_visits = fields.Integer('Total Visits', default=0)

    # Primary physician
    primary_physician_id = fields.Many2one('res.users', 'Primary Physician')

    # Insurance
    insurance_provider = fields.Char('Insurance Provider')
    insurance_policy_number = fields.Char('Policy Number')
    insurance_member_id = fields.Char('Member ID')

    @depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = date.today()
                born = record.date_of_birth
                record.age = today.year - born.year - (
                    (today.month, today.day) < (born.month, born.day)
                )
            else:
                record.age = 0
```

---

## Quick Test

1. Restart Odoo: `odoo-bin -c odoo.conf -d odoo -u your_module --stop-after-init`
2. Open browser to Odoo
3. Go to Healthcare → Patients
4. Create new patient

You should see medical fields instead of business fields!

---

## Screenshot of Expected Layout

```
┌─────────────────────────────────────────────┐
│ Patient                                     │
├─────────────────────────────────────────────┤
│ Name: [John Doe]          Is Patient: [✓]   │
│ Medical Record #: MRN000123                │
├─────────────────────────────────────────────┤
│ Contacts │ Sales & Purchase │ Medical Info  │
└─────────────────────────────────────────────┘

Medical Info Tab:
┌─────────────────────────────────────────────┐
│ Basic Info            │ Medical History      │
├─────────────────────────────────────────────┤
│ Date of Birth: [📅]   │ Allergies: [...]     │
│ Age: 35               │ Chronic: [...]       │
│ Blood Type: O+        │ Past Surgeries: [...]│
│ Risk: Low             │ Family History: [...]│
└─────────────────────────────────────────────┘
```
