import logo from '../assets/brand-flame.svg'
import logoStatic from '../assets/brand-flame-static.svg'
import logoLight from '../assets/brand-flame-light.svg'
import logoLightStatic from '../assets/brand-flame-light-static.svg'
import square from '../assets/brand-square.svg'
import squareStatic from '../assets/brand-square-static.svg'
import squareLight from '../assets/brand-square-light.svg'
import squareLightStatic from '../assets/brand-square-light-static.svg'
import lantern from '../assets/memorial-lantern.svg'
import lanternStatic from '../assets/memorial-lantern-static.svg'
import './BrandVisual.css'

export default function BrandVisual({ kind = 'logo', className = '', tone = 'dark', format = 'horizontal' }) {
  const isLogo = kind === 'logo'
  const motion = format === 'square' ? (tone === 'light' ? squareLight : square) : (tone === 'light' ? logoLight : logo)
  const still = format === 'square' ? (tone === 'light' ? squareLightStatic : squareStatic) : (tone === 'light' ? logoLightStatic : logoStatic)
  return <span className={`brand-visual ${className}`}>
    <img className="brand-motion" src={isLogo ? motion : lantern} alt={isLogo ? 'vspomin.ai' : ''} />
    <img className="brand-still" src={isLogo ? still : lanternStatic} alt={isLogo ? 'vspomin.ai' : ''} />
  </span>
}
