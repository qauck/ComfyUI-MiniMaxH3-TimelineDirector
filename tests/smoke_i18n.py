"""Static localization smoke checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NODES = {
    "MiniMaxH3TimelineDirector", "MiniMaxH3TimelinePlanner",
    "MiniMaxH3TimelineEncoder", "MiniMaxH3OmniPromptBridge",
    "MiniMaxH3AddLatentGuide", "MiniMaxH3VisualDifferenceMetrics",
    "MiniMaxH3FiniteSegmentExpansion", "MiniMaxH3FiniteSegmentSampler",
    "MiniMaxH3FiniteLatentContinuation", "MiniMaxH3FiniteSegmentFinalize",
    "MiniMaxH3FiniteAudioTrimTail", "MiniMaxH3FiniteOutputTrim",
    "MiniMaxH3FiniteLoopInitialize", "MiniMaxH3FiniteLoopSegment",
    "MiniMaxH3FiniteLoopPrepare", "MiniMaxH3FiniteLoopAccumulate",
    "MiniMaxH3FiniteLoopOutput",
    "MiniMaxH3PresetLoader", "MiniMaxH3PresetExporter",
    "MiniMaxH3FiniteSegmentVideoSampler",
}


def load(language: str, filename: str) -> dict:
    return json.loads((ROOT / "locales" / language / filename).read_text(encoding="utf-8"))


def main() -> None:
    en_main, zh_main = load("en", "main.json"), load("zh", "main.json")
    en_nodes, zh_nodes = load("en", "nodeDefs.json"), load("zh", "nodeDefs.json")
    en_timeline = en_main["MiniMaxH3TimelineDirector"]["timeline"]
    zh_timeline = zh_main["MiniMaxH3TimelineDirector"]["timeline"]
    assert set(en_timeline) == set(zh_timeline)
    assert set(en_nodes) == EXPECTED_NODES == set(zh_nodes)

    # The Import prompts path needs a socket in both languages, not only a label.
    for nodes in (en_nodes, zh_nodes):
        planner_inputs = nodes["MiniMaxH3TimelinePlanner"]["inputs"]
        for socket in ("import_preset", "import_segment_prompts"):
            assert planner_inputs[socket]["name"], socket
            assert planner_inputs[socket]["tooltip"], socket
    for key in (
        "importPrompts", "promptNotConnected", "promptLoaded",
        "promptIgnoredExtra", "promptNothingToImport", "promptLoadFailed",
    ):
        assert en_timeline[key].strip() and zh_timeline[key].strip(), key
        assert re.search(r"[\u3400-\u9fff]", zh_timeline[key]), f"Untranslated prompt-import label: {key}"

    # The Local Preset Loader carries a refresh control and a control that removes
    # the selected preset folder; both need a label in both languages.
    for key in ("refreshPresets", "deletePreset"):
        assert en_timeline[key].strip() and zh_timeline[key].strip(), key
        assert re.search(r"[\u3400-\u9fff]", zh_timeline[key]), f"Untranslated preset-list label: {key}"

    javascript = (ROOT / "js/minimax_h3_timeline_director.js").read_text(encoding="utf-8")
    used_keys = set(re.findall(r'\btr\("([A-Za-z0-9_]+)"', javascript))
    missing = used_keys - set(en_timeline)
    assert not missing, f"Timeline translation keys are missing: {sorted(missing)}"
    assert 'widgetHost.style.setProperty("width", `${hostWidth}px`, "important")' in javascript
    assert 'widgetHost.style.setProperty("min-width", `${hostWidth}px`, "important")' in javascript
    backend = (ROOT / "minimax_h3_timeline_director.py").read_text(encoding="utf-8")
    assert '"import_segment_prompts", display_name="Import Segment Prompts"' in backend
    assert "import_segment_prompts=None" in backend
    assert "_imported_segment_prompts" in backend
    assert 'data-action="importPrompts"' in javascript
    assert 'applyPresetSegmentPrompts' in javascript
    assert 'loadConnectedPreset("import_segment_prompts")' in javascript
    assert 'from "./segment_prompts.mjs"' in javascript
    assert (ROOT / "js/segment_prompts.mjs").is_file()

    # The delete control on the loader is a real button wired to a real route.
    presets_backend = (ROOT / "preset_nodes.py").read_text(encoding="utf-8")
    assert 'tr("deletePreset")' in javascript
    assert '"/minimax_h3_timeline/presets/delete"' in javascript
    # The delete control is painted as a destructive action in both render paths:
    # the node draws its own widgets on the canvas, and a DOM widget host can draw
    # them as buttons instead.
    assert "inheritedOnChain(nodeType.prototype,\"drawWidgets\")" in javascript
    assert "applyPresetDeleteColour(widget)" in javascript
    assert "addPresetDeleteRule(deleteLabel)" in javascript
    assert "presetDeleteRule(" in javascript
    assert 'variant:"destructive-textonly","aria-label":deleteLabel' in javascript
    assert 'PRESET_DANGER_COLOR = "#ef6a77"' in (ROOT / "js/preset_choice.mjs").read_text(encoding="utf-8")
    assert 'routes.post("/minimax_h3_timeline/presets/delete")' in presets_backend
    assert "def _delete_preset" in presets_backend
    assert 'from "./preset_choice.mjs"' in javascript
    assert (ROOT / "js/preset_choice.mjs").is_file()
    assert (ROOT / "tests/preset_choice.test.mjs").is_file()

    for relative in (
        "__init__.py", "minimax_h3_timeline_director.py",
        "minimax_h3_finite_segments.py", "experimental_latent_guide.py",
        "drift_control_av.py",
        "preset_nodes.py",
        "segment_video_sampler.py",
        "js/minimax_h3_timeline_director.js",
        "js/segment_prompts.mjs", "js/segment_windows.mjs", "js/preset_choice.mjs",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert not re.search(r"[\u3400-\u9fff]", source), f"Hard-coded CJK remains in {relative}"
    print("localization smoke test: PASS")


if __name__ == "__main__":
    main()
