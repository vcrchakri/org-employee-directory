import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { httpJson } from '../api/http.js'
import '../styles/RoleChanges.css'

// ─── helpers ──────────────────────────────────────────────────────────────

function fmtCTC(val) {
    const n = Number(val)
    if (isNaN(n)) return '—'
    if (n >= 100000) return `₹${(n / 100000).toFixed(2)} L`
    return `₹${n.toLocaleString('en-IN')}`
}

function fmtDate(d) {
    if (!d) return 'Present'
    return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Timeline item ─────────────────────────────────────────────────────────

function TimelineItem({ record, index }) {
    const isCurrent = !record.effective_to
    return (
        <div className="rc-tl-item">
            <div className={`rc-tl-dot${isCurrent ? ' current' : ''}`} />
            <div className="rc-tl-card">
                <div className="rc-tl-header">
                    <div className="rc-tl-role">{record.role}</div>
                    <div className={`rc-tl-badge${isCurrent ? ' current' : ''}`}>
                        {isCurrent ? '✦ Current' : `Past`}
                    </div>
                </div>
                <div className="rc-tl-meta">
                    <span><i className="bi bi-layers" /> Level {record.level}</span>
                    <span>
                        <i className="bi bi-calendar3" />
                        {fmtDate(record.effective_from)} — {fmtDate(record.effective_to)}
                    </span>
                </div>
                <div className="rc-tl-ctc">
                    CTC: <span className="ctc-val">{fmtCTC(record.ctc)}</span>
                </div>
                {record.remarks && (
                    <div className="rc-tl-remarks">"{record.remarks}"</div>
                )}
            </div>
        </div>
    )
}

// ─── Main page ─────────────────────────────────────────────────────────────

function RoleChangesPage() {
    const navigate = useNavigate()
    const { signOut, member } = useAuth()

    // Search
    const [searchEmpId, setSearchEmpId] = useState('')
    const [searching, setSearching] = useState(false)
    const [searchError, setSearchError] = useState('')

    // Loaded employee data
    const [emp, setEmp] = useState(null)   // { emp_id, name, designation, current_ctc, records[] }

    // Form state
    const [form, setForm] = useState({
        role: '', level: '', ctc: '', effective_from: '', effective_to: '', remarks: ''
    })
    const [submitting, setSubmitting] = useState(false)
    const [formError, setFormError] = useState('')
    const [formSuccess, setFormSuccess] = useState('')

    // ── handlers ──────────────────────────────────────────────────────────────

    const handleSearch = useCallback(async (e) => {
        e.preventDefault()
        const id = searchEmpId.trim().toUpperCase()
        if (!id) return
        setSearching(true)
        setSearchError('')
        setEmp(null)
        setFormError('')
        setFormSuccess('')
        try {
            const data = await httpJson(`/api/role-changes/${id}/`)
            setEmp(data)
        } catch (err) {
            setSearchError(err?.message || 'Employee not found')
        } finally {
            setSearching(false)
        }
    }, [searchEmpId])

    const handleFormChange = (field, value) => {
        setForm(prev => ({ ...prev, [field]: value }))
        setFormError('')
        setFormSuccess('')
    }

    // Client-side overlap validation
    function hasOverlap(records, newFrom, newTo) {
        const nFrom = new Date(newFrom)
        const nTo = newTo ? new Date(newTo) : Infinity
        for (const r of records) {
            const rFrom = new Date(r.effective_from)
            const rTo = r.effective_to ? new Date(r.effective_to) : Infinity
            if (nTo > rFrom && nFrom < rTo) {
                return `Overlaps with "${r.role}" (${r.effective_from} → ${r.effective_to || 'present'})`
            }
        }
        return null
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!emp) return
        setFormError('')
        setFormSuccess('')

        const { role, level, ctc, effective_from, effective_to, remarks } = form

        if (!role.trim()) return setFormError('Role is required')
        if (!level.trim()) return setFormError('Level is required')
        if (!ctc || isNaN(+ctc)) return setFormError('Valid CTC amount is required')
        if (!effective_from) return setFormError('Effective From date is required')
        if (effective_to && effective_to <= effective_from)
            return setFormError('Effective To must be after Effective From')

        // Front-end overlap check
        const overlap = hasOverlap(emp.records, effective_from, effective_to || null)
        if (overlap) return setFormError(overlap)

        setSubmitting(true)
        try {
            await httpJson(`/api/role-changes/${emp.emp_id}/`, {
                method: 'POST',
                body: {
                    role: role.trim(),
                    level: level.trim(),
                    ctc: parseFloat(ctc),
                    effective_from,
                    effective_to: effective_to || null,
                    remarks: remarks.trim(),
                },
            })
            setFormSuccess('Record added successfully!')
            setForm({ role: '', level: '', ctc: '', effective_from: '', effective_to: '', remarks: '' })

            // Refresh the records list
            const fresh = await httpJson(`/api/role-changes/${emp.emp_id}/`)
            setEmp(fresh)
        } catch (err) {
            setFormError(err?.message || 'Failed to add record')
        } finally {
            setSubmitting(false)
        }
    }

    const handleLogout = async () => {
        await signOut()
        navigate('/auth')
    }

    // ── render ────────────────────────────────────────────────────────────────

    return (
        <div className="rc-shell">

            {/* ── Sidebar ──────────────────────────────────────────────────────── */}
            <aside className="rc-sidebar">
                <div className="rc-sidebar-title">Role Tracker</div>

                {/* Emp search */}
                <form onSubmit={handleSearch}>
                    <div className="rc-search-row">
                        <input
                            id="rc-emp-search"
                            className="rc-search-input"
                            type="text"
                            placeholder="Emp ID…"
                            value={searchEmpId}
                            onChange={e => setSearchEmpId(e.target.value)}
                            disabled={searching}
                        />
                        <button className="rc-search-btn" type="submit" disabled={searching}>
                            {searching ? '…' : 'Go'}
                        </button>
                    </div>
                </form>

                {searchError && (
                    <div className="rc-form-error" style={{ marginTop: 0, marginBottom: 12 }}>{searchError}</div>
                )}

                {/* Employee card */}
                {emp && (
                    <div className="rc-emp-card">
                        <div className="rc-emp-name">{emp.name}</div>
                        <div className="rc-emp-id">{emp.emp_id}</div>
                        <div className="rc-emp-designation">{emp.designation}</div>
                        <div className="rc-emp-ctc">
                            Current CTC: <span>{fmtCTC(emp.current_ctc)}</span>
                        </div>
                    </div>
                )}

                <button className="rc-back-btn" onClick={() => navigate('/home')}>
                    <i className="bi bi-arrow-left" /> Back
                </button>
            </aside>

            {/* ── Main ──────────────────────────────────────────────────────────── */}
            <div className="rc-main">
                {/* Topbar */}
                <div className="rc-topbar">
                    <div>
                        <div className="rc-topbar-title">Job / Role Change Tracking</div>
                        <div className="rc-topbar-sub">Record role, level &amp; CTC history with effective dates</div>
                    </div>
                    <button className="rc-userbtn" title="Logout" onClick={handleLogout}>
                        <i className="bi bi-box-arrow-right" />
                    </button>
                </div>

                {/* Content */}
                <div className="rc-content">

                    {!emp ? (
                        /* Prompt */
                        <div className="rc-prompt">
                            <i className="bi bi-person-lines-fill" />
                            <h2>Search for an Employee</h2>
                            <p>Enter an Employee ID in the sidebar to view and manage their role change history.</p>
                        </div>
                    ) : (
                        <>
                            {/* ── Add Record Form ─────────────────────────────────────── */}
                            <div className="rc-card">
                                <div className="rc-card-title">
                                    <i className="bi bi-plus-circle-fill" /> Add Role / CTC Change
                                </div>

                                <form onSubmit={handleSubmit}>
                                    <div className="rc-form-grid">
                                        <div className="rc-field">
                                            <label htmlFor="rc-role">Role / Designation</label>
                                            <input
                                                id="rc-role"
                                                type="text"
                                                placeholder="e.g. Senior Analyst"
                                                value={form.role}
                                                onChange={e => handleFormChange('role', e.target.value)}
                                                disabled={submitting}
                                            />
                                        </div>

                                        <div className="rc-field">
                                            <label htmlFor="rc-level">Job Level</label>
                                            <input
                                                id="rc-level"
                                                type="text"
                                                placeholder="e.g. L3"
                                                value={form.level}
                                                onChange={e => handleFormChange('level', e.target.value)}
                                                disabled={submitting}
                                            />
                                        </div>

                                        <div className="rc-field">
                                            <label htmlFor="rc-ctc">CTC (Annual ₹)</label>
                                            <input
                                                id="rc-ctc"
                                                type="number"
                                                placeholder="e.g. 700000"
                                                min="0"
                                                value={form.ctc}
                                                onChange={e => handleFormChange('ctc', e.target.value)}
                                                disabled={submitting}
                                            />
                                        </div>

                                        <div className="rc-field">
                                            {/* empty spacer */}
                                        </div>

                                        <div className="rc-field">
                                            <label htmlFor="rc-from">Effective From</label>
                                            <input
                                                id="rc-from"
                                                type="date"
                                                value={form.effective_from}
                                                onChange={e => handleFormChange('effective_from', e.target.value)}
                                                disabled={submitting}
                                            />
                                        </div>

                                        <div className="rc-field">
                                            <label htmlFor="rc-to">Effective To <span style={{ fontWeight: 400, color: 'var(--dark-4)' }}>(leave blank if current)</span></label>
                                            <input
                                                id="rc-to"
                                                type="date"
                                                value={form.effective_to}
                                                onChange={e => handleFormChange('effective_to', e.target.value)}
                                                disabled={submitting}
                                            />
                                        </div>

                                        <div className="rc-field full-col">
                                            <label htmlFor="rc-remarks">Remarks</label>
                                            <input
                                                id="rc-remarks"
                                                type="text"
                                                placeholder="e.g. Promoted from L2 to L3"
                                                value={form.remarks}
                                                onChange={e => handleFormChange('remarks', e.target.value)}
                                                disabled={submitting}
                                            />
                                        </div>
                                    </div>

                                    {formError && <div className="rc-form-error">{formError}</div>}
                                    {formSuccess && <div className="rc-form-success">{formSuccess}</div>}

                                    <button className="rc-submit-btn" type="submit" disabled={submitting}>
                                        {submitting ? 'Saving…' : 'Add Record'}
                                    </button>
                                </form>
                            </div>

                            {/* ── Timeline ────────────────────────────────────────────── */}
                            <div className="rc-card rc-timeline-wrap">
                                <div className="rc-card-title">
                                    <i className="bi bi-clock-history" /> History Timeline
                                    &nbsp;<span style={{ fontSize: 12, fontWeight: 400, color: 'var(--dark-3)' }}>
                                        ({emp.records.length} record{emp.records.length !== 1 ? 's' : ''})
                                    </span>
                                </div>

                                {emp.records.length === 0 ? (
                                    <div className="rc-timeline-empty">
                                        <i className="bi bi-hourglass" />
                                        No records yet — add the first one using the form.
                                    </div>
                                ) : (
                                    <div className="rc-timeline">
                                        {emp.records.map((r, i) => (
                                            <TimelineItem key={r.id} record={r} index={i} />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

export default RoleChangesPage
