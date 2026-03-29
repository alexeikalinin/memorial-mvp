/**
 * Жив / умер — только по полям API (death_date / death_year).
 * Не зависит от языка интерфейса.
 */
export function isDeceasedMemorial({ death_date: deathDate, death_year: deathYear } = {}) {
  if (deathDate != null && deathDate !== '') return true
  if (deathYear != null && deathYear !== '') return true
  return false
}
