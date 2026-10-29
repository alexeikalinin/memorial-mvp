import {relationshipChoices,choiceValue} from '../utils/relationshipChoices'
import {useLanguage} from '../contexts/LanguageContext'
export default function RelationshipTypeSelect({id,type,gender,onChange,disabled=false}){
 const {lang}=useLanguage(),options=relationshipChoices(lang)
 return <><select id={id} value={choiceValue(type,gender)} disabled={disabled} required onChange={e=>onChange(options.find(o=>o.value===e.target.value))}>
 <option value="" disabled>{lang==='en'?'Choose a relationship':'Выберите связь'}</option>
 {options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}
 </select><p className="form-hint">{lang==='en'?'Half-siblings share only one parent. Cousins are children of your parents’ siblings; cousin relationships are calculated through the parents.':'У брата или сестры с одним общим родителем общая только мать или только отец. Двоюродные — дети братьев или сестёр родителей; такое родство рассчитывается через связи родителей.'}</p></>
}
