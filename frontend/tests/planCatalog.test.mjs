import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const plans = JSON.parse(readFileSync(new URL('../src/data/planCatalog.json', import.meta.url)))
const landing = readFileSync(new URL('../landing/index.html', import.meta.url), 'utf8')
test('approved annual catalogue agrees with both landing copies', () => {
  assert.equal(landing, readFileSync(new URL('../../landing/index.html', import.meta.url), 'utf8'))
  assert.deepEqual(plans.map(p => p.price), [40, 80, 140])
  for (const plan of plans) {
    const key = plan.name.toLowerCase().replaceAll(' ', '_')
    for (const [field, expected] of Object.entries({ pages: `Up to ${plan.pages} memorials`, storage: `${plan.storage} GB per account`, text: `${plan.text} text AI replies per month`, clones: `Up to ${plan.clones} voice clones`, voice: `About ${plan.voice} voice minutes per month` })) {
      assert.ok(landing.includes(`"pricing.${key}_${field}": "${expected}"`), `${key}.${field}`)
    }
    assert.ok(landing.includes(`${key}:"${plan.name} · $${plan.price}"`))
  }
})
