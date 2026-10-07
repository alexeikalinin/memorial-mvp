import BrandVisual from '../components/BrandVisual'
import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { memorialsAPI } from '../api/client'
import { useLanguage } from '../contexts/LanguageContext'
import ApiMediaImage from '../components/ApiMediaImage'
import CreateMemorialHeroButton from '../components/CreateMemorialHeroButton'
import CreateMemorialTutorial from '../components/CreateMemorialTutorial'
import { isDeceasedMemorial } from '../utils/memorialStatus'
import './Home.css'

async function waitForHeroFonts() {
  if (typeof document === 'undefined' || !document.fonts?.load) {
    return
  }
  const loads = [
    document.fonts.load("300 4rem 'Cormorant Garamond'"),
    document.fonts.load("italic 400 4rem 'Cormorant Garamond'"),
    document.fonts.load("400 1.1rem 'Inter'"),
    document.fonts.load("500 1.1rem 'Inter'"),
    document.fonts.load("600 0.75rem 'Inter'"),
  ]
  const timeout = new Promise((resolve) => {
    setTimeout(resolve, 3200)
  })
  try {
    await Promise.race([Promise.all(loads), timeout])
  } catch {
    /* ignore */
  }
}

function Home() {
  const [memorials, setMemorials] = useState([])
  const [loading, setLoading] = useState(true)
  const [heroFontsReady, setHeroFontsReady] = useState(false)
  const [showTutorial, setShowTutorial] = useState(false)
  const { t, lang } = useLanguage()
  const homeContentRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    waitForHeroFonts().then(() => {
      if (!cancelled) setHeroFontsReady(true)
    })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    memorialsAPI
      .list(lang)
      .then((res) => setMemorials(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error('Error loading memorials:', err)
        setMemorials([])
      })
      .finally(() => setLoading(false))
  }, [lang])

  const nonDemoMemorials = memorials.filter((m) => !m.is_demo_seed)
  const isFirstTimeUser = !loading && nonDemoMemorials.length === 0

  const showMemorialsContent = true
  const showDemoRevealStrip = false

  const renderMemorialCard = (memorial, i) => {
    const deceased = isDeceasedMemorial(memorial)
    return (
      <div
        key={memorial.id}
        className={`memorial-card memorial-card--${deceased ? 'deceased' : 'living'}`}
        style={{ animationDelay: `${i * 0.07}s` }}
      >
        <Link to={`/memorials/${memorial.id}`} className="memorial-card-link">
          <div className="card-cover-wrap">
            <div
              className={`card-cover ${deceased ? 'card-cover--deceased' : 'card-cover--living'}`}
            >
              {memorial.cover_photo_url || memorial.cover_photo_id ? (
                <ApiMediaImage
                  portrait={{ memorialId: memorial.id, kind: 'cover', version: memorial.updated_at }}
                  mediaId={memorial.cover_photo_id}
                  thumbnail={memorial.cover_photo_url ? null : 'large'}
                  alt={memorial.name}
                  className="card-cover-img"
                  loading={i < 4 ? 'eager' : 'lazy'}
                  eager={i < 4}
                  fallback={<div className="card-no-cover"><span>🕯</span></div>}
                />
              ) : (
                <div className="card-no-cover"><span>🕯</span></div>
              )}
            </div>
            {deceased && (
              <span className="card-cover-candle" aria-hidden="true" title={t('home.memorial_candle_title')}>
                🕯
              </span>
            )}
          </div>

          <div className="card-body">
            <h3 className="card-name">{memorial.name}</h3>
            {memorial.description && (
              <p className="card-description">{memorial.description}</p>
            )}
            <div className="card-meta">
              {(memorial.birth_date || memorial.death_date) ? (
                <span className="card-dates">
                  {memorial.birth_date && new Date(memorial.birth_date).getFullYear()}
                  {memorial.birth_date && memorial.death_date && ' — '}
                  {memorial.death_date && new Date(memorial.death_date).getFullYear()}
                </span>
              ) : (
                <span />
              )}
              <span className="card-counts">
                {t('home.card_counts', {
                  memories: memorial.memories_count,
                  media: memorial.media_count,
                })}
              </span>
            </div>
          </div>
        </Link>
        <div className="memorial-card-actions">
          <Link
            to={`/memorials/${memorial.id}?tab=memories`}
            className="btn btn-card-memories"
            onClick={(e) => e.stopPropagation()}
          >
            {t('home.add_memories')}
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className={`home${showDemoRevealStrip ? ' home--demo-first-screen' : ''}`}>
      {/* ── Hero ── */}
      <section className={`hero${showDemoRevealStrip ? ' hero--with-demo-reveal' : ''}`}>
        <div className="hero-inner">
          <div className={`hero-text${heroFontsReady ? ' hero-text--fonts-ready' : ''}`}>
            <div className="hero-brand" aria-label="vspomin.ai">
              <BrandVisual className="hero-brand-lockup" />
            </div>
            <h1 className="hero-tagline">
              <span>{t('home.tagline_plain')}</span><br />
              <em>{t('home.tagline_em')}</em>
            </h1>
            <p className="hero-subtitle">{t('home.subtitle')}</p>
            <div className="hero-cta">
              <CreateMemorialHeroButton
                label={t('home.cta')}
                onClick={(e) => {
                  if (isFirstTimeUser) {
                    e.preventDefault()
                    setShowTutorial(true)
                  }
                }}
              />
            </div>
          </div>

          <div className="hero-visual hero-album-scene">
            <img className="hero-album-image" src={`${import.meta.env.BASE_URL}preview-albums/album-1.png`} alt={lang === 'ru' ? 'Семейный альбом памяти с вымышленными фотографиями' : 'Family memory album with fictional photographs'} />
            <BrandVisual kind="lantern" className="hero-album-lantern" />
            <div className="hero-album-caption">
              <blockquote>{lang === 'ru' ? '«Я всегда буду рядом' : '“I will always be close'}<br />{lang === 'ru' ? 'в ваших воспоминаниях»' : 'in your memories”'}</blockquote>
              <div className="hero-album-voice">{lang === 'ru' ? 'Его голос. Его история.' : 'His voice. His story.'}</div>
              <div className="hero-album-wave" aria-hidden="true">{[7,14,23,12,29,18,34,22,13,25,17,30,20,11,24,16,9,5].map((height, i) => <i key={i} style={{ height }} />)}</div>
            </div>
          </div>
        </div>

        <div className="hero-scroll-cue" aria-hidden="true">
          <div className="scroll-line" />
        </div>
      </section>

      {/* ── Pricing ── */}
      <section className="pricing-section" id="pricing">
        <div className="pricing-inner">
          <h2 className="pricing-title">{t('home.pricing_title')}</h2>
          <p className="pricing-subtitle">{t('home.pricing_subtitle')}</p>
          <div className="pricing-grid">
            {(t('home.pricing_plans') || []).map((plan) => (
              <div
                key={plan.id}
                className={`pricing-card${plan.highlight ? ' pricing-card--highlight' : ''}`}
              >
                {plan.highlight && (
                  <span className="pricing-popular">{t('home.pricing_popular')}</span>
                )}
                {plan.badge && !plan.highlight && (
                  <span className="pricing-badge">{plan.badge}</span>
                )}
                <div className="pricing-card-header">
                  <span className="pricing-plan-name">{plan.name}</span>
                  <span className="pricing-plan-desc">{plan.desc}</span>
                </div>
                <div className="pricing-price">
                  <span className="pricing-amount">{plan.price}</span>
                  {plan.period && <span className="pricing-period">{plan.period}</span>}
                </div>
                {plan.annual && (
                  <div className="pricing-annual">{plan.annual}</div>
                )}
                <ul className="pricing-features">
                  {plan.features.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
                <a
                  href="/memorials/new"
                  className={`btn pricing-plan-cta${plan.highlight ? ' btn-primary' : ' btn-outline'}`}
                >
                  {plan.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Memorials List (скрыт на первом экране, если в списке только демо-сиды) ── */}
      {showMemorialsContent && (
        <div ref={homeContentRef} id="home-memorials-panel" className="home-content">
          <div className="section-header">
            <h2 className="section-title">{t('home.section_title')}</h2>
            {!loading && memorials.length > 0 && (
              <span className="section-count">
                {t('home.count_label', { n: nonDemoMemorials.length })}
              </span>
            )}
          </div>

          {loading ? (
            <div className="loading" />
          ) : (
            <>
              <div className="memorials-grid">
                {nonDemoMemorials.length === 0 ? (
                  <div className="home-empty">
                    <div className="home-empty-icon">🕯</div>
                    <p>{t('home.empty')}</p>
                    <Link
                      to="/memorials/new"
                      className="btn btn-primary"
                      onClick={(e) => {
                        if (isFirstTimeUser) {
                          e.preventDefault()
                          setShowTutorial(true)
                        }
                      }}
                    >
                      {t('home.create_first')}
                    </Link>
                    <div className="home-demo-explore-link">
                      <Link to="/app/demo">{t('home.explore_demo')}</Link>
                    </div>
                  </div>
                ) : (
                  nonDemoMemorials.map((memorial, i) => renderMemorialCard(memorial, i))
                )}
              </div>

              {nonDemoMemorials.length > 0 && (
                <div className="home-demo-explore-link">
                  <Link to="/app/demo">{t('home.explore_demo')}</Link>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {showTutorial && (
        <CreateMemorialTutorial onClose={() => setShowTutorial(false)} />
      )}
    </div>
  )
}

export default Home
