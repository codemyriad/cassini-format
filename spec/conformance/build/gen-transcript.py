"""Deterministic filler transcript. No randomness: the same arguments always
produce the same bytes, so a rebuilt vector is a rebuilt vector."""
import json, sys

WORDS = ("the quick brown fox jumps over the lazy dog while nine agenda items "
         "wait for a decision that nobody in this room is willing to make today "
         "so we agreed to revisit it next week with numbers attached").split()


def build(word_count, duration_ms, speaker_count, out):
    speakers = [{"id": f"spk_{i:02d}", "label": f"Speaker {i:02d}"}
                for i in range(speaker_count)]
    step = duration_ms // word_count
    items = []
    for i in range(word_count):
        w = WORDS[i % len(WORDS)]
        # a new speaker every 11 words, so turns are visible
        spk = speakers[(i // 11) % speaker_count]["id"]
        start = i * step
        items.append({"speaker": spk, "startMs": start,
                      "endMs": start + max(1, step - 10),
                      "text": w + ("." if (i + 1) % 17 == 0 else "")})
    json.dump({"speakers": speakers, "items": items}, open(out, "w"),
              separators=(",", ":"))


if __name__ == "__main__":
    build(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
