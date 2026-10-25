// Which preset the Local Preset Loader combo holds after its list changes.
//
// Removing a preset from disk must leave the combo on something usable: the
// entry that followed the removed folder, the entry before it when the removed
// folder was last, and the empty marker when nothing is stored any more.

export const EMPTY_PRESET_LABEL = "(no presets found)";

// Options for the combo from whatever the server answered. An empty preset
// directory is not an empty list: the marker stays selectable.
export function presetNames(payload) {
  const listed = Array.isArray(payload?.presets)
    ? payload.presets.filter(name => typeof name === "string" && name)
    : [];
  return listed.length ? listed : [EMPTY_PRESET_LABEL];
}

// `known` is the list the combo held before the delete, `remaining` the list the
// server reports after it. An entry the combo no longer recognizes is treated as
// the start of the list, so the control never leaves the user with nothing.
export function presetAfterDelete(known, remaining, removed) {
  const names = presetNames({ presets: remaining });
  const removedAt = Array.isArray(known) ? known.indexOf(removed) : -1;
  const fallback = removedAt < 0 ? 0 : Math.min(removedAt, names.length - 1);
  return names[fallback];
}

// Deleting a preset removes a folder from disk, so its control is painted in the
// same red the planner UI uses for its own danger buttons.
export const PRESET_DANGER_COLOR = "#ef6a77";

// The canvas renderer draws the button itself.  Its widget class answers
// `text_color` with the palette colour and the draw code fills the label with
// exactly that, so the only lever left is the widget: an accessor the widget
// itself owns outranks the class answer, and the drawn text follows it.
export function applyPresetDeleteColour(widget) {
  if (!widget || typeof widget !== "object") return false;
  try {
    Object.defineProperty(widget, "text_color", {
      configurable: true,
      get: () => PRESET_DANGER_COLOR,
    });
  } catch (error) {
    return false;
  }
  return widget.text_color === PRESET_DANGER_COLOR;
}

// The DOM renderer colours its button from a class the widget host writes itself,
// so only a rule that outranks that class changes the text.  The rule is anchored
// on the label, not on the node id: the id is not assigned yet while the node is
// being created, and this label belongs to this control alone.  A translated label
// is escaped because it is text, never CSS.
export function presetDeleteRule(label) {
  const safeLabel = String(label).replace(/[\\"]/g, (character) => `\\${character}`);
  return `button[aria-label="${safeLabel}"] { color:${PRESET_DANGER_COLOR} !important; }`;
}
