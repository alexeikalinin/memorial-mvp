import { test } from 'node:test';
import assert from 'node:assert/strict';
import { personDates } from '../src/utils/personDates';
test('calendar dates preserve leap days and allow clearing missing dates',()=>{
 assert.deepEqual(personDates('2000-02-29',''),{birth_date:'2000-02-29T00:00:00',death_date:null});
 assert.deepEqual(personDates('',''),{birth_date:null,death_date:null});
});
test('impossible dates and reversed life dates fail before saving',()=>{
 for(const date of ['2001-02-29','1961-04-31','1961-13-01','17.05.1961'])assert.throws(()=>personDates(date,''));
 assert.throws(()=>personDates('2000-01-02','2000-01-01'));
});
