// The prompt-only half of a preset import, shared with the checks in tests/.
//
// Import prompts is the one preset path that keeps everything else: the canvas,
// generation duration, media, assignments, and every segment window stay exactly
// as the planner has them.  Only the per-segment prompt text is copied, so a
// preset authored against a different plan shape is still usable.
export function presetPromptSlots(presetConfig) {
  const config = presetConfig && typeof presetConfig === "object" ? presetConfig : {};
  const segments = Array.isArray(config.segments) ? config.segments : [];
  const declared = Number.isFinite(Number(config.count)) ? Math.max(0, Math.floor(Number(config.count))) : 0;
  // A declared count can never describe more entries than the preset carries,
  // and a preset without a count describes exactly the entries it carries.
  const available = Math.min(declared || segments.length, segments.length);
  // Every preset entry is a slot.  An empty prompt is an explicit value, so
  // importing it clears the matching prompt instead of leaving it untouched.
  return Array.from({ length: available }, (_, index) => {
    const segment = segments[index];
    return segment && typeof segment === "object" ? String(segment.prompt ?? "") : "";
  });
}

export function importedSegmentPrompts(currentSegments, presetConfig) {
  const slots = presetPromptSlots(presetConfig);
  const segments = Array.isArray(currentSegments) ? currentSegments : [];
  // More preset prompts than the planner has segments: use the planner's count
  // and drop the extra prompts.  Fewer: the remaining prompts stay as written.
  const applied = Math.min(slots.length, segments.length);
  return {
    applied,
    ignored: slots.length - applied,
    prompts: segments.map((segment, index) => (
      index < applied ? slots[index] : String(segment?.prompt ?? "")
    )),
  };
}
