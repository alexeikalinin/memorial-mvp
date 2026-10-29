const kinds=[
 ['parent','Мать','Отец','Mother','Father'],['child','Дочь','Сын','Daughter','Son'],
 ['spouse','Супруга','Супруг','Wife','Husband'],['partner','Партнёрша','Партнёр','Female partner','Male partner'],['ex_spouse','Бывшая супруга','Бывший супруг','Former wife','Former husband'],
 ['sibling','Родная сестра','Родной брат','Sister','Brother'],['half_sibling','Сестра с одним общим родителем','Брат с одним общим родителем','Half-sister (one shared parent)','Half-brother (one shared parent)'],
 ['adoptive_parent','Приёмная мать','Приёмный отец','Adoptive mother','Adoptive father'],['adoptive_child','Приёмная дочь','Приёмный сын','Adopted daughter','Adopted son'],
 ['step_parent','Мачеха','Отчим','Stepmother','Stepfather'],['step_child','Падчерица','Пасынок','Stepdaughter','Stepson'],
]
export function relationshipChoices(lang='ru') {
 return [...kinds.flatMap(([type,female,male,enFemale,enMale])=>[
  {value:`${type}:female`,type,gender:'female',label:lang==='en'?enFemale:female},
  {value:`${type}:male`,type,gender:'male',label:lang==='en'?enMale:male},
 ]),{value:'custom',type:'custom',gender:null,label:lang==='en'?'Other (describe)':'Другая связь (указать)'}]
}
export function choiceValue(type,gender){return type==='custom'?'custom':gender&&type?`${type}:${gender}`:''}
export function choiceLabel(type,gender,lang){return relationshipChoices(lang).find(o=>o.value===choiceValue(type,gender))?.label || (lang==='en'?'Choose a relationship':'Выберите связь')}
// A relation choice must never silently change an existing person's recorded gender.
export async function prepareRelativeGender(api,id,gender,lang='ru'){
 if(!gender)return
 let person
 try{person=(await api.get(id)).data}catch(err){if([401,403].includes(err.response?.status))return;throw err}
 const known=person.gender||person.voice_gender
 if(known&&known!==gender){const error=new Error(lang==='en'?'This relationship conflicts with the relative’s recorded gender. Choose the matching relationship or correct their profile.':'Выбранная связь не соответствует полу в мемориале родственника. Выберите подходящую связь или уточните пол в его профиле.');error.relationshipExplanation=true;throw error}
 if(!known&&['owner','editor'].includes(person.current_user_role))await api.update(id,{gender})
}
