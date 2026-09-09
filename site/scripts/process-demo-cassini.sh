#!/usr/bin/env bash
# SPDX-License-Identifier: CC0-1.0
# Process synchronized, labelled audio tracks through the actual Cassini CLI.
# No authored transcript, reference words, or external timing data enters this run.
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo 'Usage: process-demo-cassini.sh <cassini-binary> <multitrack.mkv> <output.opus> [title]' >&2
  exit 2
fi

cassini_binary="$1"
source_recording="$2"
output_opus="$3"
meeting_title="${4:-Saturday repair café: the rain plan}"
meeting_bundle="${output_opus%.opus}.meeting"
build_log="${output_opus%.opus}.build.log"

[[ -x "$cassini_binary" ]] || { echo "Cassini executable missing: $cassini_binary" >&2; exit 2; }
[[ -f "$source_recording" ]] || { echo "Source recording missing: $source_recording" >&2; exit 2; }
[[ "$output_opus" == *.opus ]] || { echo 'Output must end in .opus' >&2; exit 2; }
if [[ -e "$output_opus" || -e "$meeting_bundle" ]]; then
  echo "Output already exists; choose a fresh path: $output_opus" >&2
  exit 2
fi
mkdir -p "$(dirname "$output_opus")"

# The documented configuration uses Cassini's bundled fp32 Parakeet v3 decoder
# on CPU. Disable contextual name hints and optional summary generation. Speaker
# identity still comes from each source stream's participant_id/name metadata;
# Cassini measures cross-track attribution and word ends against those tracks.
# Clear inherited alternative models, decoder backends, transcript vocabulary,
# and attribution overrides so a caller's shell cannot change this recipe.
env -u CASSINI_STT_MODEL -u CASSINI_STT_BACKEND \
  -u CASSINI_STT_ADDITIONAL_MODELS -u CASSINI_TRANSCRIPTION_TERMS \
  -u CASSINI_ATTRIBUTION_DISABLED -u CASSINI_ATTRIBUTION_DROP \
  -u CASSINI_STT_STREAM_CONCURRENCY \
  CASSINI_STT_QUALITY=best CASSINI_STT_NUM_THREADS=6 \
  CASSINI_STT_HINTS_DISABLED=1 CASSINI_SUMMARY_DISABLED=1 \
  "$cassini_binary" build "$source_recording" \
  --out "$meeting_bundle" --device cpu --keep-work 2>&1 | tee "$build_log"

"$cassini_binary" pack "$meeting_bundle" --out "$output_opus" \
  --title "$meeting_title" 2>&1 | tee -a "$build_log"
"$cassini_binary" inspect "$output_opus" | tee -a "$build_log"
