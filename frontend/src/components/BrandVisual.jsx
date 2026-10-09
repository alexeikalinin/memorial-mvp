import logo from '../assets/brand-flame.svg'
import logoStatic from '../assets/brand-flame-static.svg'
import logoLight from '../assets/brand-flame-light.svg'
import logoLightStatic from '../assets/brand-flame-light-static.svg'
import lantern from '../assets/memorial-lantern.svg'
import lanternStatic from '../assets/memorial-lantern-static.svg'
import './BrandVisual.css'

export default function BrandVisual({ kind = 'logo', className = '', tone = 'dark' }) {
  const isLogo = kind === 'logo'
  return <span className={`brand-visual ${className}`}>
    <img className="brand-motion" src={isLogo ? (tone === 'light' ? logoLight : logo) : lantern} alt={isLogo ? 'vspomin.ai' : ''} />
    <img className="brand-still" src={isLogo ? (tone === 'light' ? logoLightStatic : logoStatic) : lanternStatic} alt={isLogo ? 'vspomin.ai' : ''} />
  </span>
}
