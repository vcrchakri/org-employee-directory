from django.db import models


# ── EXISTING MODELS (unchanged) ───────────────────────────────────────────

class Employee(models.Model):

    emp_id      = models.CharField(max_length=20, unique=True)
    name        = models.CharField(max_length=255)
    email       = models.EmailField(unique=True)
    designation = models.CharField(max_length=100)

    is_active    = models.BooleanField(default=True)
    joining_date = models.DateField()
    exit_date    = models.DateField(null=True, blank=True)

    current_ctc       = models.DecimalField(max_digits=15, decimal_places=2)
    job_level         = models.CharField(max_length=50)
    compliance_status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return f"{self.emp_id} — {self.name}"


class EmployeeCompliance(models.Model):
    employee      = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='compliance')
    pan_number    = models.CharField(max_length=20, blank=True, null=True)
    aadhar_number = models.CharField(max_length=20, blank=True, null=True)
    uan_number    = models.CharField(max_length=20, blank=True, null=True)
    pf_number     = models.CharField(max_length=30, blank=True, null=True)
    esic_number   = models.CharField(max_length=20, blank=True, null=True)
    compliance_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )

    def __str__(self):
        return f"Compliance — {self.employee.emp_id}"


class EmployeeBankDetail(models.Model):
    ACCOUNT_TYPES = [
        ('Savings', 'Savings'),
        ('Current', 'Current'),
        ('Salary',  'Salary'),
    ]
    employee       = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bank')
    bank_name      = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=30,  blank=True, null=True)
    ifsc_code      = models.CharField(max_length=20,  blank=True, null=True)
    account_type   = models.CharField(max_length=20,  choices=ACCOUNT_TYPES, default='Savings')
    branch_name    = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Bank — {self.employee.emp_id}"


class CTCHistory(models.Model):
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ctc_history')
    ctc            = models.DecimalField(max_digits=15, decimal_places=2)
    effective_date = models.DateField()
    
    old_role       = models.CharField(max_length=100, null=True, blank=True)
    new_role       = models.CharField(max_length=100, null=True, blank=True)

    remarks        = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f"CTC {self.ctc} for {self.employee.emp_id} from {self.effective_date}"


# ── NEW: ONBOARDING MODELS ────────────────────────────────────────────────

class OnboardingChecklist(models.Model):
    """
    One checklist row per employee per checklist item.
    Tracks status of each onboarding step.
    """

    STATUS_CHOICES = [
        ('Pending',    'Pending'),
        ('Submitted',  'Submitted'),
        ('Verified',   'Verified'),
        ('Rejected',   'Rejected'),
    ]

    ITEM_CHOICES = [
        ('offer_letter',       'Offer Letter Signed'),
        ('id_proof',           'Government ID Proof'),
        ('address_proof',      'Address Proof'),
        ('education_cert',     'Education Certificates'),
        ('experience_letter',  'Experience Letter'),
        ('pan_card',           'PAN Card'),
        ('bank_details',       'Bank Details Form'),
        ('nda_signed',         'NDA / Policy Signed'),
        ('it_assets',          'IT Assets Issued'),
        ('induction_done',     'Induction Completed'),
    ]

    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='onboarding')
    item_key     = models.CharField(max_length=50, choices=ITEM_CHOICES)
    item_label   = models.CharField(max_length=100)          # human-readable label
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    submitted_on = models.DateField(null=True, blank=True)   # when doc was submitted
    verified_on  = models.DateField(null=True, blank=True)   # when HR verified
    notes        = models.TextField(blank=True, null=True)   # HR notes / rejection reason

    class Meta:
        unique_together = ('employee', 'item_key')           # one row per item per employee
        ordering        = ['item_key']

    def __str__(self):
        return f"{self.employee.emp_id} — {self.item_label} [{self.status}]"


class OnboardingDocument(models.Model):
    """
    Stores document metadata (name, type, upload date) linked to a checklist item.
    Actual file storage is optional — we track name/reference here.
    """

    checklist_item = models.ForeignKey(
        OnboardingChecklist, on_delete=models.CASCADE, related_name='documents'
    )
    doc_name       = models.CharField(max_length=255)        # filename or doc title
    doc_type       = models.CharField(max_length=50, blank=True, null=True)   # pdf/jpg/etc
    uploaded_on    = models.DateField(auto_now_add=True)
    uploaded_by    = models.CharField(max_length=100, blank=True, null=True)  # HR name

    def __str__(self):
        return f"{self.doc_name} — {self.checklist_item}"


# ── JOB / ROLE CHANGE TRACKING ───────────────────────────────────────────

class RoleChangeHistory(models.Model):
    """
    Records every role, level, and CTC change for an employee.
    Effective date ranges must not overlap for the same employee.
    effective_to = None means the change is still current.
    """

    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='role_history')
    role           = models.CharField(max_length=100)
    level          = models.CharField(max_length=50)
    ctc            = models.DecimalField(max_digits=15, decimal_places=2)
    effective_from = models.DateField()
    effective_to   = models.DateField(null=True, blank=True)  # None = current
    remarks        = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.employee.emp_id} — {self.role} ({self.effective_from})"
