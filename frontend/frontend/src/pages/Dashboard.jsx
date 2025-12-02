import { useState, useMemo, useEffect } from 'react'
import { CreditDisplay } from '../components/CreditDisplay'
import Footer from '../components/Footer'

// API base URL - use environment variable or production-ready default
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8001')

// Function to fetch dashboard data from API
const fetchDashboardData = async (filters = {}) => {
  const params = new URLSearchParams()

  // Add filter parameters if they have values
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== 'all') {
      params.append(key, value)
    }
  })

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/dashboard?${params}`, {
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`Failed to fetch dashboard data: ${response.status}`)
    }

    return response.json()
  } catch (error) {
    clearTimeout(timeoutId)
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again')
    }
    throw error
  }
}

// Function to fetch dashboard stats from API
const fetchDashboardStats = async () => {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`Failed to fetch dashboard stats: ${response.status}`)
    }

    return response.json()
  } catch (error) {
    clearTimeout(timeoutId)
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again')
    }
    throw error
  }
}

export default function Dashboard() {
  const [data, setData] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(new Date())
  const [filters, setFilters] = useState({
    dateRange: '24h',
    status: 'all',
    user: '',
    search: ''
  })
  const [sortConfig, setSortConfig] = useState({
    key: 'timestamp',
    direction: 'desc'
  })
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedRow, setSelectedRow] = useState(null)
  const [selectedRowCitations, setSelectedRowCitations] = useState([])
  const [citationsLoading, setCitationsLoading] = useState(false)
  const rowsPerPage = 10

  // Load data from API
  const loadData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true)
      }
      setError(null)

      // Fetch both data and stats in parallel
      const [dataResult, statsResult] = await Promise.all([
        fetchDashboardData(filters),
        fetchDashboardStats()
      ])

      setData(dataResult.jobs || [])
      setStats(statsResult)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err.message)
      console.error('Dashboard data loading error:', err)
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }

  // Initial data load
  useEffect(() => {
    loadData()
  }, [])

  // Refresh data when filters change
  useEffect(() => {
    setCurrentPage(1) // Reset to first page when filters change
    loadData(false)
  }, [filters.dateRange, filters.status, filters.user, filters.search])

  // Fetch citations when a row is selected
  useEffect(() => {
    const jobId = selectedRow?.validation_id || selectedRow?.id
    if (jobId) {
      setCitationsLoading(true)
      fetch(`${API_BASE_URL}/api/validations/${jobId}/citations`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch citations')
          return res.json()
        })
        .then(data => {
          setSelectedRowCitations(data.citations || [])
        })
        .catch(err => {
          console.error('Error fetching citations:', err)
          setSelectedRowCitations([])
        })
        .finally(() => {
          setCitationsLoading(false)
        })
    } else {
      setSelectedRowCitations([])
    }
  }, [selectedRow])

  // Manual refresh function
  const handleRefresh = () => {
    loadData()
  }

  // Retry function for error state
  const handleRetry = () => {
    loadData()
  }

  // Function to update filters from filter section
  const updateFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  // Apply client-side filtering and sorting
  const processedData = useMemo(() => {
    let filtered = [...data]

    // Sort data
    filtered.sort((a, b) => {
      if (sortConfig.key === 'token_usage') {
        const aTokens = a.token_usage?.total ?? 0
        const bTokens = b.token_usage?.total ?? 0
        return sortConfig.direction === 'asc' ? aTokens - bTokens : bTokens - aTokens
      }

      let aValue = a[sortConfig.key]
      let bValue = b[sortConfig.key]

      // Handle numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue
      }

      // Handle string values
      aValue = String(aValue || '').toLowerCase()
      bValue = String(bValue || '').toLowerCase()

      if (sortConfig.direction === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })

    return filtered
  }, [data, sortConfig])

  // Pagination
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage
    return processedData.slice(startIndex, startIndex + rowsPerPage)
  }, [processedData, currentPage, rowsPerPage])

  const totalPages = Math.ceil(processedData.length / rowsPerPage)

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <span className="sort-icon">↕</span>
    }
    return sortConfig.direction === 'asc' ? <span className="sort-icon">↑</span> : <span className="sort-icon">↓</span>
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      completed: { class: 'status-completed', text: 'Completed', icon: '✓' },
      failed: { class: 'status-failed', text: 'Failed', icon: '✗' },
      processing: { class: 'status-processing', text: 'Processing', icon: '⏳' }
    }

    const config = statusConfig[status] || statusConfig.completed
    return (
      <span className={`status-badge ${config.class}`}>
        <span className="status-icon">{config.icon}</span>
        {config.text}
      </span>
    )
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="logo">
            <h1 className="dashboard-title">Operations Dashboard</h1>
            <p className="dashboard-subtitle">Monitor validation requests and system health</p>
          </div>
          <div className="header-actions">
            <div className="last-refresh">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
            <button
              onClick={handleRefresh}
              className="refresh-button"
              disabled={loading}
              aria-label="Refresh dashboard data"
            >
              {loading ? '⟳ Refreshing...' : '🔄 Refresh'}
            </button>
            <CreditDisplay />
          </div>
        </div>
      </header>

      {/* Filters Section */}
      <section className="filters-section">
        <div className="filters-container">
          <div className="filter-group">
            <label htmlFor="dateRange">Time Range</label>
            <select
              id="dateRange"
              value={filters.dateRange}
              onChange={(e) => updateFilter('dateRange', e.target.value)}
              className="filter-select"
              aria-label="Select time range for filtering validation requests"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="status">Status</label>
            <select
              id="status"
              value={filters.status}
              onChange={(e) => updateFilter('status', e.target.value)}
              className="filter-select"
              aria-label="Filter validation requests by status"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="processing">Processing</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="user">User</label>
            <input
              id="user"
              type="text"
              placeholder="Filter by user email..."
              value={filters.user}
              onChange={(e) => updateFilter('user', e.target.value)}
              className="filter-input"
              aria-label="Filter by user email"
              aria-describedby="user-filter-description"
            />
            <span id="user-filter-description" className="sr-only">
              Enter a user email to filter validation requests by user
            </span>
          </div>

          <div className="filter-group filter-group-full">
            <label htmlFor="search">Search</label>
            <input
              id="search"
              type="text"
              placeholder="Search by user, session ID, or validation ID..."
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
              className="filter-input"
              aria-label="Search validation requests"
              aria-describedby="search-description"
            />
            <span id="search-description" className="sr-only">
              Search validation requests by user email, session ID, or validation ID
            </span>
          </div>
        </div>
      </section>

      {/* Stats Summary */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <h3>Total Requests</h3>
              <p className="stat-value">{stats.total_requests || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h3>Completed</h3>
              <p className="stat-value">{stats.completed || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">❌</div>
            <div className="stat-content">
              <h3>Failed</h3>
              <p className="stat-value">{stats.failed || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <h3>Total Citations</h3>
              <p className="stat-value">{stats.total_citations || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <h3>Total Errors</h3>
              <p className="stat-value">{stats.total_errors || 0}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⏱️</div>
            <div className="stat-content">
              <h3>Avg Processing</h3>
              <p className="stat-value">{stats.avg_processing_time || '0.0s'}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Data Table */}
      <section className="table-section">
        <div className="table-container">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading dashboard data...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <h3>Failed to load dashboard data</h3>
              <p>{error}</p>
              <button onClick={handleRetry} className="retry-button">
                Retry
              </button>
            </div>
          ) : data.length === 0 ? (
            <div className="empty-state">
              <h3>No validation requests found</h3>
              <p>Try adjusting your filters or check back later.</p>
            </div>
          ) : (
            <>
              <div className="table-header">
                <h2>Validation Requests</h2>
                <p className="table-info">
                  Showing {paginatedData.length} of {processedData.length} results
                </p>
              </div>

              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('timestamp')}
                      >
                        Timestamp {getSortIcon('timestamp')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('status')}
                      >
                        Status {getSortIcon('status')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('user')}
                      >
                        User {getSortIcon('user')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('citation_count')}
                      >
                        Citations {getSortIcon('citation_count')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('errors')}
                      >
                        Errors {getSortIcon('errors')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('processing_time')}
                      >
                        Processing Time {getSortIcon('processing_time')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('token_usage')}
                      >
                        Tokens {getSortIcon('token_usage')}
                      </th>
                      <th
                        className="sortable-header"
                        onClick={() => handleSort('revealed')}
                      >
                        Revealed {getSortIcon('revealed')}
                      </th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedData.map((item) => (
                      <tr
                        key={item.id}
                        className={selectedRow?.id === item.id ? 'selected-row' : ''}
                      >
                        <td className="timestamp-cell">{item.timestamp}</td>
                        <td className="status-cell">{getStatusBadge(item.status)}</td>
                        <td className="user-cell" title={item.user}>
                          {item.user.length > 25 ? `${item.user.substring(0, 25)}...` : item.user}
                        </td>
                        <td className="number-cell">{item.citation_count || 0}</td>
                        <td className="number-cell error-cell">
                          {item.errors !== null ? item.errors : '-'}
                        </td>
                        <td className="time-cell">{item.processing_time || '-'}</td>
                        <td className="number-cell">
                          {item.token_usage?.total?.toLocaleString() ?? '-'}
                        </td>
                        <td className="reveal-cell">
                          {item.revealed === 'Yes' && (
                            <span className="reveal-status revealed">Yes</span>
                          )}
                          {item.revealed === 'No' && (
                            <span className="reveal-status not-revealed">No</span>
                          )}
                          {item.revealed === 'N/A' && (
                            <span className="reveal-status not-applicable">N/A</span>
                          )}
                        </td>
                        <td className="actions-cell">
                          <button
                            onClick={() => setSelectedRow(item)}
                            className="details-button"
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  <div className="pagination-info">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="pagination-controls">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="pagination-button"
                    >
                      First
                    </button>
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="pagination-button"
                    >
                      Previous
                    </button>
                    <span className="pagination-current">{currentPage}</span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="pagination-button"
                    >
                      Next
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="pagination-button"
                    >
                      Last
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {/* Details Modal */}
      {selectedRow && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedRow(null)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setSelectedRow(null)
            }
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 id="modal-title">Validation Request Details</h2>
              <button
                onClick={() => setSelectedRow(null)}
                className="modal-close"
                aria-label="Close details modal"
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              <div className="details-grid">
                <div className="detail-group">
                  <label>Validation ID</label>
                  <p>{selectedRow.validation_id}</p>
                </div>

                <div className="detail-group">
                  <label>Session ID</label>
                  <p>{selectedRow.session_id}</p>
                </div>

                <div className="detail-group">
                  <label>Timestamp</label>
                  <p>{selectedRow.timestamp}</p>
                </div>

                <div className="detail-group">
                  <label>Status</label>
                  <p>{getStatusBadge(selectedRow.status)}</p>
                </div>

                <div className="detail-group">
                  <label>User</label>
                  <p>{selectedRow.user}</p>
                </div>

                <div className="detail-group">
                  <label>IP Address</label>
                  <p>{selectedRow.ip_address}</p>
                </div>

                <div className="detail-group">
                  <label>Source Type</label>
                  <p>{selectedRow.source_type}</p>
                </div>

                <div className="detail-group">
                  <label>API Version</label>
                  <p>{selectedRow.api_version}</p>
                </div>

                <div className="detail-group">
                  <label>Citations Processed ({selectedRow.citation_count || 0})</label>
                  {citationsLoading ? (
                    <p>Loading citations...</p>
                  ) : selectedRowCitations.length > 0 ? (
                    <div style={{ maxHeight: '300px', overflowY: 'auto', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', backgroundColor: '#f9f9f9' }}>
                      {selectedRowCitations.map((citation, index) => (
                        <div key={index} style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: index < selectedRowCitations.length - 1 ? '1px solid #ddd' : 'none' }}>
                          <div style={{ fontSize: '0.85em', color: '#666', marginBottom: '4px' }}>Citation {index + 1}</div>
                          <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.9em' }}>{citation.citation_text}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>No citations found</p>
                  )}
                </div>

                <div className="detail-group">
                  <label>Errors Found</label>
                  <p>{selectedRow.errors !== null ? selectedRow.errors : 'N/A'}</p>
                </div>

                <div className="detail-group">
                  <label>Token Usage</label>
                  {selectedRow.token_usage ? (
                    <p>
                      Prompt: {selectedRow.token_usage.prompt?.toLocaleString() ?? 'N/A'} |{' '}
                      Completion: {selectedRow.token_usage.completion?.toLocaleString() ?? 'N/A'} |{' '}
                      Total: {selectedRow.token_usage.total?.toLocaleString() ?? 'N/A'}
                    </p>
                  ) : (
                    <p>N/A</p>
                  )}
                </div>

                <div className="detail-group">
                  <label>Processing Time</label>
                  <p>{selectedRow.processing_time || 'N/A'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}