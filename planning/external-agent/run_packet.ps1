$ErrorActionPreference = "Stop"

python planning/external-agent/build_packet.py `
  --protocol planning/external-agent/protocol.md `
  --job planning/external-agent/job.example.json `
  --command planning/external-agent/command.txt `
  --output planning/external-agent/packet.generated.md

Write-Host ""
Write-Host "Packet ready: planning/external-agent/packet.generated.md"
Write-Host "Copy the packet content into Claude Code or another external agent."
