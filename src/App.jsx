import React, { useState, useEffect, useMemo } from 'react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [rules, setRules] = useState({});
  const [theme, setTheme] = useState('dark');
  const [apiKey, setApiKey] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState({ key: 'manufactured_date', direction: 'asc' });
  const [dragActive, setDragActive] = useState(false);
  const [hoveredSlice, setHoveredSlice] = useState(null);
  
  const [overrideMfg, setOverrideMfg] = useState('');
  const [overrideModel, setOverrideModel] = useState('');
  const [overrideType, setOverrideType] = useState('');
  const [probableTypos, setProbableTypos] = useState([]);
  const [averageConfidence, setAverageConfidence] = useState(null);
  const [formattingCorrections, setFormattingCorrections] = useState('');

  const rowsPerPage = 15;

  // Initialize theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Load cached rules on mount
  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/rules`);
      if (res.ok) {
        const rulesData = await res.json();
        setRules(rulesData);
      }
    } catch (err) {
      console.error("Failed to load rules:", err);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        processFile(droppedFile);
      } else {
        setError("Only CSV files are supported.");
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      processFile(selectedFile);
    }
  };

  const processFile = async (fileToProcess) => {
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', fileToProcess);

    try {
      const headers = {};
      if (apiKey.trim()) {
        headers['X-OpenAI-Key'] = apiKey.trim();
      }

      const res = await fetch(`${API_BASE}/api/enrich`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Error processing CSV file");
      }

      const result = await res.json();
      setData(result.data || []);
      setMetrics(result.metrics || []);
      setProbableTypos(result.probable_typos || []);
      setAverageConfidence(result.average_confidence || null);
      setFormattingCorrections(result.formatting_corrections || '');
      setCurrentPage(1);
      fetchRules(); // Refresh rules in case new ones were learned
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOverrideSubmit = async (e) => {
    e.preventDefault();
    if (!overrideMfg.trim() || !overrideModel.trim() || !overrideType.trim()) return;

    try {
      const key = `${overrideMfg.trim().toLowerCase()}|${overrideModel.trim().toLowerCase()}`;
      const res = await fetch(`${API_BASE}/api/rules/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, device_type: overrideType.trim() }),
      });

      if (res.ok) {
        setOverrideMfg('');
        setOverrideModel('');
        setOverrideType('');
        fetchRules();
        // If we currently have a file loaded, re-process it to apply the new rules
        if (file) {
          processFile(file);
        }
      }
    } catch (err) {
      console.error("Failed to save override rule:", err);
    }
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Sorting logic
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Filter and Sort Data
  const processedData = useMemo(() => {
    let result = [...data];

    // Search filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(row => {
        return (
          row.manufacturer?.toLowerCase().includes(term) ||
          row.model?.toLowerCase().includes(term) ||
          row['serial number']?.toLowerCase().includes(term) ||
          row.manufactured_date?.toLowerCase().includes(term) ||
          row.device_type?.toLowerCase().includes(term)
        );
      });
    }

    // Sort
    const { key, direction } = sortConfig;
    if (key) {
      result.sort((a, b) => {
        const valA = a[key] ? String(a[key]).toLowerCase() : '';
        const valB = b[key] ? String(b[key]).toLowerCase() : '';
        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [data, searchTerm, sortConfig]);

  // Pagination
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage;
    return processedData.slice(startIndex, startIndex + rowsPerPage);
  }, [processedData, currentPage]);

  const totalPages = Math.ceil(processedData.length / rowsPerPage);

  // SVG Pie Chart Coordinates helper
  const getCoordinatesForPercent = (percent) => {
    const x = Math.cos(2 * Math.PI * percent);
    const y = Math.sin(2 * Math.PI * percent);
    return [x, y];
  };

  // Generate SVG Pie Chart Paths
  const piePaths = useMemo(() => {
    let cumulativePercent = 0;
    const colors = [
      '#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
      '#ec4899', '#14b8a6', '#6366f1', '#a855f7', '#f43f5e'
    ];

    return metrics.map((metric, index) => {
      const percent = metric.percentage / 100;
      const [startX, startY] = getCoordinatesForPercent(cumulativePercent);
      cumulativePercent += percent;
      const [endX, endY] = getCoordinatesForPercent(cumulativePercent);

      // Centered at 100, 100, radius 80
      const x1 = 100 + startX * 80;
      const y1 = 100 + startY * 80;
      const x2 = 100 + endX * 80;
      const y2 = 100 + endY * 80;

      const largeArcFlag = percent > 0.5 ? 1 : 0;
      const pathData = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

      return {
        path: pathData,
        color: colors[index % colors.length],
        label: metric.device_type,
        percentage: metric.percentage,
        count: metric.count
      };
    });
  }, [metrics]);

  const activeHoverInfo = hoveredSlice !== null ? piePaths[hoveredSlice] : null;

  // Export sorted, filtered CSV
  const handleExport = () => {
    if (processedData.length === 0) return;

    // Build CSV string
    const headers = Object.keys(processedData[0]);
    const csvRows = [
      headers.join(','),
      ...processedData.map(row => 
        headers.map(fieldName => JSON.stringify(row[fieldName] || '')).join(',')
      )
    ];

    const csvText = csvRows.join('\n');
    const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", file ? `enriched_${file.name}` : "enriched_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header glass-panel" style={{ padding: '1.2rem 2rem' }}>
        <div className="brand-section">
          <h1>Equiply Portal</h1>
          <p>Hospital Equipment Data Enrichment Dashboard</p>
        </div>
        <button 
          className="theme-toggle-btn" 
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
        </button>
      </header>

      {/* Main Grid Layout */}
      <main className="dashboard-grid">
        
        {/* Left Column: Sidebar panels */}
        <aside className="sidebar-panel" aria-label="Upload and Settings">
          
          {/* File Upload Zone */}
          <div className="upload-card glass-panel">
            <h2>CSV Data Upload</h2>
            <div 
              className={`dropzone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-upload').click()}
              tabIndex={0}
              role="button"
              aria-label="Upload CSV File. Drag and drop a CSV file here, or press Enter or Space to browse local files"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  document.getElementById('file-upload').click();
                }
              }}
            >
              <input 
                type="file" 
                id="file-upload" 
                style={{ display: 'none' }} 
                accept=".csv"
                onChange={handleFileChange}
              />
              <div className="dropzone-icon" aria-hidden="true">📥</div>
              <div className="dropzone-text">
                <p>Drag and drop CSV here</p>
                <span>or click to browse local files</span>
              </div>
            </div>
            {file && (
              <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'hsl(var(--success-color))', fontWeight: '500' }}>
                Selected: {file.name}
              </div>
            )}
          </div>

          {/* Optional LLM Integration */}
          <div className="api-config-card glass-panel">
            <h3>🤖 LLM Enrichment Config</h3>
            <p id="llm-config-desc" style={{ fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', marginBottom: '0.75rem' }}>
              Add an OpenAI key to dynamically resolve unknown serial patterns via gpt-5.4-mini.
            </p>
            <label htmlFor="api-key-input" style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', border: 0 }}>OpenAI API Key</label>
            <input 
              id="api-key-input"
              type="password" 
              placeholder="OpenAI API Key" 
              className="input-field"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              aria-describedby="llm-config-desc"
            />
          </div>

          {/* Rules Override Manager */}
          <div className="rules-card glass-panel">
            <h3>✏️ Add Custom Override</h3>
            <form onSubmit={handleOverrideSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <label htmlFor="override-mfg" style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '0.25rem', display: 'block' }}>Manufacturer</label>
                <input 
                  id="override-mfg"
                  type="text" 
                  placeholder="Manufacturer (e.g. ZOLL)" 
                  className="input-field"
                  value={overrideMfg}
                  onChange={e => setOverrideMfg(e.target.value)}
                  required
                />
              </div>
              <div>
                <label htmlFor="override-model" style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '0.25rem', display: 'block' }}>Model</label>
                <input 
                  id="override-model"
                  type="text" 
                  placeholder="Model (e.g. M SERIES)" 
                  className="input-field"
                  value={overrideModel}
                  onChange={e => setOverrideModel(e.target.value)}
                  required
                />
              </div>
              <div>
                <label htmlFor="override-type" style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '0.25rem', display: 'block' }}>Standard Device Type</label>
                <input 
                  id="override-type"
                  type="text" 
                  placeholder="Standard Device Type" 
                  className="input-field"
                  value={overrideType}
                  onChange={e => setOverrideType(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-secondary" style={{ marginTop: '0.25rem', fontSize: '0.8rem', padding: '0.5rem' }}>
                Save Override Rule
              </button>
            </form>
            
            <div style={{ marginTop: '1.25rem' }}>
              <h4 style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Active Rules ({Object.keys(rules).length})</h4>
              <div className="rules-list">
                {Object.entries(rules).map(([key, val]) => (
                  <div className="rule-item" key={key}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span className="rule-name">{key.split('|')[0].toUpperCase()}</span>
                      <span style={{ fontSize: '0.65rem', color: 'hsl(var(--text-secondary))' }}>{val.device_type}</span>
                    </div>
                    <span className="rule-type-badge">{val.rule_type || 'cached'}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </aside>

        {/* Right Column: Main Content */}
        <div className="main-panel">
          
          {/* Stats Bar */}
          {data.length > 0 && (
            <div className="stats-banner">
              <div className="stat-item glass-panel">
                <span className="stat-label">Total Records</span>
                <span className="stat-value">{processedData.length}</span>
              </div>
              <div className="stat-item glass-panel">
                <span className="stat-label">Device Types</span>
                <span className="stat-value">{metrics.length}</span>
              </div>
              <div className="stat-item glass-panel">
                <span className="stat-label">Earliest Date</span>
                <span className="stat-value" style={{ fontSize: '1.25rem', fontWeight: '800', marginTop: '0.4rem' }}>
                  {processedData[0]?.manufactured_date}
                </span>
              </div>
              <div className="stat-item glass-panel">
                <span className="stat-label">Latest Date</span>
                <span className="stat-value" style={{ fontSize: '1.25rem', fontWeight: '800', marginTop: '0.4rem' }}>
                  {processedData[processedData.length - 1]?.manufactured_date}
                </span>
              </div>
              {averageConfidence !== null && (
                <div className="stat-item glass-panel" style={{ borderLeft: '4px solid hsl(var(--primary-color))' }}>
                  <span className="stat-label">Data Confidence</span>
                  <span className="stat-value" style={{ color: 'hsl(var(--primary-color))', fontSize: '1.25rem', fontWeight: '800', marginTop: '0.4rem' }}>{averageConfidence}%</span>
                </div>
              )}
            </div>
          )}

          {/* Loader or Error states */}
          {loading && (
            <div className="glass-panel loading-overlay">
              <div className="spinner"></div>
              <div className="loading-text">Analyzing & Enriching Equipment Data...</div>
            </div>
          )}

          {error && (
            <div className="glass-panel" style={{ padding: '2rem', borderLeft: '5px solid hsl(var(--danger-color))' }}>
              <h3 style={{ color: 'hsl(var(--danger-color))', marginBottom: '0.5rem' }}>Enrichment Error</h3>
              <p style={{ fontSize: '0.9rem' }}>{error}</p>
            </div>
          )}

          {/* Probable Typos Panel */}
          {!loading && !error && probableTypos.length > 0 && (
            <div className="glass-panel typos-warning-panel" style={{ borderLeft: '4px solid hsl(var(--warning-color))', padding: '1.25rem', marginBottom: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'hsl(var(--warning-color))', fontSize: '1.1rem', margin: 0 }}>
                ⚠️ Probable Typos to Verify ({probableTypos.length})
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-secondary))', margin: '0.5rem 0 1rem 0' }}>
                The following models were identified as probable typos. Click "Verify" to load details and save an override rule.
              </p>
              <div className="typos-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                {probableTypos.map((typo, idx) => (
                  <div key={idx} className="typo-card" style={{ background: 'hsl(var(--text-secondary) / 0.05)', padding: '0.75rem', borderRadius: 'var(--border-radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.85rem' }}>{typo.manufacturer} {typo.model}</div>
                      <div style={{ fontSize: '0.75rem', color: 'hsl(var(--text-secondary))', marginTop: '0.2rem' }}>
                        Resolved: <span style={{ fontWeight: '500' }}>{typo.device_type}</span> ({typo.confidence}% confidence)
                      </div>
                    </div>
                    <button 
                      className="btn btn-secondary" 
                      style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', margin: 0 }}
                      onClick={() => {
                        setOverrideMfg(typo.manufacturer);
                        setOverrideModel(typo.model);
                        setOverrideType(typo.device_type);
                        const form = document.querySelector('.rules-card form');
                        if (form) form.scrollIntoView({ behavior: 'smooth' });
                      }}
                    >
                      Verify
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Applied Formatting Corrections Log */}
          {!loading && !error && formattingCorrections && (
            <div className="glass-panel corrections-panel" style={{ borderLeft: '4px solid hsl(var(--primary-color))', padding: '1.25rem', marginBottom: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'hsl(var(--primary-color))', fontSize: '1.1rem', margin: 0 }}>
                🔧 Auto-Applied Formatting Corrections Log
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-secondary))', margin: '0.5rem 0 1rem 0' }}>
                The enrichment engine dynamically corrected spelling, spacing, and serial number formatting inconsistencies based on majority dataset patterns:
              </p>
              <pre style={{
                background: 'rgba(0, 0, 0, 0.2)',
                padding: '1rem',
                borderRadius: 'var(--border-radius-sm)',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                margin: 0,
                color: 'hsl(var(--text-secondary))',
                maxHeight: '200px',
                overflowY: 'auto'
              }}>
                {formattingCorrections}
              </pre>
            </div>
          )}

          {/* Data Displays */}
          {!loading && !error && data.length > 0 && (
            <section className="main-panel" aria-label="Dashboard Metrics and Records">
              {/* Pie Chart Card */}
              <div className="chart-card glass-panel">
                <h3>Device Type Distribution</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
                  <div className="svg-chart-container">
                    <svg 
                      viewBox="0 0 200 200" 
                      width="100%" 
                      height="100%" 
                      style={{ transform: 'rotate(-90deg)' }}
                      role="img"
                      aria-label="Pie chart showing hospital device type distribution"
                    >
                      <title>Device Type Distribution</title>
                      {piePaths.map((slice, idx) => (
                        <path
                          key={idx}
                          d={slice.path}
                          fill={slice.color}
                          className="pie-slice"
                          onMouseEnter={() => setHoveredSlice(idx)}
                          onMouseLeave={() => setHoveredSlice(null)}
                          opacity={hoveredSlice !== null && hoveredSlice !== idx ? 0.6 : 1}
                        />
                      ))}
                    </svg>
                    <div className="chart-center-text" aria-hidden="true">
                      <span className="chart-center-val">
                        {activeHoverInfo ? `${activeHoverInfo.percentage}%` : `${data.length}`}
                      </span>
                      <span className="chart-center-lbl">
                        {activeHoverInfo ? activeHoverInfo.label : 'Devices'}
                      </span>
                    </div>
                  </div>

                  <div className="chart-legend">
                    {piePaths.map((slice, idx) => (
                      <div 
                        className="legend-item" 
                        key={idx}
                        onMouseEnter={() => setHoveredSlice(idx)}
                        onMouseLeave={() => setHoveredSlice(null)}
                        style={{ background: hoveredSlice === idx ? 'hsl(var(--text-secondary) / 0.1)' : 'transparent' }}
                      >
                        <div className="legend-left">
                          <span className="legend-dot" style={{ backgroundColor: slice.color }} aria-hidden="true"></span>
                          <span className="legend-name">{slice.label}</span>
                        </div>
                        <span className="legend-right">{slice.count} ({slice.percentage}%)</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Data Table */}
              <div className="table-card glass-panel">
                <div className="table-header-controls">
                  <div className="table-title">Enriched Records</div>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="search-input-wrapper">
                      <label htmlFor="search-records-input" style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', border: 0 }}>Search records</label>
                      <input 
                        id="search-records-input"
                        type="text" 
                        placeholder="🔍 Search records..." 
                        className="input-field" 
                        style={{ maxWidth: '300px', margin: 0 }}
                        value={searchTerm}
                        onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                      />
                    </div>
                    <button className="btn" style={{ maxWidth: '200px' }} onClick={handleExport}>
                      📥 Export Enriched CSV
                    </button>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="data-table" aria-label="Enriched Equipment Records">
                    <thead>
                      <tr>
                        <th 
                          scope="col"
                          role="columnheader"
                          aria-sort={sortConfig.key === 'manufacturer' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                        >
                          <button 
                            type="button"
                            onClick={() => handleSort('manufacturer')}
                            style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', width: '100%', textAlign: 'left', padding: 0 }}
                          >
                            Manufacturer {sortConfig.key === 'manufacturer' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
                          </button>
                        </th>
                        <th 
                          scope="col"
                          role="columnheader"
                          aria-sort={sortConfig.key === 'model' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                        >
                          <button 
                            type="button"
                            onClick={() => handleSort('model')}
                            style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', width: '100%', textAlign: 'left', padding: 0 }}
                          >
                            Model {sortConfig.key === 'model' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
                          </button>
                        </th>
                        <th 
                          scope="col"
                          role="columnheader"
                          aria-sort={sortConfig.key === 'serial number' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                        >
                          <button 
                            type="button"
                            onClick={() => handleSort('serial number')}
                            style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', width: '100%', textAlign: 'left', padding: 0 }}
                          >
                            Serial Number {sortConfig.key === 'serial number' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
                          </button>
                        </th>
                        <th 
                          scope="col"
                          role="columnheader"
                          aria-sort={sortConfig.key === 'manufactured_date' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                        >
                          <button 
                            type="button"
                            onClick={() => handleSort('manufactured_date')}
                            style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', width: '100%', textAlign: 'left', padding: 0 }}
                          >
                            Manufactured Date {sortConfig.key === 'manufactured_date' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
                          </button>
                        </th>
                        <th 
                          scope="col"
                          role="columnheader"
                          aria-sort={sortConfig.key === 'device_type' ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                        >
                          <button 
                            type="button"
                            onClick={() => handleSort('device_type')}
                            style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', width: '100%', textAlign: 'left', padding: 0 }}
                          >
                            Device Type {sortConfig.key === 'device_type' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
                          </button>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedData.map((row, idx) => (
                        <tr key={idx}>
                          <td>{row.manufacturer}</td>
                          <td>{row.model}</td>
                          <td>{row['serial number'] || row.serial_number}</td>
                          <td style={{ fontWeight: '600' }}>{row.manufactured_date}</td>
                          <td>
                            <span className="rule-type-badge" style={{ backgroundColor: 'hsl(var(--primary-color) / 0.08)' }}>
                              {row.device_type}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Controls */}
                <div className="table-pagination">
                  <span>
                    Showing {Math.min(processedData.length, (currentPage - 1) * rowsPerPage + 1)} to {Math.min(processedData.length, currentPage * rowsPerPage)} of {processedData.length} records
                  </span>
                  {totalPages > 1 && (
                    <nav className="pagination-btn-group" aria-label="Pagination Navigation">
                      <button 
                        className="pagination-btn" 
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        aria-label="Go to previous page"
                      >
                        Prev
                      </button>
                      <span style={{ alignSelf: 'center', margin: '0 0.5rem', fontWeight: '500' }} aria-current="page">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button 
                        className="pagination-btn" 
                        disabled={currentPage === totalPages}
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        aria-label="Go to next page"
                      >
                        Next
                      </button>
                    </nav>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* Empty State */}
          {!loading && !error && data.length === 0 && (
            <div className="glass-panel empty-state">
              <div className="empty-state-icon" aria-hidden="true">📄</div>
              <h3>No Data Enriched</h3>
              <p>Drag and drop your equipment CSV file in the upload zone to begin parsing and enriching the dataset.</p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}

export default App;
