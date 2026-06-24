import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { memorialsAPI } from '../api/client'
import ApiMediaImage from '../components/ApiMediaImage'
import DemoTutorial from '../components/DemoTutorial'
import { useLanguage } from '../contexts/LanguageContext'
import './DemoPage.css'

const TUTORIAL_KEY = 'demo_tutorial_v1'

const FAMILY_KEYS = ['Kelly', 'Anderson', 'Chang', 'Rossi']
const FAMILY_COLORS = {
  Kelly: '#3D6B4F',
  Anderson: '#4A5D7A',
  Chang: '#7A4A3D',
  Rossi: '#5D4A7A',
}

function detectFamily(name) {
  for (const key of FAMILY_KEYS) {
    if (name.includes(key)) return key
  }
  return null
}

export default function DemoPage() {
  const { t } = useLanguage()
  const families = t('demoPage.families')
  const FAMILIES = FAMILY_KEYS.map(key => ({ key, color: FAMILY_COLORS[key], ...families[key] }))

  const [memorials, setMemorials] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [tutorialStep, setTutorialStep] = useState(() => {
    try {
      const saved = localStorage.getItem(TUTORIAL_KEY)
      if (saved === 'done') return null
      return saved ? parseInt(saved, 10) : 1
    } catch { return 1 }
  })

  const skipTutorial = () => {
    try { localStorage.setItem(TUTORIAL_KEY, 'done') } catch {}
    setTutorialStep(null)
  }

  const advanceTutorial = () => {
    const next = (tutorialStep || 0) + 1
    try { localStorage.setItem(TUTORIAL_KEY, next > 2 ? 'done' : String(next)) } catch {}
    setTutorialStep(next <= 2 ? next : null)
  }

  useEffect(() => {
    memorialsAPI.listDemo()
      .then(r => setMemorials(Array.isArray(r.data) ? r.data : []))
      .catch(() => setMemorials([]))
      .finally(() => setLoading(false))
  }, [])

  const byFamily = {}
  for (const f of FAMILIES) byFamily[f.key] = []
  for (const m of memorials) {
    const key = detectFamily(m.name)
    if (key) byFamily[key].push(m)
  }

  const activeFamilyDef = FAMILIES.find(f => f.key === selected)
  const activeMembers = selected ? byFamily[selected] : []

  return (
    <div className="demo-page">
      {/* ── Tutorial overlays ── */}
      {tutorialStep === 1 && (
        <DemoTutorial step={1} type="overlay" onNext={advanceTutorial} onSkip={skipTutorial} />
      )}

      {/* ── Header ── */}
      <div className="demo-header">
        <h1 className="demo-title">{t('demoPage.title')}</h1>
        <p className="demo-subtitle">
          {t('demoPage.subtitle')}
        </p>
        <div className="demo-cta-row">
          <Link to="/register" className="btn-demo-cta">{t('demoPage.create_cta')}</Link>
          <Link to="/login" className="btn-demo-secondary">{t('demoPage.signin')}</Link>
        </div>
      </div>

      {/* ── Family cards ── */}
      {!selected && (
        <div className="demo-families">
          {FAMILIES.map(f => {
            const members = byFamily[f.key] || []
            const count = members.length
            const p = members.find(m => m.name.includes(f.patriarch.split(' ')[0]))
            return (
              <button
                key={f.key}
                className="demo-family-card"
                style={{ '--family-color': f.color }}
                onClick={() => { setSelected(f.key); if (tutorialStep === 1) advanceTutorial() }}
              >
                <div className="demo-family-cover">
                  {p?.cover_photo_id ? (
                    <ApiMediaImage
                      mediaId={p.cover_photo_id}
                      thumbnail="medium"
                      alt={p.name}
                      className="demo-family-img"
                      fallback={<div className="demo-family-placeholder">🕯</div>}
                    />
                  ) : (
                    <div className="demo-family-placeholder">🕯</div>
                  )}
                  <div className="demo-family-overlay" />
                </div>
                <div className="demo-family-body">
                  <div className="demo-family-label">{f.label}</div>
                  <div className="demo-family-subtitle">{f.subtitle}</div>
                  <p className="demo-family-desc">{f.description}</p>
                  {!loading && <div className="demo-family-count">{t('demoPage.memorials_count', { count })}</div>}
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* ── Family member list ── */}
      {selected && activeFamilyDef && (
        <div className="demo-members">
          <div className="demo-members-header">
            <button className="btn-back" onClick={() => setSelected(null)}>{t('demoPage.all_families')}</button>
            <h2 className="demo-members-title">{activeFamilyDef.label}</h2>
            <span className="demo-members-subtitle">{activeFamilyDef.subtitle}</span>
          </div>
          {tutorialStep === 2 && (
            <DemoTutorial step={2} type="hint" onNext={advanceTutorial} onSkip={skipTutorial} />
          )}

          {loading ? (
            <div className="demo-loading">{t('demoPage.loading')}</div>
          ) : (
            <div className="demo-members-grid">
              {activeMembers
                .sort((a, b) => {
                  const ay = a.birth_date ? new Date(a.birth_date).getFullYear() : 9999
                  const by2 = b.birth_date ? new Date(b.birth_date).getFullYear() : 9999
                  return ay - by2
                })
                .map(m => {
                  const birthYear = m.birth_date ? new Date(m.birth_date).getFullYear() : null
                  const deathYear = m.death_date ? new Date(m.death_date).getFullYear() : null
                  return (
                    <Link key={m.id} to={(() => { try { return localStorage.getItem(TUTORIAL_KEY) !== 'done' ? `/m/${m.id}?demo_step=3` : `/m/${m.id}` } catch { return `/m/${m.id}` } })()} className="demo-member-card">
                      <div className="demo-member-cover">
                        {m.cover_photo_id ? (
                          <ApiMediaImage
                            mediaId={m.cover_photo_id}
                            thumbnail="small"
                            alt={m.name}
                            className="demo-member-img"
                            fallback={<div className="demo-member-placeholder">🕯</div>}
                          />
                        ) : (
                          <div className="demo-member-placeholder">🕯</div>
                        )}
                      </div>
                      <div className="demo-member-info">
                        <div className="demo-member-name">{m.name}</div>
                        {(birthYear || deathYear) && (
                          <div className="demo-member-years">
                            {birthYear}
                            {birthYear && deathYear ? ' — ' : ''}
                            {deathYear || (birthYear ? t('demoPage.alive_suffix') : '')}
                          </div>
                        )}
                        {m.memories_count > 0 && (
                          <div className="demo-member-count">{t('demoPage.memories_count', { count: m.memories_count })}</div>
                        )}
                      </div>
                    </Link>
                  )
                })}
            </div>
          )}
        </div>
      )}

      {/* ── Bottom CTA ── */}
      <div className="demo-bottom-cta">
        <p>{t('demoPage.bottom_cta_text')}</p>
        <Link to="/register" className="btn-demo-cta">{t('demoPage.bottom_cta_btn')}</Link>
      </div>
    </div>
  )
}
