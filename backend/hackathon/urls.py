from django.urls import path
from .views import (
    # Existing
    HealthView,
    HeadcountReportView,
    EmployeeListView,
    EmployeeProfileView,
    ApiLoginView,
    ApiRegisterView,
    ApiLogoutView,
    ApiForgotPasswordView,
    # Onboarding
    OnboardingChecklistView,
    OnboardingItemUpdateView,
    OnboardingDocumentView,
    OnboardingHRDashboardView,
    OnboardingInitView,
    # Role Change Tracking
    RoleChangeHistoryView,
    # Alerts
    AlertsView,
    # Reports
    JoinersLeaversReportView,
)

urlpatterns = [

    # ── Health ────────────────────────────────────────────────────────────
    path('health/', HealthView.as_view()),

    # ── Employees (CRUD) ──────────────────────────────────────────────────
    path('employees/',                      EmployeeListView.as_view()),
    path('employees/profile/<str:emp_id>/', EmployeeProfileView.as_view()),

    # ── Reports ───────────────────────────────────────────────────────────
    path('reports/headcount/', HeadcountReportView.as_view()),

    # ── Onboarding ────────────────────────────────────────────────────────
    # IMPORTANT: all fixed-segment paths MUST come before <str:emp_id>
    # otherwise Django matches "document", "item", "dashboard" as emp_id

    # HR overview dashboard
    path('onboarding/dashboard/',                 OnboardingHRDashboardView.as_view()),

    # Document add (POST) / list
    path('onboarding/document/',                  OnboardingDocumentView.as_view()),

    # Document delete by id
    path('onboarding/document/<int:doc_id>/',     OnboardingDocumentView.as_view()),

    # Update single checklist item status/notes
    path('onboarding/item/<int:item_id>/',        OnboardingItemUpdateView.as_view()),

    # Per-employee checklist — wildcard LAST so it doesn't swallow above routes
    path('onboarding/<str:emp_id>/init/',         OnboardingInitView.as_view()),
    path('onboarding/<str:emp_id>/',              OnboardingChecklistView.as_view()),

    # ── Auth stubs ────────────────────────────────────────────────────────
    path('auth/login/',           ApiLoginView.as_view()),
    path('auth/register/',        ApiRegisterView.as_view()),
    path('auth/logout/',          ApiLogoutView.as_view()),
    path('auth/forgot-password/', ApiForgotPasswordView.as_view()),

    # ── Job / Role Change Tracking ───────────────────────────
    path('role-changes/<str:emp_id>/', RoleChangeHistoryView.as_view()),

    # ── Alerts & Reminders ───────────────────────────────────
    path('alerts/', AlertsView.as_view()),
    
    # ── Reports (Joiners/Leavers) ────────────────────────────
    path('reports/joiners-leavers/', JoinersLeaversReportView.as_view()),
]