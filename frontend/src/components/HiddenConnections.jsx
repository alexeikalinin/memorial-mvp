import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { familyAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import './HiddenConnections.css'

export default function HiddenConnections({ memorialId }) {
  const navigate = useNavigate()
  const { t } = useLanguage()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(null)

  const hopLabels = t('hiddenConnections.hop_labels')

  const hopLabel = (hops) => hopLabels[hops] || t('hiddenConnections.hop_label_fallback', { hops })

  const discover = async () => {
    setLoading(true)
    try {
      const res = await familyAPI.getHiddenConnections(memorialId)
      setResult(res.data)
    } catch (err) {
      console.error('Hidden connections error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="hidden-connections">
      <div className="hc-header">
        <h3>{t('hiddenConnections.title')}</h3>
        <p className="hc-hint">
          {t('hiddenConnections.hint')}
        </p>
        <button
          className="btn btn-secondary hc-discover-btn"
          onClick={discover}
          disabled={loading}
        >
          {loading ? t('hiddenConnections.searching') : result ? t('hiddenConnections.refresh') : t('hiddenConnections.discover')}
        </button>
      </div>

      {result && (
        <div className="hc-results">
          {result.hidden.length === 0 ? (
            <div className="hc-empty">
              {t('hiddenConnections.empty')}
            </div>
          ) : (
            <>
              <div className="hc-count">
                {t('hiddenConnections.found_prefix')} <strong>{result.hidden.length}</strong>{' '}
                {result.hidden.length === 1 ? t('hiddenConnections.connection_singular') : t('hiddenConnections.connection_plural')}{' '}
                {t('hiddenConnections.through')}{' '}
                {result.hidden.length > 0 ? `${result.hidden[0].hops}–${result.hidden[result.hidden.length - 1].hops}` : ''} {t('hiddenConnections.generations')}
              </div>

              <div className="hc-list">
                {result.hidden.map((conn) => (
                  <div
                    key={conn.target_memorial_id}
                    className={`hc-item hc-item--hops-${Math.min(conn.hops, 5)}`}
                  >
                    <div
                      className="hc-item-header"
                      onClick={() =>
                        setExpanded(
                          expanded === conn.target_memorial_id ? null : conn.target_memorial_id
                        )
                      }
                    >
                      <div className="hc-item-left">
                        <span className="hc-badge">{hopLabel(conn.hops)}</span>
                        <span
                          className="hc-name"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/memorials/${conn.target_memorial_id}`)
                          }}
                        >
                          {conn.target_name}
                        </span>
                      </div>
                      <span className="hc-toggle">
                        {expanded === conn.target_memorial_id ? '▲' : '▼'}
                      </span>
                    </div>

                    {expanded === conn.target_memorial_id && (
                      <div className="hc-path">
                        <div className="hc-path-label">{t('hiddenConnections.chain_label')}</div>
                        <div className="hc-chain">
                          {conn.path.map((step, i) => (
                            <span key={i} className="hc-chain-step">
                              <span
                                className="hc-chain-name"
                                onClick={() => navigate(`/memorials/${step.memorial_id}`)}
                              >
                                {step.name}
                              </span>
                              <span className="hc-chain-rel">
                                → ({step.relationship_label}) →
                              </span>
                            </span>
                          ))}
                          <span
                            className="hc-chain-name hc-chain-name--target"
                            onClick={() => navigate(`/memorials/${conn.target_memorial_id}`)}
                          >
                            {conn.target_name}
                          </span>
                        </div>
                        <div className="hc-summary">{conn.connection_summary}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
