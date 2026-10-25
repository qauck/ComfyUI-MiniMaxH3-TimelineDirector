"""Local preset export/import and planner integration smoke test."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_finite_segments import _load_package


def main() -> None:
    plugin = Path(__file__).resolve().parents[1]
    finite = _load_package(plugin)
    package = finite.__package__
    preset = __import__(f"{package}.preset_nodes", fromlist=["preset_nodes"])
    director = __import__(f"{package}.minimax_h3_timeline_director", fromlist=["timeline"])

    with tempfile.TemporaryDirectory() as temp_text:
        temp = Path(temp_text)
        input_root, output_root = temp / "input", temp / "output"
        upload = input_root / "minimax_h3_timeline_director"
        upload.mkdir(parents=True)
        for name, content in (("clip.mp4", b"video"), ("still.png", b"image"), ("voice.wav", b"audio")):
            (upload / name).write_bytes(content)

        timeline = {
            "version": 9,
            "globalPrompt": "Portable prompt",
            "secondPass": True,
            "secondPassModel": "machine-specific.safetensors",
            "secondPassHighSteps": 2,
            "loraEnabled": True,
            "pluginVersion": "do-not-export",
            "selection": {"start": 0.0, "duration": 5.0},
            "videoAudioEnabled": True,
            "videoClips": [{
                "id": "v1", "file": "minimax_h3_timeline_director/clip.mp4",
                "name": "clip.mp4", "start": 0.0, "trimStart": 0.0, "duration": 5.0,
                "hasAudio": True, "referenceMode": "edit", "proxy": "private.mp4", "peaks": [0.1],
            }],
            "images": [{"id": "i1", "file": "minimax_h3_timeline_director/still.png", "name": "still.png"}],
            "audios": [{"id": "a1", "file": "minimax_h3_timeline_director/voice.wav", "name": "voice.wav", "audioMode": "locked"}],
            "segmentConfig": {"mode": "timeline", "count": 1, "activeIndex": 0, "segments": [{"startFrame": 0, "endFrame": 120, "prompt": "One", "images": ["i1"], "audios": ["a1"]}]},
        }
        plan = director._create_timeline_plan(json.dumps(timeline), 640, 352, 5.0)

        with patch.object(preset.folder_paths, "get_input_directory", return_value=str(input_root)), patch.object(
            preset.folder_paths, "get_output_directory", return_value=str(output_root)
        ):
            config_folder, _ = preset.MiniMaxH3PresetExporter.execute(
                "Config only", "configuration", material_plan=plan
            )
            config_data = json.loads((Path(config_folder) / "preset.json").read_text(encoding="utf-8"))
            assert not (Path(config_folder) / "media").exists()
            serialized = json.dumps(config_data)
            assert "machine-specific" not in serialized and "lora" not in serialized.lower()
            assert "private.mp4" not in serialized and "peaks" not in serialized

            complete_folder, _ = preset.MiniMaxH3PresetExporter.execute(
                "Complete", "complete", segment_plan=plan
            )
            assert (Path(complete_folder) / "media" / "videos" / "clip.mp4").read_bytes() == b"video"
            loaded, name, _ = preset.MiniMaxH3PresetLoader.execute(Path(complete_folder).name)
            assert name == Path(complete_folder).name
            for collection in ("videoClips", "images", "audios"):
                for asset in loaded["timeline"][collection]:
                    assert (input_root / asset["file"]).is_file()

            events = []
            with patch.object(director, "_create_prompt_media_bundle", side_effect=lambda value: value), patch.object(
                director.PromptServer.instance, "send_sync", side_effect=lambda *args: events.append(args), create=True
            ):
                selected, _, complete = director.MiniMaxH3TimelinePlanner.execute(
                    1344, 768, 9.0, "{}", import_preset=loaded, unique_id="42"
                )
            assert (selected["width"], selected["height"]) == (640, 352)
            assert selected["timeline"]["globalPrompt"] == "Portable prompt"
            assert complete["generation_seconds"] == 5.0
            assert events and events[0][0] == "minimax_h3_timeline_preset_applied"
            assert events[0][1]["node_id"] == "42"
            assert events[0][1]["timeline"]["segmentConfig"]["count"] == 1

            # Import Segment Prompts serves the Import prompts button only: the
            # prompt slots it exposes are clamped to the preset's own segment
            # entries, and the plan a queue run produces is unchanged.
            slots = director._imported_segment_prompts(loaded)
            assert [segment["prompt"] for segment in slots] == ["One"]
            three_segment_prompt_preset = {**loaded, "timeline": {
                **loaded["timeline"],
                "segmentConfig": {"mode": "timeline", "count": 3, "activeIndex": 0, "segments": [
                    {"startFrame": 0, "endFrame": 120, "prompt": "First", "images": [], "audios": []},
                    {"startFrame": 120, "endFrame": 240, "prompt": "", "images": [], "audios": []},
                    {"startFrame": 240, "endFrame": 360, "prompt": "Third", "images": [], "audios": []},
                    {"startFrame": 360, "endFrame": 480, "prompt": "Unused", "images": [], "audios": []},
                ]},
            }}
            assert [segment["prompt"] for segment in director._imported_segment_prompts(three_segment_prompt_preset)] == ["First", "", "Third"]
            local_timeline = json.dumps({
                "version": 10, "selection": {"start": 0.0, "duration": 5.0},
                "segmentConfig": {"mode": "timeline", "count": 2, "activeIndex": 0, "segments": [
                    {"startFrame": 0, "endFrame": 120, "prompt": "Local one", "images": [], "audios": []},
                    {"startFrame": 120, "endFrame": 240, "prompt": "Local two", "images": [], "audios": []},
                ]},
            })
            prompted, _, prompted_complete = director.MiniMaxH3TimelinePlanner.execute(
                1344, 768, 9.0, local_timeline,
                import_segment_prompts=three_segment_prompt_preset, unique_id="43",
            )
            prompts = [segment["prompt"] for segment in prompted["timeline"]["segmentConfig"]["segments"]]
            assert prompts == ["Local one", "Local two"]
            # Nothing else moves: this node keeps its own 1344x768 canvas, its
            # own 9.0-second duration, and its own window timings, instead of the
            # preset's 640x352 canvas and its different windows, and the prompts
            # the node already had are still the ones the plan carries.
            assert (prompted["width"], prompted["height"]) == (1344, 768)
            assert prompted["generation_seconds"] == 5.0
            assert [
                (segment["startFrame"], segment["endFrame"])
                for segment in prompted["timeline"]["segmentConfig"]["segments"]
            ] == [(0, 120), (120, 240)]
            assert prompted_complete["generation_seconds"] == 9.0
            assert prompted_complete["timeline"]["segmentConfig"]["count"] == 2
            try:
                director.MiniMaxH3TimelinePlanner.execute(
                    1344, 768, 9.0, local_timeline, import_segment_prompts={"type": "other"}
                )
            except ValueError as error:
                assert "MiniMax H3 Local Preset Loader" in str(error)
            else:
                raise AssertionError("A non-preset Import Segment Prompts link must fail")
            sockets = {spec.id: spec for spec in director.MiniMaxH3TimelinePlanner.define_schema().inputs}
            assert "import_segment_prompts" in sockets
            assert sockets["import_segment_prompts"].optional
            assert sockets["import_segment_prompts"].display_name == "Import Segment Prompts"
            assert sockets["import_segment_prompts"].tooltip

    print("preset smoke test: PASS")


if __name__ == "__main__":
    main()
