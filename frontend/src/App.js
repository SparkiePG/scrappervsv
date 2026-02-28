import React, { useState } from 'react';

// A minimal dashboard component. Allows users to enter a URL,
// sends it to the Flask backend to start scraping, and displays
// the results. In a production app you might split this into
// multiple components and add error handling, loading states,
// pagination and data visualisation.

function App() {
  const [url, setUrl] = useState('');
  const [strategy, setStrategy] = useState('combined');
  const [jobId, setJobId] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultUrl, setResultUrl] = useState('');

  // Poll job status until finished
  const pollStatus = async (id) => {
    try {
      const res = await fetch(`http://localhost:5000/status/${id}`);
      const json = await res.json();
      if (json.status === 'pending') {
        // Wait a bit before polling again
        setTimeout(() => pollStatus(id), 1000);
      } else if (json.status === 'finished') {
        setData(json.result);
        setLoading(false);
      } else if (json.error) {
        setError(json.error);
        setLoading(false);
      }
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  const handleScrape = async () => {
    if (!url) return;
    setLoading(true);
    setError(null);
    setData(null);
    setJobId(null);
    setResultUrl(url);
    try {
      const res = await fetch('http://localhost:5000/start_scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, strategy })
      });
      const json = await res.json();
      if (res.status >= 400) {
        setError(json.error || 'Failed to start scrape');
        setLoading(false);
        return;
      }
      const id = json.job_id;
      if (id) {
        setJobId(id);
        // Start polling
        pollStatus(id);
      } else {
        setError(json.error || 'Unknown error');
        setLoading(false);
      }
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 640,
        margin: '0 auto',
        padding: 24,
        fontFamily: 'system-ui, sans-serif',
        color: '#111827',
        backgroundColor: '#ffffff',
        lineHeight: 1.5,
      }}
    >
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0 }}>Web Scraper Dashboard</h1>
        <p style={{ fontSize: 14, color: '#6b7280', marginTop: 4 }}>
          Enter a URL to retrieve text, images and links
        </p>
      </header>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleScrape();
        }}
        style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label htmlFor="url-input" style={{ fontSize: 14, color: '#374151' }}>
            URL
          </label>
          <input
            id="url-input"
            type="url"
            inputMode="url"
            autoComplete="off"
            aria-label="URL to scrape"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            style={{
              padding: '10px 12px',
              borderRadius: 4,
              border: '1px solid #d1d5db',
              fontSize: 14,
              color: '#111827',
            }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label htmlFor="strategy-select" style={{ fontSize: 14, color: '#374151' }}>
            Strategy
          </label>
          <select
            id="strategy-select"
            aria-label="Scraping strategy"
            value={strategy}
            disabled={loading}
            onChange={(e) => setStrategy(e.target.value)}
            style={{
              padding: '10px 12px',
              borderRadius: 4,
              border: '1px solid #d1d5db',
              fontSize: 14,
              color: '#111827',
              backgroundColor: '#fff',
            }}
          >
            <option value="combined">Combined (default)</option>
            <option value="static">Static</option>
            <option value="dynamic">Dynamic</option>
            <option value="api">API</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={loading || !url}
          style={{
            padding: '10px 14px',
            borderRadius: 4,
            border: 'none',
            backgroundColor: loading || !url ? '#9ca3af' : '#3b82f6',
            color: '#ffffff',
            fontSize: 14,
            fontWeight: 600,
            cursor: loading || !url ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Scraping…' : 'Scrape'}
        </button>
      </form>
      {/* Error message */}
      {error && (
        <div
          role="alert"
          style={{ marginTop: 16, color: '#dc2626', fontSize: 14 }}
        >
          {error}
        </div>
      )}
      {/* Results display */}
      {data && (
        <section
          aria-live="polite"
          style={{
            marginTop: 24,
            padding: 16,
            border: '1px solid #e5e7eb',
            borderRadius: 4,
            backgroundColor: '#f9fafb',
          }}
        >
          <h2 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 12px' }}>
            Results for {resultUrl}
          </h2>
          {/* If the result includes a file download, show it */}
          {data.file_content ? (
            <div>
              <p style={{ fontSize: 14, margin: '4px 0' }}>
                <strong>File name:</strong> {data.file_name || 'unknown'}
              </p>
              <p style={{ fontSize: 14, margin: '4px 0' }}>
                <strong>Type:</strong> {data.file_type || 'binary'}
              </p>
              {/* Show a preview if the file is an image, video or audio */}
              {data.file_type && data.file_type.startsWith('image/') && (
                <div style={{ margin: '8px 0' }}>
                  <img
                    src={`data:${data.file_type};base64,${data.file_content}`}
                    alt={data.file_name || 'downloaded image'}
                    style={{ maxWidth: '100%', height: 'auto', borderRadius: 4, border: '1px solid #e5e7eb' }}
                  />
                </div>
              )}
              {data.file_type && data.file_type.startsWith('video/') && (
                <div style={{ margin: '8px 0' }}>
                  <video
                    controls
                    src={`data:${data.file_type};base64,${data.file_content}`}
                    style={{ maxWidth: '100%', borderRadius: 4, border: '1px solid #e5e7eb' }}
                  >
                    Your browser does not support the video tag.
                  </video>
                </div>
              )}
              {data.file_type && data.file_type.startsWith('audio/') && (
                <div style={{ margin: '8px 0' }}>
                  <audio
                    controls
                    src={`data:${data.file_type};base64,${data.file_content}`}
                    style={{ width: '100%' }}
                  >
                    Your browser does not support the audio tag.
                  </audio>
                </div>
              )}
              <p style={{ fontSize: 14, margin: '4px 0' }}>
                <a
                  href={`data:${data.file_type};base64,${data.file_content}`}
                  download={data.file_name || 'download'}
                  style={{ color: '#2563eb', textDecoration: 'underline' }}
                >
                  Download file
                </a>
              </p>
              {/* If extracted text is available (e.g., from PDFs or documents), show a preview */}
              {data.text && data.text.trim() && (
                <p style={{ fontSize: 14, margin: '4px 0' }}>
                  <strong>Extracted text (preview):</strong>{' '}
                  {data.text.slice(0, 300)}
                  {data.text.length > 300 ? '…' : ''}
                </p>
              )}
            </div>
          ) : (
            <div>
              {data.metadata && (
                <div style={{ marginBottom: 12 }}>
                  {data.metadata.title && (
                    <p style={{ fontSize: 14, margin: '4px 0' }}>
                      <strong>Title:</strong> {data.metadata.title}
                    </p>
                  )}
                  {data.metadata.description && (
                    <p style={{ fontSize: 14, margin: '4px 0' }}>
                      <strong>Description:</strong> {data.metadata.description}
                    </p>
                  )}
                </div>
              )}
              <p style={{ fontSize: 14, margin: '4px 0' }}>
                <strong>Text (preview): </strong>
                {data.text ? data.text.slice(0, 300) : ''}
                {data.text && data.text.length > 300 ? '…' : ''}
              </p>
              <p style={{ fontSize: 14, margin: '4px 0' }}>
                <strong>Images:</strong>{' '}
                {Array.isArray(data.images) ? data.images.length : 0}
              </p>
              <p style={{ fontSize: 14, margin: '4px 0' }}>
                <strong>Links:</strong>{' '}
                {Array.isArray(data.links) ? data.links.length : 0}
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default App;