from __future__ import annotations

import argparse
import json
from pathlib import Path


# Read a UTF-8 text file and return its trimmed contents, or fail loudly if missing.
def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


# Read a JSON file and return it as a dict, validating both the JSON and the root type.
def _read_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON root in {path} must be an object")
    return data


# Stitch protocol + injection command + job config into one markdown packet for external agents.
def build_packet(protocol_path: Path, job_path: Path, command_path: Path) -> str:
    protocol_text = _read_text(protocol_path)
    job_data = _read_json(job_path)
    command_text = _read_text(command_path)

    sections = [
        "# External Agent Execution Packet",
        "",
        "Use this entire packet as the prompt for Claude Code or another external coding agent.",
        "",
        "## Injection Command",
        "",
        command_text,
        "",
        "## Protocol",
        "",
        protocol_text,
        "",
        "## Job Configuration",
        "",
        "```json",
        json.dumps(job_data, indent=2),
        "```",
    ]
    return "\n".join(sections) + "\n"


# CLI entry point: parse paths, build the packet, and write it to disk.
def main() -> None:
    parser = argparse.ArgumentParser(description="Build a single prompt packet for external agents")
    parser.add_argument(
        "--protocol",
        default="planning/external-agent/protocol.md",
        help="Path to external workflow protocol markdown",
    )
    parser.add_argument(
        "--job",
        default="planning/external-agent/job.example.json",
        help="Path to external agent job JSON",
    )
    parser.add_argument(
        "--command",
        default="planning/external-agent/command.txt",
        help="Path to external command/instruction text",
    )
    parser.add_argument(
        "--output",
        default="planning/external-agent/packet.generated.md",
        help="Output markdown packet path",
    )
    args = parser.parse_args()

    packet = build_packet(
        protocol_path=Path(args.protocol),
        job_path=Path(args.job),
        command_path=Path(args.command),
    )

    output_path = Path(args.output)
    output_path.write_text(packet, encoding="utf-8")
    print(f"Generated packet: {output_path}")


if __name__ == "__main__":
    main()
