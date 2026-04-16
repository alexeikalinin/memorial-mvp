import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import CandleIcon from './CandleIcon'
import './CreateMemorialHeroButton.css'

const MotionLink = motion.create(Link)

export default function CreateMemorialHeroButton({ to = '/memorials/new', label }) {
  const [hovered, setHovered] = useState(false)

  return (
    <MotionLink
      to={to}
      className="create-memorial-hero-btn"
      whileHover={{ scale: 1.03 }}
      transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
    >
      <span className="create-memorial-hero-btn__label">{label}</span>

      <div
        className="create-memorial-hero-btn__candle-main"
        aria-hidden
      >
        <CandleIcon className="create-memorial-hero-btn__candle-main-svg" />
      </div>

      <div className="create-memorial-hero-btn__candles" aria-hidden>
        <motion.div
          className="create-memorial-hero-btn__candle create-memorial-hero-btn__candle--1"
          initial={false}
          animate={
            hovered
              ? { opacity: [0, 0.7, 1], scale: [0.6, 1.05, 1], y: 0 }
              : { opacity: 0, scale: 0.6, y: 20 }
          }
          transition={{ duration: 0.8, delay: hovered ? 0.1 : 0 }}
        >
          <CandleIcon className="create-memorial-hero-btn__candle-svg create-memorial-hero-btn__candle-svg--amber" />
        </motion.div>

        <motion.div
          className="create-memorial-hero-btn__candle create-memorial-hero-btn__candle--2"
          initial={false}
          animate={
            hovered
              ? { opacity: [0, 0.85, 1], scale: [0.5, 1.1, 1] }
              : { opacity: 0, scale: 0.5 }
          }
          transition={{ duration: 0.7, delay: hovered ? 0.25 : 0 }}
        >
          <CandleIcon className="create-memorial-hero-btn__candle-svg create-memorial-hero-btn__candle-svg--bright" />
        </motion.div>

        <motion.div
          className="create-memorial-hero-btn__candle create-memorial-hero-btn__candle--3"
          initial={false}
          animate={
            hovered
              ? { opacity: [0, 0.6, 1], scale: [0.7, 1, 1], y: 0 }
              : { opacity: 0, scale: 0.7, y: 15 }
          }
          transition={{ duration: 0.9, delay: hovered ? 0.4 : 0 }}
        >
          <CandleIcon className="create-memorial-hero-btn__candle-svg create-memorial-hero-btn__candle-svg--orange" />
        </motion.div>
      </div>

      <motion.div
        className="create-memorial-hero-btn__glow"
        initial={false}
        animate={{ opacity: hovered ? 1 : 0 }}
        transition={{ duration: 0.6 }}
      />
    </MotionLink>
  )
}
