const inverse = {parent:'child',child:'parent',adoptive_parent:'adoptive_child',adoptive_child:'adoptive_parent',step_parent:'step_child',step_child:'step_parent'}
const labels = {
 parent:[['Отец','Мать','Родитель'],['Father','Mother','Parent']], child:[['Сын','Дочь','Ребёнок'],['Son','Daughter','Child']],
 sibling:[['Родной брат','Родная сестра','Родственник'],['Brother','Sister','Relative']], half_sibling:[['Брат с одним общим родителем','Сестра с одним общим родителем','Родственник'],['Half-brother','Half-sister','Relative']],
 spouse:[['Супруг','Супруга','Партнёр'],['Husband','Wife','Partner']], partner:[['Партнёр','Партнёрша','Партнёр'],['Partner','Partner','Partner']], ex_spouse:[['Бывший супруг','Бывшая супруга','Бывший партнёр'],['Former husband','Former wife','Former partner']],
 adoptive_parent:[['Приёмный отец','Приёмная мать','Приёмный родитель'],['Adoptive father','Adoptive mother','Adoptive parent']], adoptive_child:[['Приёмный сын','Приёмная дочь','Приёмный ребёнок'],['Adopted son','Adopted daughter','Adopted child']],
 step_parent:[['Отчим','Мачеха','Неродной родитель'],['Stepfather','Stepmother','Stepparent']], step_child:[['Пасынок','Падчерица','Неродной ребёнок'],['Stepson','Stepdaughter','Stepchild']],
 'child,spouse':[['Зять','Невестка','Родственник по браку'],['Son-in-law','Daughter-in-law','In-law']],
 'parent,spouse':[['Отец','Мать','Родитель'],['Father','Mother','Parent']],
 'spouse,child':[['Пасынок','Падчерица','Неродной ребёнок'],['Stepson','Stepdaughter','Stepchild']],
 'parent,parent':[['Дедушка','Бабушка','Прародитель'],['Grandfather','Grandmother','Grandparent']],
 'child,child':[['Внук','Внучка','Потомок'],['Grandson','Granddaughter','Grandchild']],
 'parent,sibling':[['Дядя','Тётя','Родственник'],['Uncle','Aunt','Relative']],
 'parent,half_sibling':[['Дядя','Тётя','Родственник'],['Uncle','Aunt','Relative']],
 'sibling,child':[['Племянник','Племянница','Родственник'],['Nephew','Niece','Relative']],
 'half_sibling,child':[['Племянник','Племянница','Родственник'],['Nephew','Niece','Relative']],
 'parent,child':[['Брат','Сестра','Родственник'],['Brother','Sister','Relative']],
 'parent,sibling,child':[['Двоюродный брат','Двоюродная сестра','Родственник'],['Cousin','Cousin','Relative']],
 'parent,parent,parent':[['Прадедушка','Прабабушка','Предок'],['Great-grandfather','Great-grandmother','Ancestor']],
 'child,child,child':[['Правнук','Правнучка','Потомок'],['Great-grandson','Great-granddaughter','Descendant']],
}
export function personGender(node) { return node?.gender || node?.voice_gender || null }
export function kinshipName(path, node, lang='ru') {
 const gender=personGender(node), index=gender==='male'?0:gender==='female'?1:2
 return labels[path]?.[lang==='en'?1:0]?.[index] || (lang==='en'?'Relative':gender==='female'?'Родственница':'Родственник')
}
export function selectedKinshipLabels(graph, selectedId, lang='ru') {
 const nodes=new Map((graph?.nodes||[]).map(n=>[String(n.memorial_id),n])), adj=new Map([...nodes.keys()].map(id=>[id,[]]))
 for(const e of graph?.edges||[]) {
  const a=String(e.source), b=String(e.target), type=String(e.type).toLowerCase()
  if(!nodes.has(a)||!nodes.has(b)||type==='custom')continue
  adj.get(a).push({id:b,type}); adj.get(b).push({id:a,type:inverse[type]||type})
 }
 // Prefer blood relationships over a same-length route through a spouse.
 for(const list of adj.values())list.sort((a,b)=>Number(['spouse','partner','ex_spouse'].includes(a.type))-Number(['spouse','partner','ex_spouse'].includes(b.type)))
 const root=String(selectedId), seen=new Set([root]), queue=[{id:root,path:[],via:[]}], result={}
 while(queue.length) {
  const {id,path,via}=queue.shift()
  if(path.length>=6)continue
  for(const next of adj.get(id)||[]) {
   if(seen.has(next.id))continue
   seen.add(next.id);const route=[...path,next.type]
   const target=nodes.get(next.id), routeKey=route.join(',')
   result[next.id]=kinshipName(routeKey,target,lang)
   if (lang !== 'en' && ['spouse,sibling','spouse,half_sibling','spouse,parent','sibling,spouse','half_sibling,spouse'].includes(routeKey)) {
    const gender=personGender(target), middle=nodes.get(via[0]), middleFemale=personGender(middle)==='female'
    if(gender && personGender(middle)) {
     const kind=route[0]==='spouse' ? (route[1]==='parent' ? (gender==='female'?'Мать':'Отец') : (gender==='female'?'Сестра':'Брат')) : (gender==='female'?'Жена':'Муж')
     const of=route[0]==='spouse' ? (middleFemale?'супруги':'супруга') : (middleFemale?'сестры':'брата')
     result[next.id]=`${kind} ${of}`
    }
   }
   if(lang==='en' && ['spouse,sibling','spouse,half_sibling','sibling,spouse','half_sibling,spouse'].includes(routeKey))result[next.id]=personGender(target)==='female'?'Sister-in-law':personGender(target)==='male'?'Brother-in-law':'In-law'
   queue.push({id:next.id,path:route,via:[...via,next.id]})
  }
 }
 return result
}
