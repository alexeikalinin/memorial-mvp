import test from 'node:test'
import assert from 'node:assert/strict'
import {selectedKinshipLabels,kinshipName} from '../src/utils/familyTreeKinship.js'
const graph={nodes:[{memorial_id:1,gender:'female'},{memorial_id:2,gender:'male'},{memorial_id:3,gender:'female'},{memorial_id:4,gender:'male'},{memorial_id:5,gender:'male'}],edges:[{source:1,target:2,type:'spouse'},{source:1,target:3,type:'sibling'},{source:2,target:4,type:'sibling'},{source:5,target:1,type:'parent'},{source:5,target:2,type:'parent'}]}
test('selected son sees mother, father, maternal aunt and paternal uncle from inverse edges',()=>{
 const labels=selectedKinshipLabels(graph,5)
 assert.deepEqual(labels,{'1':'Мать','2':'Отец','3':'Тётя','4':'Дядя'})
 assert.equal(selectedKinshipLabels(graph,1)[3],'Родная сестра')
 assert.equal(selectedKinshipLabels(graph,2)[4],'Родной брат')
 assert.equal(selectedKinshipLabels(graph,1)[5],'Сын')
 assert.equal(selectedKinshipLabels(graph,3)[5],'Племянник')
})
test('sex-specific labels preserve half/adoptive/step distinctions and English',()=>{
 assert.equal(kinshipName('half_sibling',{gender:'female'}),'Сестра с одним общим родителем')
 assert.equal(kinshipName('adoptive_parent',{gender:'female'}),'Приёмная мать')
 assert.equal(kinshipName('step_parent',{gender:'male'}),'Отчим')
 assert.equal(selectedKinshipLabels(graph,5,'en')[3],'Aunt')
 assert.equal(kinshipName('sibling',{}),'Родственник')
 assert.equal(kinshipName('sibling',{gender:'female',voice_gender:'male'}),'Родная сестра')
})
test('case, duplicate inverse records, cycles and unrelated orphan nodes are safe',()=>{
 const result=selectedKinshipLabels({...graph,edges:[...graph.edges,{source:1,target:5,type:'CHILD'},{source:9,target:5,type:'parent'}]},5)
 assert.equal(result[1],'Мать');assert.equal(result[9],undefined);assert.equal(result[5],undefined)
})

test('a parent’s spouse defaults to mother/father; explicit step links keep their meaning',()=>{
 const graph={nodes:[{memorial_id:1},{memorial_id:2,gender:'male'},{memorial_id:3,gender:'female'}],edges:[{source:1,target:2,type:'parent'},{source:2,target:3,type:'spouse'}]}
 assert.equal(selectedKinshipLabels(graph,1)[3],'Мать')
 graph.edges.push({source:1,target:3,type:'step_parent'})
 assert.equal(selectedKinshipLabels(graph,1)[3],'Мачеха')
})
