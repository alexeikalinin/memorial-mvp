export function memorialName(person) {
 const name=person?.name || ''
 const maiden=person?.maiden_name?.trim()
 return maiden && (person.gender || person.voice_gender)!=='male' ? `${name} (${maiden})` : name
}
export function matchesMemorial(person,query) {
 const text=[person.name,person.maiden_name].filter(Boolean).join(' ').toLocaleLowerCase().replaceAll('ё','е')
 return query.toLocaleLowerCase().replaceAll('ё','е').trim().split(/\s+/).every(word=>text.includes(word))
}
