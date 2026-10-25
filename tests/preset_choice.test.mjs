import assert from 'node:assert/strict';
import {EMPTY_PRESET_LABEL, PRESET_DANGER_COLOR, applyPresetDeleteColour, presetAfterDelete, presetDeleteRule, presetNames} from '../js/preset_choice.mjs';

// What the server reports becomes the combo list; an empty preset directory is
// still a list the loader can show.
assert.deepEqual(presetNames({presets: ['Alpha', 'Beta']}), ['Alpha', 'Beta']);
assert.deepEqual(presetNames({presets: []}), [EMPTY_PRESET_LABEL]);
assert.deepEqual(presetNames({}), [EMPTY_PRESET_LABEL]);
assert.deepEqual(presetNames({presets: ['Alpha', '', null, 'Beta']}), ['Alpha', 'Beta']);

// A deleted middle preset leaves the combo on the preset that followed it.
assert.equal(presetAfterDelete(['A', 'B', 'C'], ['A', 'C'], 'B'), 'C');
assert.equal(presetAfterDelete(['A', 'B', 'C', 'D'], ['A', 'C', 'D'], 'B'), 'C');

// A deleted last preset falls back to the previous entry.
assert.equal(presetAfterDelete(['A', 'B', 'C'], ['A', 'B'], 'C'), 'B');
assert.equal(presetAfterDelete(['A', 'B'], ['A'], 'B'), 'A');

// A deleted only preset leaves nothing but the empty marker.
assert.equal(presetAfterDelete(['A'], [], 'A'), EMPTY_PRESET_LABEL);
assert.equal(presetAfterDelete([EMPTY_PRESET_LABEL], [], EMPTY_PRESET_LABEL), EMPTY_PRESET_LABEL);

// A name the combo no longer holds (a stale or renamed preset) starts from the
// top of the list rather than choosing nothing.
assert.equal(presetAfterDelete(['A', 'B'], ['B'], 'Gone'), 'B');
assert.equal(presetAfterDelete(undefined, ['A', 'B'], 'A'), 'A');
assert.equal(presetAfterDelete([], ['A', 'B'], 'A'), 'A');

// The answer is always something the new list actually contains.
for (const [known, remaining, removed] of [
  [['A', 'B', 'C'], ['A', 'C'], 'B'],
  [['A', 'B', 'C'], ['A', 'B'], 'C'],
  [['A'], [], 'A'],
  [['A', 'B'], ['B'], 'Gone'],
]) {
  const names = presetNames({presets: remaining});
  assert.ok(names.includes(presetAfterDelete(known, remaining, removed)));
}

// The canvas renderer draws the button itself and fills its label with the colour
// the widget reports: the widget class answers `text_color` with the palette
// colour, and the widget's own answer has to outrank the class answer.
const palette = {get text_color() { return '#DDD'; }};
const widget = Object.create(palette);
assert.equal(widget.text_color, '#DDD');
assert.equal(applyPresetDeleteColour(widget), true);
assert.equal(widget.text_color, PRESET_DANGER_COLOR);
assert.equal(PRESET_DANGER_COLOR, '#ef6a77');

// The answer stays configurable, because the frontend re-describes the widget when
// it turns it into its own kind of object.
assert.equal(Object.getOwnPropertyDescriptor(widget, 'text_color').configurable, true);

// A widget that cannot carry the answer is reported as unpainted instead of being
// left half-coloured.
assert.equal(applyPresetDeleteColour(undefined), false);
assert.equal(applyPresetDeleteColour(null), false);
assert.equal(applyPresetDeleteColour(Object.freeze({})), false);

// The DOM render path colours its button from a class the widget host writes
// itself, so the rule has to outrank that class.
assert.equal(
  presetDeleteRule('Delete current preset'),
  'button[aria-label="Delete current preset"] { color:#ef6a77 !important; }',
);
assert.ok(presetDeleteRule('x').includes('!important'));

// A translated label is text, never CSS: a quote or a backslash cannot break the
// selector it is placed in.
assert.ok(presetDeleteRule('Say "hi"').includes('aria-label="Say \\"hi\\""'));
assert.ok(presetDeleteRule('back\\slash').includes('aria-label="back\\\\slash"'));
assert.ok(presetDeleteRule('Delete [current]').includes('aria-label="Delete [current]"'));
