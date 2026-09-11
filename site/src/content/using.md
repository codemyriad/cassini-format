We needed this for [gocassini](https://github.com/codemyriad/gocassini), our
Nextcloud Talk app. We wanted to find a passage in a transcript and hear what
was actually said. Transcriptions can miss a word or change the meaning.
Keeping the recording and timed words in one file means we can listen back,
even after the file is saved or shared.

That has been useful for our own meetings, so we published the format. The
examples and checks on this site come from that work. We think the idea could
help elsewhere too; the workflow below explains what is available for you to try.

If you already have a file, [open it in the browser player](/try/). You can
listen and read without installing anything or uploading your recording.

## From a recording to something you can share

1. **Create the file.** A producer combines Ogg Opus audio with a transcript,
   word timings and speaker labels. Recording and speech recognition happen
   before packaging. Our app, [gocassini](https://github.com/codemyriad/gocassini),
   records and transcribes Nextcloud Talk calls; developers can also
   [package inputs from their own pipeline](/produce/).
2. **Send or save it.** The result is one `.opus` file. Its text travels with
   the audio when you copy the file, so the recipient does not need a matching
   transcript attachment or access to the original recording service.
3. **Read, then listen.** An Ogg Opus player plays the audio. A Cassini
   reader also opens the embedded words and speakers, helping you find a
   passage and listen to check what was said. Your own software can
   [extract that data](/consume/) for search, analysis or another interface.

The [example recording](/try/) demonstrates that whole artifact: the player
reads its transcript from the downloadable audio file. Find a passage, then
play it and compare what you hear with the text. Save the example and open the
saved copy to try the same workflow a recipient would use.

## What do you have today?

| Your starting point | What comes next |
| --- | --- |
| A Cassini recording someone sent you | [Open the file](/try/) to read and listen. Ordinary audio playback needs an Ogg Opus player. |
| Ogg Opus audio and words with timestamps | [Package them together](/produce/). The standalone producer keeps the encoded audio intact. |
| Audio in another format, such as WAV or MP3 | Create an Ogg Opus copy before packaging. Converting audio to Opus is lossy; keep an original when you need it. |
| A recording with no transcript | Transcribe it first with a tool of your choice. Opening audio on this site does not generate text. |
| Text or subtitles without word timings | Add or align word timings to get word-by-word seeking. The standalone packer expects timed JSON; it does not import SRT, VTT or plain text directly. |

For a meeting or interview, this can make a useful sharing copy. For a collection
with preservation masters, consider how an Opus access copy fits alongside
those originals. Cassini does not require you to replace the files or systems
you already use.

## What the recipient needs

| Where the file is opened | What is available |
| --- | --- |
| A player that supports Ogg Opus | The audio. It generally ignores the Cassini transcript metadata. |
| [This browser player](/try/) | The default word transcript, speakers and audio, with word seeking. Local files stay in the browser. |
| [gocassini](https://github.com/codemyriad/gocassini) | The reference recording application and its transcript viewer. Check the [implementation status](/status/) for compatibility with installed builds. |
| Software you build | The open format and [standalone readers](/build/) let you choose which capabilities to support. |

The format can carry multiple transcripts and additional context. A particular
reader may show only some of them. The browser player here is one example of
using the format; its features do not define the full contract.

## What stays with the file

Copying the file preserves the recording, embedded words, speakers and any
additional metadata the producer included. Reading them does not require a
Cassini account or a running copy of the original service. The specification
and reusable reader code are public.

Editing or converting the audio can strip its metadata or leave the words out
of sync. Keep the original and [check the result](/verify/) when another tool
rewrites a file. Adding metadata with a Cassini producer preserves the compressed
audio packets; arbitrary audio editors may behave differently.

Checks can establish that embedded data is intact and that the audio matches
the file's recorded claim. They do not establish that a transcript is accurate
or prove who spoke. In the browser player, “audio match not checked” means that
check has not run, rather than that a mismatch was found.

## Is it ready for your workflow?

Version 1 is published. Our experience is with gocassini and the tools in this
repository; we do not yet have independent adoption to report. Read the
[project status](/status/) for adoption, revisions and compatibility before
choosing a deployment.

A useful first trial is to take one representative recording through creation,
sharing, opening in the recipient's software, and reading back the data. That
shows which parts of your workflow are already covered and where you would need
an integration. The [implementation paths](/build/) explain what you can reuse
and how to check the result.
