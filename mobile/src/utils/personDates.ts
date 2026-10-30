export function personDates(birth: string, death: string) {
  for (const value of [birth, death]) {
    if (value && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(Date.parse(value)) || new Date(value).toISOString().slice(0,10) !== value)) throw Error("Укажите существующую дату в формате ГГГГ-ММ-ДД.");
  }
  if (birth && death && birth > death) throw Error("Дата ухода не может быть раньше даты рождения.");
  return {birth_date:birth ? `${birth}T00:00:00` : null, death_date:death ? `${death}T00:00:00` : null};
}

export function fullLifeDates(person: {birth_date?: string | null; death_date?: string | null}) {
 return [person.birth_date,person.death_date].filter(Boolean).map(value=>{const match=value!.match(/^(\d{4})-(\d{2})-(\d{2})/);return match?`${match[3]}.${match[2]}.${match[1]}`:value}).join(' — ');
}
