# Rollout plan, v1

Date: 2026-03-11

Status: historical. Delivered in part; the command names below are not the ones
that shipped.

Kept because it records what was planned, not what exists. For the commands that
exist, run `cassini help`.

## Phase 1: Read support

- add `cassini inspect meeting.opus`
- add Cassini metadata detection for `.opus`
- add integrity verification and plain-audio fallback

## Phase 2: Export support

- add `cassini pack <meeting bundle> --out meeting.opus`
- emit the v1 tags and embedded manifest

## Phase 3: Native record flow

- add `cassini record --out meeting.opus`
- add `cassini record --into ./Archive`

## Phase 4: Archive UX

- add `cassini browse ./Archive`
- add `cassini add file.opus ./Archive`
- add `cassini share file.opus --out ./shared`
