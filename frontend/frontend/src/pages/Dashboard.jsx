import { useState, useMemo } from 'react'
import { CreditDisplay } from '../components/CreditDisplay'
import Footer from '../components/Footer'
import './Dashboard.css'

// Mock data for demonstration
const mockData = [
  {
    id: 1,
    timestamp: '2025-01-27 10:23:45',
    status: 'completed',
    user: 'john.doe@university.edu',
    citations: 15,
    errors: 3,
    processing_time: '2.3s',
    source_type: 'paste',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    ip_address: '192.168.1.100',
    session_id: 'sess_abc123',
    validation_id: 'val_789xyz',
    api_version: 'v1.2.0',
    error_details: [
      { type: 'capitalization', count: 2 },
      { type: 'italics', count: 1 }
    ]
  },
  {
    id: 2,
    timestamp: '2025-01-27 10:21:12',
    status: 'completed',
    user: 'student@college.edu',
    citations: 8,
    errors: 0,
    processing_time: '1.1s',
    source_type: 'paste',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    ip_address: '192.168.1.101',
    session_id: 'sess_def456',
    validation_id: 'val_012abc',
    api_version: 'v1.2.0',
    error_details: []
  },
  {
    id: 3,
    timestamp: '2025-01-27 10:18:33',
    status: 'failed',
    user: 'researcher@institute.edu',
    citations: 25,
    errors: null,
    processing_time: '5.7s',
    source_type: 'paste',
    user_agent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    ip_address: '192.168.1.102',
    session_id: 'sess_ghi789',
    validation_id: 'val_345def',
    api_version: 'v1.2.0',
    error_details: [],
    failure_reason: 'Timeout during processing'
  },
  {
    id: 4,
    timestamp: '2025-01-27 10:15:20',
    status: 'completed',
    user: 'professor@university.edu',
    citations: 12,
    errors: 7,
    processing_time: '3.8s',
    source_type: 'paste',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    ip_address: '192.168.1.103',
    session_id: 'sess_jkl012',
    validation_id: 'val_678ghi',
    api_version: 'v1.2.0',
    error_details: [
      { type: 'capitalization', count: 3 },
      { type: 'italics', count: 2 },
      { type: 'doi_format', count: 2 }
    ]
  },
  {
    id: 5,
    timestamp: '2025-01-27 10:12:08',
    status: 'processing',
    user: 'graduate@university.edu',
    citations: 18,
    errors: null,
    processing_time: null,
    source_type: 'paste',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    ip_address: '192.168.1.104',
    session_id: 'sess_mno345',
    validation_id: 'val_901jkl',
    api_version: 'v1.2.0',
    error_details: []
  }
]

export default function Dashboard({
  // Props for API integration
  initialData = [],
  isLoading = false,
  loadError = null,
  onDataUpdate = () => {},
  // Mock mode flag for development/testing
  mockMode = true
}) {
  const [data, setData] = useState(initialData)
  const [loading, setLoading] = useState(isLoading)
  const [error, setError] = useState(loadError)
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
  const rowsPerPage = 10

  // Load data (mock for now, ready for API integration)
  useEffect(() => {
    if (mockMode && data.length === 0) {
      const loadData = async () => {
        setLoading(true)
        setError(null)

        try {
          // Simulate API call
          await new Promise(resolve => setTimeout(resolve, 500))

          // Use mock data for now
          setData(mockData)
          onDataUpdate(mockData)
        } catch (err) {
          setError('Failed to load dashboard data')
          console.error('Dashboard data loading error:', err)
        } finally {
          setLoading(false)
        }
      }

      loadData()
    }
  }, [mockMode, data.length, onDataUpdate])

  // Retry function for error state
  const handleRetry = () => {
    if (mockMode) {
      // Reload mock data
      setData(mockData)
      setError(null)
      setLoading(false)
    } else {
      // Let parent handle retry through props
      onDataUpdate([])
    }
  }

  // Function to update data from API integration
  const updateData = (newData) => {
    setData(newData)
    setError(null)
    setLoading(false)
  }

  // Expose data update function to parent
  useEffect(() => {
    if (onDataUpdate) {
      onDataUpdate(data)
    }
  }, [data, onDataUpdate])

  // Helper function to parse date and apply date range filter
  const isInDateRange = (timestamp, dateRange) => {
    const itemDate = new Date(timestamp.replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/, '$1-$2-$3T$4:$5:$6'))
    const now = new Date()

    switch (dateRange) {
      case '1h':
        return (now - itemDate) <= (60 * 60 * 1000) // 1 hour
      case '24h':
        return (now - itemDate) <= (24 * 60 * 60 * 1000) // 24 hours
      case '7d':
        return (now - itemDate) <= (7 * 24 * 60 * 60 * 1000) // 7 days
      case '30d':
        return (now - itemDate) <= (30 * 24 * 60 * 60 * 1000) // 30 days
      default:
        return true
    }
  }

  // Filter data based on filters
  const filteredData = useMemo(() => {
    return data.filter(item => {
      // Date range filter
      if (!isInDateRange(item.timestamp, filters.dateRange)) {
        return false
      }

      // Status filter
      if (filters.status !== 'all' && item.status !== filters.status) {
        return false
      }

      // User filter
      if (filters.user && !item.user.toLowerCase().includes(filters.user.toLowerCase())) {
        return false
      }

      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase()
        return (
          item.user.toLowerCase().includes(searchLower) ||
          item.validation_id.toLowerCase().includes(searchLower) ||
          item.session_id.toLowerCase().includes(searchLower)
        )
      }

      return true
    })
  }, [data, filters])

  // Sort data
  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => {
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
  }, [filteredData, sortConfig])

  // Pagination
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage
    return sortedData.slice(startIndex, startIndex + rowsPerPage)
  }, [sortedData, currentPage, rowsPerPage])

  const totalPages = Math.ceil(sortedData.length / rowsPerPage)

  // Calculate stats
  const stats = useMemo(() => {
    const total = data.length
    const completed = data.filter(item => item.status === 'completed').length
    const failed = data.filter(item => item.status === 'failed').length
    const processing = data.filter(item => item.status === 'processing').length
    const totalCitations = data.reduce((sum, item) => sum + (item.citations || 0), 0)
    const totalErrors = data.reduce((sum, item) => sum + (item.errors || 0), 0)
    const avgProcessingTime = data
      .filter(item => item.processing_time)
      .reduce((sum, item, _, arr) => {
        const time = parseFloat(item.processing_time.replace('s', ''))
        return sum + time / arr.length
      }, 0)

    return {
      total,
      completed,
      failed,
      processing,
      totalCitations,
      totalErrors,
      avgProcessingTime: avgProcessingTime.toFixed(1)
    }
  }, [data])

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
          <CreditDisplay />
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
              onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
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
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
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
              onChange={(e) => setFilters(prev => ({ ...prev, user: e.target.value }))}
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
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
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
              <p className="stat-value">{stats.total}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h3>Completed</h3>
              <p className="stat-value">{stats.completed}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">❌</div>
            <div className="stat-content">
              <h3>Failed</h3>
              <p className="stat-value">{stats.failed}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <h3>Total Citations</h3>
              <p className="stat-value">{stats.totalCitations}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <h3>Total Errors</h3>
              <p className="stat-value">{stats.totalErrors}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⏱️</div>
            <div className="stat-content">
              <h3>Avg Processing</h3>
              <p className="stat-value">{stats.avgProcessingTime}s</p>
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
                  Showing {paginatedData.length} of {sortedData.length} results
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
                    onClick={() => handleSort('citations')}
                  >
                    Citations {getSortIcon('citations')}
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
                    <td className="number-cell">{item.citations}</td>
                    <td className="number-cell error-cell">
                      {item.errors !== null ? item.errors : '-'}
                    </td>
                    <td className="time-cell">{item.processing_time || '-'}</td>
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
              )}
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
                  <label>Citations Processed</label>
                  <p>{selectedRow.citations}</p>
                </div>

                <div className="detail-group">
                  <label>Errors Found</label>
                  <p>{selectedRow.errors !== null ? selectedRow.errors : 'N/A'}</p>
                </div>

                <div className="detail-group">
                  <label>Processing Time</label>
                  <p>{selectedRow.processing_time || 'N/A'}</p>
                </div>

                {selectedRow.failure_reason && (
                  <div className="detail-group detail-group-full">
                    <label>Failure Reason</label>
                    <p className="failure-reason">{selectedRow.failure_reason}</p>
                  </div>
                )}

                {selectedRow.error_details && selectedRow.error_details.length > 0 && (
                  <div className="detail-group detail-group-full">
                    <label>Error Breakdown</label>
                    <div className="error-breakdown">
                      {selectedRow.error_details.map((error, index) => (
                        <div key={index} className="error-item">
                          <span className="error-type">{error.type}</span>
                          <span className="error-count">{error.count} occurrences</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="detail-group detail-group-full">
                  <label>User Agent</label>
                  <p className="user-agent">{selectedRow.user_agent}</p>
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