import test from 'node:test'
import assert from 'node:assert/strict'
import {surnameOf,buildSurnameClusterStyles} from '../src/utils/familyTreeGenerationLayout.js'
test('Russian surname-first names do not produce given names or patronymics in the legend',()=>{
 assert.equal(surnameOf('Калинин Николай Иванович'),'Калинин');assert.equal(surnameOf('Бахар Инна'),'Бахар');assert.equal(surnameOf('Сачко Александр Антонович'),'Сачко');assert.equal(surnameOf('Калинина Светлана (Бахар)'),'Калинина');assert.equal(surnameOf('James Kelly'),'Kelly')
 const nodes=[{memorial_id:1,name:'Бахар Инна'},{memorial_id:2,name:'Бахар Михаил'}]
 const a=buildSurnameClusterStyles(nodes),b=buildSurnameClusterStyles([...nodes,{memorial_id:3,name:'Калинин Николай Иванович'}])
 assert.equal(a.memorialClusterStyle[1].borderColor,b.memorialClusterStyle[1].borderColor)
 assert.deepEqual(a.clusterLegend.map(c=>c.key),['Бахар'])
})
