import { useState, useEffect, useRef } from 'react'
import { httpJson } from '../api/http.js'
import '../styles/Reports.css'

function ReportsPage() {
    // Default to Last 6 Months
    const today = new Date()
    const sixMonthsAgo = new Date()
    sixMonthsAgo.setMonth(today.getMonth() - 5)
    sixMonthsAgo.setDate(1) // Start of month

    const defaultStart = sixMonthsAgo.toISOString().split('T')[0]
    const defaultEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0] // End of current month

    const [startDate, setStartDate] = useState(defaultStart)
    const [endDate, setEndDate] = useState(defaultEnd)
    const [reportData, setReportData] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const canvasRef = useRef(null)
    const chartInstanceRef = useRef(null)

    const fetchReport = async () => {
        setLoading(true)
        setError('')
        try {
            const res = await httpJson(`/api/reports/joiners-leavers/?start_date=${startDate}&end_date=${endDate}`)
            if (res.error) throw new Error(res.error)
            setReportData(res.data || [])
        } catch (err) {
            setError(err.message || 'Failed to fetch report data')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchReport()
    }, [])

    useEffect(() => {
        if (!reportData.length) return

        const labels = reportData.map(d => d.month_label)
        const joinersMap = reportData.map(d => d.joiners)
        const leaversMap = reportData.map(d => d.leavers)

        if (chartInstanceRef.current) {
            chartInstanceRef.current.destroy()
        }

        const ctx = canvasRef.current.getContext('2d')

        // Using global window.Chart which is loaded via CDN in index.html
        if (window.Chart) {
            chartInstanceRef.current = new window.Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Joiners',
                            data: joinersMap,
                            backgroundColor: '#06C270', // Success green
                            borderRadius: 4,
                        },
                        {
                            label: 'Leavers',
                            data: leaversMap,
                            backgroundColor: '#FF3B3B', // Error red
                            borderRadius: 4,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    }
                }
            })
        }
    }, [reportData])


    const totalJoiners = reportData.reduce((acc, curr) => acc + curr.joiners, 0)
    const totalLeavers = reportData.reduce((acc, curr) => acc + curr.leavers, 0)

    return (
        <div className="reports-page">
            <div className="reports-header">
                <h1>Monthly Hiring & Attrition</h1>
                <p>Insights into joiner and leaver trends over time.</p>
            </div>

            <div className="reports-controls">
                <div className="date-group">
                    <label>Start Date</label>
                    <input
                        type="date"
                        value={startDate}
                        onChange={e => setStartDate(e.target.value)}
                    />
                </div>
                <div className="date-group">
                    <label>End Date</label>
                    <input
                        type="date"
                        value={endDate}
                        onChange={e => setEndDate(e.target.value)}
                    />
                </div>
                <button className="reports-btn-primary" onClick={fetchReport} disabled={loading}>
                    {loading ? 'Generating...' : 'Generate Report'}
                </button>
            </div>

            {error && <div className="reports-error">{error}</div>}

            <div className="reports-dashboard">
                {/* Metric Cards */}
                <div className="reports-metrics">
                    <div className="metric-card">
                        <h3>Total Joiners</h3>
                        <div className="metric-value text-success">{totalJoiners}</div>
                        <div className="metric-sub">In selected period</div>
                    </div>
                    <div className="metric-card">
                        <h3>Total Leavers</h3>
                        <div className="metric-value text-error">{totalLeavers}</div>
                        <div className="metric-sub">In selected period</div>
                    </div>
                    <div className="metric-card">
                        <h3>Net Change</h3>
                        <div className={`metric-value ${totalJoiners - totalLeavers >= 0 ? 'text-success' : 'text-error'}`}>
                            {totalJoiners - totalLeavers > 0 ? '+' : ''}{totalJoiners - totalLeavers}
                        </div>
                        <div className="metric-sub">In selected period</div>
                    </div>
                </div>

                {/* Chart */}
                <div className="reports-chart-container">
                    {reportData.length === 0 && !loading && !error ? (
                        <div className="reports-empty">No data available for this date range.</div>
                    ) : (
                        <canvas ref={canvasRef}></canvas>
                    )}
                </div>

                {/* Data Table */}
                {reportData.length > 0 && (
                    <div className="reports-table-container">
                        <table className="reports-table">
                            <thead>
                                <tr>
                                    <th>Month</th>
                                    <th>Joiners</th>
                                    <th>Leavers</th>
                                    <th>Net Change</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reportData.map(row => (
                                    <tr key={row.month_key}>
                                        <td><strong>{row.month_label}</strong></td>
                                        <td className="text-success">{row.joiners}</td>
                                        <td className="text-error">{row.leavers}</td>
                                        <td>
                                            <span className={row.joiners - row.leavers >= 0 ? 'net-pos' : 'net-neg'}>
                                                {row.joiners - row.leavers > 0 ? '+' : ''}{row.joiners - row.leavers}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

            </div>
        </div>
    )
}

export default ReportsPage
