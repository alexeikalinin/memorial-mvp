// Read the calendar date directly: UTC offsets must not change a person's dates.
export function fullMemorialDate(value) {
 if (!value) return null
 const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/)
 return match ? `${match[3]}.${match[2]}.${match[1]}` : String(value)
}
