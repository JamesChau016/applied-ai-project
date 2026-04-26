import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "planning" / "external-agent" / "build_packet.py"


def test_build_external_agent_packet_success(tmp_path):
    protocol = tmp_path / "protocol.md"
    job = tmp_path / "job.json"
    command = tmp_path / "command.txt"
    output = tmp_path / "packet.md"

    protocol.write_text("# Protocol\n\nPlan -> Execute -> Observe -> Re-plan", encoding="utf-8")
    job.write_text(
        '{"job_name": "demo", "objective": "Implement feature", "scope": ["src"]}',
        encoding="utf-8",
    )
    command.write_text("Run protocol and report phases.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--protocol",
            str(protocol),
            "--job",
            str(job),
            "--command",
            str(command),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert output.exists()

    packet = output.read_text(encoding="utf-8")
    assert "# External Agent Execution Packet" in packet
    assert "## Injection Command" in packet
    assert "## Protocol" in packet
    assert "## Job Configuration" in packet
    assert '"job_name": "demo"' in packet


def test_build_external_agent_packet_invalid_job_json(tmp_path):
    protocol = tmp_path / "protocol.md"
    job = tmp_path / "job.json"
    command = tmp_path / "command.txt"
    output = tmp_path / "packet.md"

    protocol.write_text("# Protocol", encoding="utf-8")
    job.write_text("{ invalid json", encoding="utf-8")
    command.write_text("Command", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--protocol",
            str(protocol),
            "--job",
            str(job),
            "--command",
            str(command),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Invalid JSON" in result.stderr
