"""Generate spec/vectors/index.json: the machine-readable conformance suite.
SPDX-License-Identifier: CC0-1.0"""
import hashlib, json, pathlib

CASSINI3 = "org.cassini.portable-meeting/3"


def V(**kw):
    return kw


VECTORS = [
 V(id="001-minimal-v3", derivedFrom=None, profiles=["metadata", "full"],
   summary="The smallest well-formed v3 file: 60 ms of audio, three words, one transcript.",
   rationale="If a reader opens nothing else in this suite, it must open this.",
   spec=["SPEC.md#file-identification", "SPEC.md#payload-encoding"],
   expect=V(classification="cassini", payloadTrust="verified", audioTrust="verified",
            formatId=CASSINI3, manifestVersion=3, manifestKind="cassini-portable-meeting",
            transcriptIds=["raw-asr"], defaultTranscriptId="raw-asr",
            wordCounts={"raw-asr": 3}, speakerIds=["spk_a", "spk_b"],
            audioOpusSha256="3504435d6e7c677c862313ffdb0ced1d0678b7bf3b8c33fd903b89a848c076a8",
            manifestEquals="decoded/001-minimal-v3.manifest.json",
            transcriptEquals={"raw-asr": "decoded/001-minimal-v3.transcript.json"},
            errors=[], warnings=[])),
 V(id="002-plain-audio", derivedFrom=None, profiles=["metadata", "full"],
   summary="Ordinary Opus audio carrying ordinary tags and not one CASSINI_ name.",
   rationale=("SPEC.md:76 makes this a MUST. It shares its audio essence byte for byte "
              "with 003, so a full reader can prove the digest does not depend on the "
              "metadata: audioOpusSha256 here equals audioOpusSha256 there."),
   spec=["SPEC.md#file-identification", "SPEC.md#1-no-cassini-metadata-present"],
   expect=V(classification="plain-audio", payloadTrust="not-applicable",
            audioTrust="not-applicable",
            audioOpusSha256="0925ee8942a13b409a6fd4c2a13056a9ad02b6af3214d383a91eb7dbb2f99aee",
            errors=[], warnings=[])),
 V(id="003-multichunk-v3", derivedFrom=None, profiles=["metadata", "full"],
   summary="900 words over 25 s of audible audio; the transcript body spans three chunk tags.",
   rationale=("Chunk reassembly is the one thing every reader must get right and the "
              "one thing 001 cannot test. 4096 + 4096 + 2119 characters."),
   spec=["SPEC.md#payload-chunk-tags"],
   expect=V(classification="cassini", payloadTrust="verified", audioTrust="verified",
            formatId=CASSINI3, manifestVersion=3, transcriptIds=["raw-asr"],
            defaultTranscriptId="raw-asr", wordCounts={"raw-asr": 900},
            audioOpusSha256="0925ee8942a13b409a6fd4c2a13056a9ad02b6af3214d383a91eb7dbb2f99aee",
            manifestEquals="decoded/003-multichunk-v3.manifest.json",
            transcriptEquals={"raw-asr": "decoded/003-multichunk-v3.transcript.json"},
            errors=[], warnings=[])),
 V(id="004-padded-base64url-v3", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="Identical to 001 except that the final chunk of each set carries base64url '=' padding.",
   rationale=("Producers write unpadded; most languages emit padded by default. "
              "Decides SPEC-D4. The reference Go reader currently REFUSES this file."),
   spec=["SPEC.md#payload-encoding"], decides="base64url-padding",
   expect=V(classification="cassini", payloadTrust="verified",
            transcriptIds=["raw-asr"], wordCounts={"raw-asr": 3},
            sameContentAs="001-minimal-v3", errors=[], warnings=[])),
 V(id="005-duplicate-chunk-tag", derivedFrom="003-multichunk-v3", profiles=["metadata", "full"],
   summary="CASSINI_TX_RAW_ASR_PAYLOAD_001 appears twice with the same value.",
   rationale=("Vorbis permits a repeated field name; Cassini must not. Two identical "
              "values still make reassembly order-dependent."),
   spec=["SPEC.md#payload-chunk-tags"], decides="duplicate-field-names",
   expect=V(classification="damaged-metadata", payloadTrust="unverified",
            errors=[V(code="duplicate-tag", tag="CASSINI_TX_RAW_ASR_PAYLOAD_001")],
            mustNot=["emit-transcript"])),
 V(id="006-missing-chunk", derivedFrom="003-multichunk-v3", profiles=["metadata", "full"],
   summary="Chunk 001 of a three-chunk transcript set is absent; 000 and 002 are present.",
   rationale="A hole in the middle, not a truncation. The count still says three.",
   spec=["SPEC.md#payload-chunk-tags"],
   expect=V(classification="damaged-metadata", payloadTrust="unverified",
            errors=[V(code="chunk-missing", tag="CASSINI_TX_RAW_ASR_PAYLOAD_001")],
            mustNot=["emit-transcript", "report-declared-word-count-as-decoded"])),
 V(id="007-chunk-count-too-high", derivedFrom="003-multichunk-v3", profiles=["metadata", "full"],
   summary="CASSINI_TX_RAW_ASR_PAYLOAD_CHUNK_COUNT says 4; payloadRef.chunkCount says 3; three chunks exist.",
   rationale=("The manifest is the record and the tag is the copy (SPEC.md:180-182), "
              "so the file is readable and the disagreement is a warning."),
   spec=["SPEC.md#cassini-descriptor-tags"], decides="tag-vs-manifest-precedence",
   expect=V(classification="cassini", payloadTrust="verified",
            wordCounts={"raw-asr": 900}, sameContentAs="003-multichunk-v3",
            warnings=[V(code="tag-manifest-disagreement",
                        tag="CASSINI_TX_RAW_ASR_PAYLOAD_CHUNK_COUNT")])),
 V(id="008-chunk-count-too-low", derivedFrom="003-multichunk-v3", profiles=["metadata", "full"],
   summary="The same disagreement in the other direction: the tag says 2, the manifest says 3.",
   rationale="Proves a reader is not silently truncating to the smaller of the two.",
   spec=["SPEC.md#cassini-descriptor-tags"], decides="tag-vs-manifest-precedence",
   expect=V(classification="cassini", payloadTrust="verified",
            wordCounts={"raw-asr": 900}, sameContentAs="003-multichunk-v3",
            warnings=[V(code="tag-manifest-disagreement",
                        tag="CASSINI_TX_RAW_ASR_PAYLOAD_CHUNK_COUNT")])),
 V(id="009-bad-payload-sha256", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="CASSINI_PAYLOAD_SHA256 is 64 zeroes. The manifest itself is intact and parses.",
   rationale=("SPEC.md:476 makes verifying the payload hash a consumer MUST. A reader "
              "that parses on regardless has not implemented it."),
   spec=["SPEC.md#consumer-requirements"],
   expect=V(classification="damaged-metadata", payloadTrust="mismatched",
            errors=[V(code="payload-sha256-mismatch", tag="CASSINI_PAYLOAD_SHA256")],
            mustNot=["report-payload-verified"])),
 V(id="010-stale-audio", derivedFrom=None, profiles=["full"],
   summary="Vector 003's complete, self-consistent metadata over vector 001's audio.",
   rationale=("The real lifecycle failure: the metadata is internally perfect and "
              "describes a different recording. Manifest and tag agree with each "
              "other and disagree with the file."),
   spec=["SPEC.md#3-cassini-metadata-present-and-audio-does-not-match"],
   expect=V(classification="cassini", payloadTrust="verified", audioTrust="mismatched",
            wordCounts={"raw-asr": 900},
            errors=[], warnings=[V(code="audio-digest-mismatch"),
                                 V(code="audio-shape-mismatch")],
            mustNot=["report-audio-verified", "discard-transcript"])),
 V(id="011-tag-manifest-disagreement", derivedFrom="001-minimal-v3", profiles=["full"],
   summary="CASSINI_AUDIO_OPUS_SHA256 is 64 f's; the manifest's copy is correct; the audio matches the manifest.",
   rationale="Verification cannot run against two different claims, so it must not report success.",
   spec=["SPEC.md#cassini-descriptor-tags", "SPEC.md#v3-compressed-opus-integrity"],
   expect=V(classification="cassini", payloadTrust="verified", audioTrust="unverified",
            warnings=[V(code="tag-manifest-disagreement", tag="CASSINI_AUDIO_OPUS_SHA256")],
            mustNot=["report-audio-verified"])),
 V(id="012-lowercase-tag-names", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="Vector 001 with every comment name lower-cased. Values untouched.",
   rationale=("Vorbis field names are case-insensitive and SPEC.md never says so. "
              "The shipped browser viewer fails this file."),
   spec=["SPEC.md#cassini-descriptor-tags"], decides="tag-name-case",
   expect=V(classification="cassini", payloadTrust="verified",
            sameContentAs="001-minimal-v3", errors=[], warnings=[])),
 V(id="013-mixed-case-tag-names", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="Vector 001 with alternating case in every comment name (cAsSiNi_FoRmAt).",
   rationale="Catches a reader that lower-cases or upper-cases only some lookups.",
   spec=["SPEC.md#cassini-descriptor-tags"], decides="tag-name-case",
   expect=V(classification="cassini", payloadTrust="verified",
            sameContentAs="001-minimal-v3", errors=[], warnings=[])),
 V(id="014-unknown-manifest-member", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="The manifest carries a top-level cassiniFutureField and a speakers[0].pronouns.",
   rationale=("Forward compatibility. The schemas say additionalProperties:false and "
              "every reader is permissive; the schemas are what is wrong."),
   spec=["SPEC.md#embedded-manifest"], decides="additional-properties",
   expect=V(classification="cassini", payloadTrust="verified",
            transcriptIds=["raw-asr"], wordCounts={"raw-asr": 3},
            speakerIds=["spk_a", "spk_b"], errors=[], warnings=[])),
 V(id="015-unknown-major-version", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="CASSINI_FORMAT=org.cassini.portable-meeting/99 and manifest.version=99.",
   rationale=("A reader may decode a future version, but it must not present the "
              "content as if it understood the version."),
   spec=["SPEC.md#file-identification"], decides="unknown-version-behaviour",
   expect=V(classification="unsupported-version", formatId="org.cassini.portable-meeting/99",
            payloadTrust="unverified", mustNot=["present-as-current"]),
   alsoAcceptable=[V(classification="cassini", manifestVersion=99,
                     warnings=[V(code="unsupported-version")])]),
 V(id="016-two-transcripts", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="Two raw-asr transcripts, raw-asr (default:true) and second-pass (default:false), three words each.",
   rationale=("The format's headline feature and nothing tests it. Also the minimal "
              "reproduction of the reference inspector summing word counts across "
              "alternative transcripts and reporting six."),
   spec=["SPEC.md#manifest-shape-v2", "SPEC.md#consumer-rules-v2"],
   expect=V(classification="cassini", payloadTrust="verified",
            transcriptIds=["raw-asr", "second-pass"], defaultTranscriptId="raw-asr",
            wordCounts={"raw-asr": 3, "second-pass": 3}, errors=[], warnings=[],
            mustNot=["sum-word-counts-across-transcripts"])),
 V(id="017-dangling-transcript-id", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="CASSINI_TRANSCRIPT_IDS=raw-asr,ghost. No manifest entry and no chunk set for ghost.",
   rationale=("The tag is a convenience copy. A reader must take its transcript list "
              "from the manifest and must not fail over a stale copy."),
   spec=["SPEC.md#cassini-descriptor-tags"],
   expect=V(classification="cassini", payloadTrust="verified",
            transcriptIds=["raw-asr"], wordCounts={"raw-asr": 3},
            warnings=[V(code="tag-manifest-disagreement", tag="CASSINI_TRANSCRIPT_IDS")],
            mustNot=["fail"])),
 V(id="018-oversize-opustags", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary=("A 65,351-octet OpusTags packet, inflated by a 46 KB attachments[] entry. "
            "24 comments fall past octet 61,440, including CASSINI_PAYLOAD_CHUNK_COUNT "
            "and CASSINI_PAYLOAD_SHA256."),
   rationale=("RFC 7845 5.2 lets an implementation ignore comments not fully inside "
              "the first 61,440 octets. A reader that exercises that MAY sees "
              "CASSINI_FORMAT and nothing it needs to act on it."),
   spec=["RFC7845#section-5.2", "SPEC.md#payload-chunk-tags"], decides="comment-header-size",
   expect=V(classification="cassini", payloadTrust="verified",
            sameContentAs="001-minimal-v3"),
   alsoAcceptable=[V(classification="damaged-metadata",
                     errors=[V(code="comment-header-truncated")])],
   note="MUST NOT be classified plain-audio: CASSINI_FORMAT is inside the window."),
 V(id="019-manifest-chunk-count-too-high", derivedFrom="001-minimal-v3", profiles=["metadata", "full"],
   summary="CASSINI_PAYLOAD_CHUNK_COUNT=2 with one chunk present.",
   rationale=("The manifest chunk set is the one set with no payloadRef behind it, so "
              "this tag is load-bearing and a reader must act on it."),
   spec=["SPEC.md#payload-chunk-tags"],
   expect=V(classification="damaged-metadata", payloadTrust="unverified",
            errors=[V(code="chunk-missing", tag="CASSINI_PAYLOAD_001")],
            mustNot=["emit-transcript"])),
 V(id="020-duplicate-chunk-differing", derivedFrom="003-multichunk-v3", profiles=["metadata", "full"],
   summary="CASSINI_TX_RAW_ASR_PAYLOAD_001 twice: junk first, the real value second.",
   rationale="Separates 'is a repeat legal' from 'which repeat wins'. Neither question has an answer today.",
   spec=["SPEC.md#payload-chunk-tags"], decides="duplicate-field-names",
   expect=V(classification="damaged-metadata", payloadTrust="unverified",
            errors=[V(code="duplicate-tag", tag="CASSINI_TX_RAW_ASR_PAYLOAD_001")],
            mustNot=["emit-transcript"])),
 V(id="021-descriptors-first", derivedFrom="018-oversize-opustags", profiles=["metadata", "full"],
   summary=("Byte-identical comment set to 018 in a different write order: every "
            "descriptor before every chunk tag. Same 65,351-octet packet."),
   rationale=("The control for 018 and the demonstration of the proposed producer "
              "rule. Load-bearing comments past octet 61,440: 17 in 018, 0 here."),
   spec=["RFC7845#section-5.2"], decides="comment-header-size",
   expect=V(classification="cassini", payloadTrust="verified",
            sameContentAs="001-minimal-v3", errors=[], warnings=[])),
 V(id="022-duplicate-chunk-junk-last", derivedFrom="003-multichunk-v3", profiles=["metadata", "full"],
   summary="CASSINI_TX_RAW_ASR_PAYLOAD_001 twice: the real value first, junk second.",
   rationale="The mirror of 020. A last-wins reader accepts 020 and breaks here; a first-wins reader does the opposite.",
   spec=["SPEC.md#payload-chunk-tags"], decides="duplicate-field-names",
   expect=V(classification="damaged-metadata", payloadTrust="unverified",
            errors=[V(code="duplicate-tag", tag="CASSINI_TX_RAW_ASR_PAYLOAD_001")],
            mustNot=["emit-transcript"])),
]

doc = {
    "suite": "org.cassini.portable-meeting/vectors/1",
    "covers": [CASSINI3],
    "notCovered": ["org.cassini.portable-meeting/1", "org.cassini.portable-meeting/2"],
    "updated": "2026-09-01",
    "profiles": {
        "metadata": ("Decodes the tags and the chunk sets and verifies every declared "
                     "payload SHA-256 and byte count. Does not read the audio. Such a "
                     "reader reports audioTrust 'not-checked' and never 'verified'."),
        "full": ("Everything a metadata reader does, plus exact-opus-audio-v1 over the "
                 "compressed audio packets."),
    },
    "vectors": [],
}
for v in VECTORS:
    p = pathlib.Path("opus") / f"{v['id']}.opus"
    entry = {"id": v["id"], "file": str(p), "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    entry.update({k: val for k, val in v.items() if k != "id"})
    doc["vectors"].append(entry)
pathlib.Path("index.json").write_text(json.dumps(doc, indent=2) + "\n")
print(f"index.json: {len(doc['vectors'])} vectors, "
      f"{pathlib.Path('index.json').stat().st_size} bytes")
