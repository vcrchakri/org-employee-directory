import json
from datetime import date
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from .models import (
    Employee, EmployeeCompliance, EmployeeBankDetail,
    CTCHistory, OnboardingChecklist, OnboardingDocument,
    RoleChangeHistory,
)

# Default checklist items created for every new employee
DEFAULT_CHECKLIST_ITEMS = [
    ('offer_letter',      'Offer Letter Signed'),
    ('id_proof',          'Government ID Proof'),
    ('address_proof',     'Address Proof'),
    ('education_cert',    'Education Certificates'),
    ('experience_letter', 'Experience Letter'),
    ('pan_card',          'PAN Card'),
    ('bank_details',      'Bank Details Form'),
    ('nda_signed',        'NDA / Policy Signed'),
    ('it_assets',         'IT Assets Issued'),
    ('induction_done',    'Induction Completed'),
]


# ── EXISTING VIEWS (unchanged) ────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})


@method_decorator(csrf_exempt, name='dispatch')
class HeadcountReportView(View):
    def get(self, request):
        total  = Employee.objects.count()
        active = Employee.objects.filter(is_active=True).count()
        exited = Employee.objects.filter(is_active=False).count()
        return JsonResponse({"total": total, "active": active, "exited": exited})


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeListView(View):

    def get(self, request):
        from datetime import date
        # Lazy cron: deactivate employees whose exit date has passed
        to_deactivate = Employee.objects.filter(is_active=True, exit_date__lte=date.today())
        if to_deactivate.exists():
            to_deactivate.update(is_active=False)

        queryset = Employee.objects.all()
        search = request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(emp_id__icontains=search)
            )
        status = request.GET.get("status", "").strip().lower()
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "exited":
            queryset = queryset.filter(is_active=False)
        return JsonResponse(list(queryset.values()), safe=False)

    def post(self, request):
        try:
            payload = json.loads(request.body)
            emp_id  = payload.get("emp_id", "").strip()
            name    = payload.get("name",   "").strip()

            if not emp_id:
                return JsonResponse({"error": "emp_id is required"}, status=400)
            if not name:
                return JsonResponse({"error": "name is required"}, status=400)
            if not payload.get("joining_date"):
                return JsonResponse({"error": "joining_date is required"}, status=400)
            if not payload.get("designation"):
                return JsonResponse({"error": "designation is required"}, status=400)

            if Employee.objects.filter(emp_id=emp_id).exists():
                return JsonResponse({"error": f"Employee ID '{emp_id}' already exists"}, status=400)

            if not payload.get("email"):
                payload["email"] = f"{emp_id.lower()}@company.com"
            if Employee.objects.filter(email=payload["email"]).exists():
                payload["email"] = f"{emp_id.lower()}.{date.today().year}@company.com"

            payload.setdefault("is_active",         True)
            payload.setdefault("current_ctc",       500000)
            payload.setdefault("job_level",         "L1")
            payload.setdefault("compliance_status", "Pending")

            emp = Employee.objects.create(**payload)

            # Auto-seed CTC history
            CTCHistory.objects.create(
                employee=emp,
                ctc=emp.current_ctc,
                effective_date=emp.joining_date,
                remarks="Joining CTC"
            )

            # ── Auto-create default onboarding checklist for new employee ──
            for key, label in DEFAULT_CHECKLIST_ITEMS:
                OnboardingChecklist.objects.create(
                    employee=emp, item_key=key, item_label=label, status='Pending'
                )

            return JsonResponse({"message": "Employee created successfully", "id": emp.emp_id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def put(self, request):
        try:
            data   = json.loads(request.body)
            emp_id = data.get("emp_id", "").strip()
            if not emp_id:
                return JsonResponse({"error": "emp_id is required"}, status=400)
            emp = Employee.objects.get(emp_id=emp_id)
            if data.get("name"):         emp.name         = data["name"].strip()
            if data.get("designation"):  emp.designation  = data["designation"].strip()
            if data.get("joining_date"): emp.joining_date = data["joining_date"]
            if data.get("email"):        emp.email        = data["email"].strip()
            if data.get("current_ctc") is not None:
                emp.current_ctc = data["current_ctc"]
            if data.get("job_level"):    emp.job_level    = data["job_level"]
            emp.save()
            return JsonResponse({"message": "Employee updated successfully"})
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Employee not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def patch(self, request):
        try:
            data   = json.loads(request.body)
            emp_id = data.get("emp_id", "").strip()
            exit_date = data.get("exit_date")
            
            if not emp_id:
                return JsonResponse({"error": "emp_id is required"}, status=400)
            if not exit_date:
                return JsonResponse({"error": "Last Working Day (exit_date) is required"}, status=400)

            emp = Employee.objects.get(emp_id=emp_id)
            if not emp.is_active:
                return JsonResponse({"error": f"Employee '{emp_id}' has already exited"}, status=400)
            
            try:
                parsed_exit_date = date.fromisoformat(exit_date)
                if parsed_exit_date < emp.joining_date:
                    return JsonResponse({"error": "Last Working Day cannot be before Joining Date"}, status=400)
            except ValueError:
                return JsonResponse({"error": "Invalid date format for exit_date"}, status=400)

            # Lazy cron handles marking is_active False if the date is in the past
            if parsed_exit_date <= date.today():
                emp.is_active = False
            else:
                emp.is_active = True
                
            emp.exit_date = parsed_exit_date
            emp.save()
            return JsonResponse({"message": "Employee exit date set successfully"})
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Employee not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class EmployeeProfileView(View):

    def get(self, request, emp_id):
        try:
            emp = Employee.objects.get(emp_id=emp_id.upper())
        except Employee.DoesNotExist:
            return JsonResponse({"error": f"Employee '{emp_id}' not found"}, status=404)

        emp_data = {
            "emp_id":            emp.emp_id,
            "name":              emp.name,
            "email":             emp.email,
            "designation":       emp.designation,
            "is_active":         emp.is_active,
            "joining_date":      str(emp.joining_date) if emp.joining_date else None,
            "exit_date":         str(emp.exit_date)    if emp.exit_date    else None,
            "current_ctc":       float(emp.current_ctc),
            "job_level":         emp.job_level,
            "compliance_status": emp.compliance_status,
        }

        compliance_data = {}
        try:
            c = emp.compliance
            compliance_data = {
                "pan_number":        c.pan_number,
                "aadhar_number":     c.aadhar_number,
                "uan_number":        c.uan_number,
                "pf_number":         c.pf_number,
                "esic_number":       c.esic_number,
                "compliance_status": c.compliance_status,
            }
        except EmployeeCompliance.DoesNotExist:
            pass

        bank_data = {}
        try:
            b = emp.bank
            bank_data = {
                "bank_name":      b.bank_name,
                "account_number": b.account_number,
                "ifsc_code":      b.ifsc_code,
                "account_type":   b.account_type,
                "branch_name":    b.branch_name,
            }
        except EmployeeBankDetail.DoesNotExist:
            pass

        ctc_history = list(emp.ctc_history.values("ctc", "effective_date", "old_role", "new_role", "remarks"))
        for entry in ctc_history:
            entry["ctc"]            = float(entry["ctc"])
            entry["effective_date"] = str(entry["effective_date"])

        return JsonResponse({
            "employee":    emp_data,
            "compliance":  compliance_data,
            "bank":        bank_data,
            "ctc_history": ctc_history,
        })


# ── NEW: ONBOARDING VIEWS ─────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class OnboardingChecklistView(View):
    """
    GET  /api/onboarding/<emp_id>/          — fetch full checklist for an employee
    POST /api/onboarding/<emp_id>/init/     — create default checklist (if not exists)
    """

    def get(self, request, emp_id):
        try:
            emp = Employee.objects.get(emp_id=emp_id.upper())
        except Employee.DoesNotExist:
            return JsonResponse({"error": f"Employee '{emp_id}' not found"}, status=404)

        items = OnboardingChecklist.objects.filter(employee=emp).order_by('item_key')

        total     = items.count()
        verified  = items.filter(status='Verified').count()
        submitted = items.filter(status='Submitted').count()
        pending   = items.filter(status='Pending').count()
        rejected  = items.filter(status='Rejected').count()
        pct       = round((verified / total * 100) if total else 0)

        checklist_data = []
        for item in items:
            docs = list(item.documents.values("id", "doc_name", "doc_type", "uploaded_on", "uploaded_by"))
            for d in docs:
                d["uploaded_on"] = str(d["uploaded_on"])
            checklist_data.append({
                "id":           item.id,
                "item_key":     item.item_key,
                "item_label":   item.item_label,
                "status":       item.status,
                "submitted_on": str(item.submitted_on) if item.submitted_on else None,
                "verified_on":  str(item.verified_on)  if item.verified_on  else None,
                "notes":        item.notes,
                "documents":    docs,
            })

        return JsonResponse({
            "emp_id":   emp.emp_id,
            "name":     emp.name,
            "summary":  {
                "total":     total,
                "verified":  verified,
                "submitted": submitted,
                "pending":   pending,
                "rejected":  rejected,
                "percent":   pct,
            },
            "checklist": checklist_data,
        })


@method_decorator(csrf_exempt, name='dispatch')
class OnboardingItemUpdateView(View):
    """
    PATCH /api/onboarding/item/<item_id>/
    Body: { status, notes, submitted_on, verified_on }
    Updates a single checklist item's status.
    """

    def patch(self, request, item_id):
        try:
            item = OnboardingChecklist.objects.get(id=item_id)
            data = json.loads(request.body)

            if "status" in data:
                allowed = ['Pending', 'Submitted', 'Verified', 'Rejected']
                if data["status"] not in allowed:
                    return JsonResponse({"error": f"status must be one of {allowed}"}, status=400)
                item.status = data["status"]

                # Auto-set dates
                if data["status"] == "Submitted" and not item.submitted_on:
                    item.submitted_on = date.today()
                if data["status"] == "Verified" and not item.verified_on:
                    item.verified_on = date.today()

            if "notes"        in data: item.notes        = data["notes"]
            if "submitted_on" in data: item.submitted_on = data["submitted_on"]
            if "verified_on"  in data: item.verified_on  = data["verified_on"]

            item.save()
            return JsonResponse({"message": "Checklist item updated", "status": item.status})

        except OnboardingChecklist.DoesNotExist:
            return JsonResponse({"error": "Checklist item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class OnboardingDocumentView(View):
    """
    POST   /api/onboarding/document/            — add a document to a checklist item
    DELETE /api/onboarding/document/<doc_id>/   — remove a document
    """

    def post(self, request):
        try:
            content_type = request.content_type or ''

            if 'multipart' in content_type or 'application/x-www-form-urlencoded' in content_type:
                # ── Multipart / form-data path ─────────────────────────────
                item_id     = request.POST.get("item_id", "").strip()
                uploaded_by = request.POST.get("uploaded_by", "HR").strip()
                doc_type    = request.POST.get("doc_type", "").strip()
                doc_name    = request.POST.get("doc_name", "").strip()

                # If a real file was attached, use its name
                if not doc_name and "document" in request.FILES:
                    doc_name = request.FILES["document"].name

                # Auto-detect type from extension if not provided
                if doc_name and not doc_type:
                    ext = doc_name.rsplit(".", 1)[-1].upper() if "." in doc_name else "File"
                    doc_type = ext

            else:
                # ── JSON path ──────────────────────────────────────────────
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid JSON body"}, status=400)
                item_id     = str(data.get("item_id", "")).strip()
                doc_name    = data.get("doc_name", "").strip()
                doc_type    = data.get("doc_type", "").strip()
                uploaded_by = data.get("uploaded_by", "HR").strip()

            # ── Validate ───────────────────────────────────────────────────
            if not item_id:
                return JsonResponse({"error": "item_id is required"}, status=400)
            if not doc_name:
                return JsonResponse({"error": "Document name or file is required"}, status=400)

            try:
                item_pk = int(item_id)
            except (ValueError, TypeError):
                return JsonResponse({"error": f"Invalid item_id: {item_id}"}, status=400)

            item = OnboardingChecklist.objects.get(id=item_pk)

            doc = OnboardingDocument.objects.create(
                checklist_item=item,
                doc_name=doc_name,
                doc_type=doc_type or "File",
                uploaded_by=uploaded_by or "HR",
            )

            # Auto-advance Pending → Submitted
            if item.status == 'Pending':
                item.status       = 'Submitted'
                item.submitted_on = date.today()
                item.save()

            return JsonResponse({
                "message":     "Document added successfully",
                "doc_id":      doc.id,
                "doc_name":    doc.doc_name,
                "item_status": item.status,
            }, status=201)

        except OnboardingChecklist.DoesNotExist:
            return JsonResponse({"error": f"Checklist item not found"}, status=404)
        except Exception as e:
            import traceback
            return JsonResponse({"error": str(e), "detail": traceback.format_exc()}, status=400)

    def delete(self, request, doc_id=None):
        try:
            if not doc_id:
                data   = json.loads(request.body)
                doc_id = data.get("doc_id")
            doc = OnboardingDocument.objects.select_related('checklist_item').get(id=doc_id)
            item = doc.checklist_item
            doc.delete()
            
            # Revert status if 0 documents remain
            if item.documents.count() == 0 and item.status in ['Submitted', 'Verified']:
                item.status = 'Pending'
                item.submitted_on = None
                item.verified_on = None
                item.save()
                
            return JsonResponse({"message": "Document removed. Status updated if needed."})
        except OnboardingDocument.DoesNotExist:
            return JsonResponse({"error": "Document not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class OnboardingHRDashboardView(View):
    """
    GET /api/onboarding/dashboard/
    Returns completion summary for all active employees — HR overview.
    """

    def get(self, request):
        from datetime import date
        to_deactivate = Employee.objects.filter(is_active=True, exit_date__lte=date.today())
        if to_deactivate.exists():
            to_deactivate.update(is_active=False)

        employees = Employee.objects.filter(is_active=True).order_by('name')
        result    = []

        for emp in employees:
            items     = OnboardingChecklist.objects.filter(employee=emp)
            total     = items.count()
            if total == 0:
                continue   # skip employees with no checklist yet

            verified  = items.filter(status='Verified').count()
            submitted = items.filter(status='Submitted').count()
            pending   = items.filter(status='Pending').count()
            rejected  = items.filter(status='Rejected').count()
            pct       = round(verified / total * 100)

            result.append({
                "emp_id":      emp.emp_id,
                "name":        emp.name,
                "designation": emp.designation,
                "joining_date": str(emp.joining_date),
                "summary": {
                    "total":     total,
                    "verified":  verified,
                    "submitted": submitted,
                    "pending":   pending,
                    "rejected":  rejected,
                    "percent":   pct,
                }
            })

        # Sort: incomplete first
        result.sort(key=lambda x: x["summary"]["percent"])

        return JsonResponse({"employees": result, "count": len(result)})


@method_decorator(csrf_exempt, name='dispatch')
class OnboardingInitView(View):
    """
    POST /api/onboarding/<emp_id>/init/
    Creates the default checklist for an existing employee (idempotent).
    """

    def post(self, request, emp_id):
        try:
            emp     = Employee.objects.get(emp_id=emp_id.upper())
            created = 0
            for key, label in DEFAULT_CHECKLIST_ITEMS:
                _, was_created = OnboardingChecklist.objects.get_or_create(
                    employee=emp, item_key=key,
                    defaults={"item_label": label, "status": "Pending"}
                )
                if was_created:
                    created += 1

            return JsonResponse({
                "message": f"Checklist initialised — {created} new items created",
                "emp_id":  emp.emp_id,
            })
        except Employee.DoesNotExist:
            return JsonResponse({"error": f"Employee '{emp_id}' not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ── Auth stubs (unchanged) ────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class ApiLoginView(View):
    def post(self, request):
        return JsonResponse({"message": "Login stub"})


@method_decorator(csrf_exempt, name='dispatch')
class ApiRegisterView(View):
    def post(self, request):
        return JsonResponse({"message": "Register stub"})


@method_decorator(csrf_exempt, name='dispatch')
class ApiLogoutView(View):
    def post(self, request):
        return JsonResponse({"message": "Logout successful"})


@method_decorator(csrf_exempt, name='dispatch')
class ApiForgotPasswordView(View):
    def post(self, request):
        return JsonResponse({"message": "Password reset link sent"})


# ── JOB / ROLE CHANGE TRACKING VIEWS ─────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class RoleChangeHistoryView(View):
    """
    GET  /api/role-changes/<emp_id>/  — list all role/CTC change records
    POST /api/role-changes/<emp_id>/  — add a new record (with overlap check)
    """

    def get(self, request, emp_id):
        try:
            emp = Employee.objects.get(emp_id=emp_id.upper())
        except Employee.DoesNotExist:
            return JsonResponse({"error": f"Employee '{emp_id}' not found"}, status=404)

        records = RoleChangeHistory.objects.filter(employee=emp)
        data = []
        for r in records:
            data.append({
                "id":             r.id,
                "role":           r.role,
                "level":          r.level,
                "ctc":            float(r.ctc),
                "effective_from": str(r.effective_from),
                "effective_to":   str(r.effective_to) if r.effective_to else None,
                "remarks":        r.remarks or "",
            })

        return JsonResponse({
            "emp_id":  emp.emp_id,
            "name":    emp.name,
            "designation": emp.designation,
            "current_ctc": float(emp.current_ctc),
            "records": data,
        })

    def post(self, request, emp_id):
        try:
            emp = Employee.objects.get(emp_id=emp_id.upper())
        except Employee.DoesNotExist:
            return JsonResponse({"error": f"Employee '{emp_id}' not found"}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        role           = (body.get("role") or "").strip()
        level          = (body.get("level") or "").strip()
        ctc            = body.get("ctc")
        effective_from = (body.get("effective_from") or "").strip()
        effective_to   = (body.get("effective_to") or "").strip() or None
        remarks        = (body.get("remarks") or "").strip()

        # — Validation —
        if not role:
            return JsonResponse({"error": "role is required"}, status=400)
        if not level:
            return JsonResponse({"error": "level is required"}, status=400)
        if ctc is None:
            return JsonResponse({"error": "ctc is required"}, status=400)
        if not effective_from:
            return JsonResponse({"error": "effective_from is required"}, status=400)

        try:
            from datetime import datetime
            eff_from = datetime.strptime(effective_from, "%Y-%m-%d").date()
            eff_to   = datetime.strptime(effective_to, "%Y-%m-%d").date() if effective_to else None
        except ValueError:
            return JsonResponse({"error": "Dates must be in YYYY-MM-DD format"}, status=400)

        if eff_to and eff_to <= eff_from:
            return JsonResponse({"error": "effective_to must be after effective_from"}, status=400)

        # — Overlap and Auto-close check —
        from datetime import timedelta
        existing = RoleChangeHistory.objects.filter(employee=emp)
        for r in existing:
            r_from = r.effective_from
            r_to   = r.effective_to   # None = open

            # Auto-close preceding open roles:
            if r_to is None and eff_from > r_from:
                r.effective_to = eff_from - timedelta(days=1)
                r.save()
                r_to = r.effective_to

            new_overlaps_existing = (
                (eff_to is None or eff_to > r_from) and
                (r_to is None  or eff_from < r_to)
            )
            
            # If after auto-closing, it STILL overlaps, throw an error
            if new_overlaps_existing:
                period = f"{r_from} to {r_to or 'present'}"
                return JsonResponse(
                    {"error": f"Date range overlaps with an existing record ({r.role} / {period})"},
                    status=400
                )

        record = RoleChangeHistory.objects.create(
            employee=emp,
            role=role,
            level=level,
            ctc=ctc,
            effective_from=eff_from,
            effective_to=eff_to,
            remarks=remarks,
        )

        # Sync main user profile to the LATEST chronological record by effective_from
        from datetime import date
        
        # Determine the definitive current record
        # A record is "current" if its effective_from is <= today, 
        # AND its effective_to is either None, or > today.
        # We order by -effective_from to get the latest active one.
        active_records = RoleChangeHistory.objects.filter(
            employee=emp,
            effective_from__lte=date.today()
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gt=date.today())
        )
        
        if active_records.exists():
            # In cases where multiple records might casually overlap or be open, pick the one that started most recently
            current_role = active_records.order_by('-effective_from').first()
        else:
            # Fallback to the absolute latest record we know of if there's a gap, only future records, or employee has exited
            current_role = RoleChangeHistory.objects.filter(employee=emp).order_by('-effective_from').first()
            
        if current_role:
            old_role = emp.designation
            old_ctc = float(emp.current_ctc)
            
            emp.designation = current_role.role
            emp.job_level = current_role.level
            
            new_ctc = float(current_role.ctc)
            
            # If CTC changed, record it in CTCHistory
            if old_ctc != new_ctc:
                emp.current_ctc = current_role.ctc
                CTCHistory.objects.create(
                    employee=emp,
                    ctc=current_role.ctc,
                    effective_date=current_role.effective_from,
                    old_role=old_role,
                    new_role=current_role.role,
                    remarks="Synced via Role Change History Engine"
                )
            
            emp.save()

        return JsonResponse({
            "message": "Role change record added successfully",
            "id":      record.id,
        }, status=201)


# ── NEW: ALERTS & REMINDERS ───────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class AlertsView(View):
    """
    GET /api/alerts/
    Scans all active employees for:
      - Pending compliance (EmployeeCompliance.compliance_status == 'Pending')
      - Pending/Rejected onboarding (OnboardingChecklist.status in ['Pending', 'Rejected'])
    Returns an aggregated list of alerts grouped by employee.
    """
    def get(self, request):
        from datetime import date
        
        # Lazy Deactivate
        to_deactivate = Employee.objects.filter(is_active=True, exit_date__lte=date.today())
        if to_deactivate.exists():
            to_deactivate.update(is_active=False)

        # Exclude anyone who has technically exited (even if they were manually reactivated somehow)
        active_employees = Employee.objects.filter(
            is_active=True
        ).filter(
            Q(exit_date__isnull=True) | Q(exit_date__gt=date.today())
        ).prefetch_related('compliance', 'onboarding')
        
        alerts = []
        
        for emp in active_employees:
            emp_alerts = []
            
            # Check Compliance
            try:
                if emp.compliance.compliance_status == 'Pending':
                    emp_alerts.append({
                        "type": "compliance",
                        "message": "Statutory compliance is Pending review",
                    })
            except EmployeeCompliance.DoesNotExist:
                # Treat missing as pending
                emp_alerts.append({
                    "type": "compliance",
                    "message": "Statutory compliance data is missing/Pending",
                })
            
            # Check Onboarding
            pending_onboarding = [item for item in emp.onboarding.all() if item.status in ['Pending', 'Rejected']]
            for item in pending_onboarding:
                emp_alerts.append({
                    "type": "onboarding",
                    "message": f"{item.item_label} is {item.status}",
                })
                
            if emp_alerts:
                alerts.append({
                    "emp_id": emp.emp_id,
                    "name": emp.name,
                    "designation": emp.designation,
                    "alert_count": len(emp_alerts),
                    "items": emp_alerts
                })
                
        return JsonResponse(alerts, safe=False)


# ── NEW: JOINERS & LEAVERS REPORT ─────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class JoinersLeaversReportView(View):
    """
    GET /api/reports/joiners-leavers/?start_date=2024-01-01&end_date=2024-12-31
    Aggregates new joiners and exited employees per month, ensuring zero counts
    are included for months with no activity.
    """
    def get(self, request):
        from datetime import datetime, date
        import calendar

        start_str = request.GET.get('start_date')
        end_str = request.GET.get('end_date')

        if not start_str or not end_str:
            return JsonResponse({"error": "start_date and end_date are required"}, status=400)

        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Dates must be in YYYY-MM-DD format"}, status=400)

        if start_date > end_date:
            return JsonResponse({"error": "start_date cannot be after end_date"}, status=400)

        # Build a contiguous dictionary of months
        # Format: "YYYY-MM" -> {"joiners": 0, "leavers": 0}
        report_data = {}
        curr_date = start_date.replace(day=1)
        while curr_date <= end_date:
            month_key = curr_date.strftime("%Y-%m")
            report_data[month_key] = {
                "month_label": curr_date.strftime("%b %Y"), # e.g. "Jan 2024"
                "joiners": 0,
                "leavers": 0
            }
            # Increment month by 1
            month = curr_date.month % 12 + 1
            year = curr_date.year + (curr_date.month // 12)
            curr_date = curr_date.replace(year=year, month=month, day=1)
            
        # Fetch matching joined employees
        joiners = Employee.objects.filter(joining_date__gte=start_date, joining_date__lte=end_date)
        for emp in joiners:
            m_key = emp.joining_date.strftime("%Y-%m")
            if m_key in report_data:
                report_data[m_key]["joiners"] += 1

        # Fetch matching exited employees
        leavers = Employee.objects.filter(exit_date__gte=start_date, exit_date__lte=end_date)
        for emp in leavers:
            m_key = emp.exit_date.strftime("%Y-%m")
            if m_key in report_data:
                report_data[m_key]["leavers"] += 1

        # Convert dictionary to ordered list
        result = sorted([
            {
                "month_key": k,
                "month_label": v["month_label"],
                "joiners": v["joiners"],
                "leavers": v["leavers"]
            }
            for k, v in report_data.items()
        ], key=lambda x: x["month_key"])

        return JsonResponse({"data": result}, safe=False)
