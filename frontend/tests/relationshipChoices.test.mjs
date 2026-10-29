import test from 'node:test'
import assert from 'node:assert/strict'
import {relationshipChoices,choiceValue,choiceLabel,prepareRelativeGender} from '../src/utils/relationshipChoices.js'
test('one catalog has explicit mother/father and all canonical relationship types without generic parent options',()=>{
 const list=relationshipChoices()
 assert.equal(new Set(list.map(o=>o.value)).size,list.length)
 assert.equal(choiceLabel('parent','female'),'Мать');assert.equal(choiceLabel('parent','male'),'Отец')
 assert.ok(!list.some(o=>o.label==='Родитель'||o.label.includes('/')))
 assert.deepEqual(new Set(list.map(o=>o.type)),new Set(['parent','child','spouse','partner','ex_spouse','sibling','half_sibling','adoptive_parent','adoptive_child','step_parent','step_child','custom']))
 assert.equal(choiceValue('parent',null),'');assert.equal(choiceValue('custom',null),'custom')
 assert.match(choiceLabel('half_sibling','male'),/одним общим родителем/)
 assert.equal(choiceLabel('parent','female','en'),'Mother')
})
test('gendered choice cannot overwrite a known gender or silently change avatar voice',async()=>{
 let writes=[];const api={get:async()=>({data:{gender:'female',voice_gender:'male',current_user_role:'owner'}}),update:async(...args)=>writes.push(args)}
 await assert.rejects(prepareRelativeGender(api,1,'male'),/не соответствует/)
 await prepareRelativeGender(api,1,'female');assert.deepEqual(writes,[])
 api.get=async()=>({data:{current_user_role:'editor'}})
 await prepareRelativeGender(api,1,'female');assert.deepEqual(writes,[[1,{gender:'female'}]])
})
test('choosing a relationship to a private person does not bypass access control',async()=>{
 let writes=0;const api={get:async()=>{throw{response:{status:403}}},update:async()=>writes++}
 await prepareRelativeGender(api,1,'female');assert.equal(writes,0)
 api.get=async()=>({data:{current_user_role:'viewer'}})
 await prepareRelativeGender(api,1,'female');assert.equal(writes,0)
})
