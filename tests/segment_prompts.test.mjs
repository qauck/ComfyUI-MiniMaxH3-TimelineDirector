import assert from 'node:assert/strict';
import {presetPromptSlots,importedSegmentPrompts} from '../js/segment_prompts.mjs';

const segment=(prompt,extra={})=>({startFrame:0,endFrame:120,prompt,images:[],audios:[],...extra});

// A preset slot is every preset segment entry, empty prompt included: the empty
// value is an explicit clearing, not a missing entry.
assert.deepEqual(presetPromptSlots({count:2,segments:[{prompt:'First'},{prompt:''}]}),['First','']);
// A declared count can never describe entries the preset does not carry.
assert.deepEqual(presetPromptSlots({count:6,segments:[{prompt:'One'},{prompt:'Two'}]}),['One','Two']);
assert.deepEqual(presetPromptSlots({segments:[{prompt:'Only'}]}),['Only']);
// A preset that declares fewer segments than its list holds is read as declared.
assert.deepEqual(presetPromptSlots({count:1,segments:[{prompt:'Kept'},{prompt:'Beyond the count'}]}),['Kept']);
// Missing or malformed prompt text is still a slot.
assert.deepEqual(presetPromptSlots({count:3,segments:[{startFrame:0},null,{prompt:'Third'}]}),['','','Third']);
assert.deepEqual(presetPromptSlots(undefined),[]);
assert.deepEqual(presetPromptSlots({count:2}),[]);

// More preset prompts than the planner has segments: keep the planner's count
// and ignore the extra prompts.
let current=[segment('Local one'),segment('Local two')];
let result=importedSegmentPrompts(current,{count:4,segments:[
  {prompt:'Preset one'},{prompt:''},{prompt:'Preset three'},{prompt:'Preset four'},
]});
assert.equal(result.applied,2);
assert.equal(result.ignored,2);
assert.deepEqual(result.prompts,['Preset one','']);

// Fewer preset prompts than the planner has segments: the rest stay unchanged.
current=[segment('Local one'),segment('Local two'),segment('Local three')];
result=importedSegmentPrompts(current,{count:1,segments:[{prompt:'Preset one'}]});
assert.equal(result.applied,1);
assert.equal(result.ignored,0);
assert.deepEqual(result.prompts,['Preset one','Local two','Local three']);

// A preset with no prompt data at all changes nothing.
result=importedSegmentPrompts([segment('Keep me')],{count:1,segments:[]});
assert.equal(result.applied,0);
assert.deepEqual(result.prompts,['Keep me']);
result=importedSegmentPrompts([segment('Keep me')],undefined);
assert.equal(result.applied,0);
assert.deepEqual(result.prompts,['Keep me']);

// Importing never reorders, adds, or removes planner segments.
current=[segment('A'),segment('B')];
result=importedSegmentPrompts(current,{count:3,segments:[{prompt:'X'},{prompt:'Y'},{prompt:'Z'}]});
assert.equal(result.prompts.length,current.length);
assert.equal(current.length,2);

console.log('preset segment prompt import: PASS');
