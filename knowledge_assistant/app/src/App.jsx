import { useEffect, useState } from 'react'
import { api } from './api'
import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

function PanelTitle({ children }) {
  return <h2 className="text-lg font-semibold text-gray-900 mb-3">{children}</h2>
}

export default function App() {
  const [health, setHealth] = useState(null)

  // Ingest
  const [urlsText, setUrlsText] = useState('')
  const [ingestLoading, setIngestLoading] = useState(false)
  const [ingestIds, setIngestIds] = useState([])

  // Ask
  const [question, setQuestion] = useState('Briefly explain multi-head attention and cite sources.')
  const [topK, setTopK] = useState(4)
  const [domain, setDomain] = useState('') // optional collection name
  const [askLoading, setAskLoading] = useState(false)
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])

  // Search (placeholder - backend /search not implemented yet)
  const [searchQ, setSearchQ] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)

  useEffect(() => {
    api.get('/health')
      .then(res => setHealth(res.data))
      .catch(() => {})
  }, [])

  const onIngest = async () => {
    const urls = urlsText.split(/\r?\n/).map(u => u.trim()).filter(Boolean)
    if (!urls.length) {
      toast.info('Please enter 1 or more URLs (one per line).')
      return
    }
    setIngestLoading(true)
    setIngestIds([])
    try {
      const resp = await api.post('/ingest', { urls })
      setIngestIds(resp.data?.ids || [])
      toast.success('Ingestion complete.')
    } catch (e) {} finally {
      setIngestLoading(false)
    }
  }

  const onAsk = async () => {
    if (!question.trim()) {
      toast.info('Please enter a question.')
      return
    }
    setAskLoading(true)
    setAnswer('')
    setSources([])
    try {
      const payload = { question, top_k: Number(topK) || 4 }
      if (domain.trim()) payload.domain = domain.trim()
      const resp = await api.post('/ask', payload)
      setAnswer(resp.data?.answer || '')
      setSources(resp.data?.sources || [])
    } catch (e) {} finally {
      setAskLoading(false)
    }
  }

  const onSearch = async () => {
    if (!searchQ.trim()) {
      toast.info('Enter a query to search (feature scaffolded; backend /search not yet wired).')
      return
    }
    setSearchLoading(true)
    try {
      toast.info('Search is scaffolded in UI but not implemented in backend yet.')
    } finally {
      setSearchLoading(false)
    }
  }

  return (
    <div className="container-max py-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Modular Knowledge Assistant</h1>
        <p className="text-sm text-gray-600">Local UI • Vite + Tailwind + Axios</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Search / Domain Panel */}
        <section className="card">
          <PanelTitle>1) Domain & Search</PanelTitle>
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">Restrict retrieval to domain (collection name)</label>
            <input
              className="input"
              placeholder="e.g., en.wikipedia.org (optional)"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">Leave empty to search across all collections.</p>
          </div>

          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Search the web (UI scaffold)</label>
              <input
                className="input"
                placeholder="e.g., Transformers positional encoding"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
              />
            </div>
            <button className="btn-secondary" onClick={onSearch} disabled={searchLoading}>
              {searchLoading ? 'Searching…' : 'Search'}
            </button>
          </div>
        </section>

        {/* Ingest Panel */}
        <section className="card">
          <PanelTitle>2) Ingest URLs</PanelTitle>
          <label className="block text-sm font-medium text-gray-700 mb-1">Enter one URL per line (HTML or PDF)</label>
          <textarea
            className="textarea h-32"
            placeholder="https://en.wikipedia.org/wiki/Transformer_(machine_learning)\nhttps://arxiv.org/pdf/1706.03762.pdf"
            value={urlsText}
            onChange={(e) => setUrlsText(e.target.value)}
          />
          <div className="mt-3 flex gap-2">
            <button className="btn-primary" onClick={onIngest} disabled={ingestLoading}>
              {ingestLoading ? 'Ingesting…' : 'Ingest'}
            </button>
            <button className="btn-secondary" onClick={() => { setUrlsText(''); setIngestIds([]); }} disabled={ingestLoading}>
              Clear
            </button>
          </div>

          {ingestIds.length > 0 && (
            <div className="mt-3">
              <p className="text-sm text-gray-700">
                Stored chunk IDs: <span className="font-mono">{ingestIds.length}</span>
              </p>
            </div>
          )}
        </section>

        {/* Ask Panel */}
        <section className="card">
          <PanelTitle>3) Ask</PanelTitle>
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">Question</label>
            <input className="input" value={question} onChange={(e) => setQuestion(e.target.value)} />
          </div>
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">top_k</label>
            <input type="number" className="number" value={topK} min={1} max={10} onChange={(e) => setTopK(e.target.value)} />
          </div>
          <button className="btn-primary" onClick={onAsk} disabled={askLoading}>
            {askLoading ? 'Answering…' : 'Ask'}
          </button>

          {answer && (
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-1">Answer</h3>
              <p className="text-gray-800 whitespace-pre-wrap">{answer}</p>
              {sources?.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-sm font-semibold text-gray-900 mb-1">Sources</h4>
                  <ul className="list-disc pl-6 space-y-1 text-sm">
                    {sources.map((s, i) => (
                      <li key={i}>
                        {s.url ? <a href={s.url} target="_blank" className="text-blue-600 underline" rel="noreferrer">{s.url}</a> : 'Unknown URL'}
                        {s.snippet ? <div className="text-gray-600 mt-1">{s.snippet}</div> : null}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Stats Panel */}
        <section className="card">
          <PanelTitle>4) Stats</PanelTitle>
          <div className="text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">API Base:</span>
              <span className="font-mono">{import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}</span>
            </div>
            <div className="mt-2">
              <span className="text-gray-700">/health</span>
              <pre className="mt-1 bg-gray-50 border border-gray-200 rounded p-2 overflow-auto max-h-40 text-xs">
{`${
  health ? JSON.stringify(health, null, 2) : 'Loading…'
}`}
              </pre>
            </div>
          </div>
        </section>
      </div>

      <ToastContainer position="bottom-right" />
    </div>
  )
}
