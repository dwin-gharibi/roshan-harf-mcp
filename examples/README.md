# Examples

Small, dependency-free helpers for exploring `roshan-harf-mcp`.

## `inspect_server.py`

Builds the server and prints the Harf service catalog plus every registered tool
(name, parameters, and one-line description), then dumps the catalog as JSON. No
credentials or network access required.

```bash
python examples/inspect_server.py
```

## Calling a tool

Once the server is running (stdio or HTTP) and configured with a token, an MCP
client invokes tools by name. Examples of arguments:

```jsonc
// Transcribe a remote audio file (blocks until done)
{ "tool": "harf_transcribe", "arguments": {
    "media_urls": ["https://i.ganjoor.net/a2/41417.mp3"] } }

// Kick off async transcription, then poll
{ "tool": "harf_transcribe", "arguments": {
    "media_urls": ["https://example.ir/long.mp3"], "wait": false } }
{ "tool": "harf_transcription_status", "arguments": {
    "task_ids": ["<task-id-from-previous-call>"] } }

// Force-align a known transcript to its audio
{ "tool": "harf_align", "arguments": {
    "media_url": "https://i.ganjoor.net/a2/41417.mp3",
    "text": "حکایت یکی را از حکما شنیدم که می گفت" } }

// Speaker diarization, routed to a named self-hosted instance
{ "tool": "harf_speaker_diarization", "arguments": {
    "media_urls": ["https://example.ir/panel.mp3"], "instance": "onprem" } }

// Speaker identification against named references
{ "tool": "harf_speaker_identification", "arguments": {
    "media_url": "https://example.ir/probe.mp3",
    "target_urls": { "Ali": ["https://example.ir/ali1.mp3"], "Sara": ["https://example.ir/sara1.mp3"] } } }
```

See [`../scripts/smoke_test.py`](../scripts/smoke_test.py) for an offline check
that all tools are registered correctly.
