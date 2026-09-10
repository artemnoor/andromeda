from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from scripts import run_spike_demo


class PopenRecorder:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


def test_start_process_uses_posix_process_session(monkeypatch: Any) -> None:
    recorder: PopenRecorder | None = None

    def fake_popen(*args: Any, **kwargs: Any) -> PopenRecorder:
        nonlocal recorder
        recorder = PopenRecorder(*args, **kwargs)
        return recorder

    monkeypatch.setattr(run_spike_demo.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(run_spike_demo, "os", SimpleNamespace(name="posix"))

    result = run_spike_demo._start_process(["demo"], {"PATH": "safe"}, "spike", cwd=Path("."))

    assert result is recorder
    assert recorder is not None
    assert recorder.kwargs["start_new_session"] is True
    assert "creationflags" not in recorder.kwargs


def test_start_process_uses_typed_windows_process_group_flag(monkeypatch: Any) -> None:
    recorder: PopenRecorder | None = None

    def fake_popen(*args: Any, **kwargs: Any) -> PopenRecorder:
        nonlocal recorder
        recorder = PopenRecorder(*args, **kwargs)
        return recorder

    monkeypatch.setattr(run_spike_demo.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(run_spike_demo, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(run_spike_demo.subprocess, "CREATE_NEW_PROCESS_GROUP", 512, raising=False)

    result = run_spike_demo._start_process(["demo"], {"PATH": "safe"}, "spike", cwd=Path("."))

    assert result is recorder
    assert recorder is not None
    assert recorder.kwargs["creationflags"] == 512
    assert isinstance(recorder.kwargs["creationflags"], int)
    assert "start_new_session" not in recorder.kwargs


def test_start_process_falls_back_to_zero_when_windows_flag_is_missing(monkeypatch: Any) -> None:
    recorder: PopenRecorder | None = None

    def fake_popen(*args: Any, **kwargs: Any) -> PopenRecorder:
        nonlocal recorder
        recorder = PopenRecorder(*args, **kwargs)
        return recorder

    monkeypatch.setattr(run_spike_demo.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(run_spike_demo, "os", SimpleNamespace(name="nt"))
    monkeypatch.delattr(run_spike_demo.subprocess, "CREATE_NEW_PROCESS_GROUP", raising=False)

    result = run_spike_demo._start_process(["demo"], {"PATH": "safe"}, "spike", cwd=Path("."))

    assert result is recorder
    assert recorder is not None
    assert recorder.kwargs["creationflags"] == 0
    assert isinstance(recorder.kwargs["creationflags"], int)
