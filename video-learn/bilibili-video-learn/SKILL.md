---
name: bilibili-video-learn
description: 'Turn Bilibili video frames and subtitles into a full teaching note'
disable-model-invocation: true
---

# Bilibili Video Learn

Download a Bilibili video with its AI subtitles, extract deduplicated frames,
then read both to write a teaching note.

## Workspace layout

Everything is produced inside the **current working directory**:

```
./
├── video/          # mp4 + srt (step 2)
├── frames/         # deduplicated frames + frames.tsv (step 4)
├── resources/      # OPTIONAL, user-supplied code snippets and slides
└── notes/          # teaching note (step 6)
```

`SLUG` below means a short kebab-case name for the video, e.g. `168-zap-logger`. Pick it once in step 1 and reuse it everywhere.

## Step 1 — Preflight

Confirm the toolchain before downloading anything:

```sh
yt-dlp --version
ffmpeg -version | head -1
python3 -c "import PIL, imagehash; print('Dependencies OK')"
ls -l /mnt/c/Users/fulim/Downloads/cookies.txt
```

If anything is missing:

```sh
sudo apt update && sudo apt install -y ffmpeg python3-pip
python3 -m pip install --user Pillow ImageHash yt-dlp
```

If `cookies.txt` is missing or expired, **stop and tell the user** to install
the _Get cookies.txt LOCALLY_ Chrome extension, open bilibili.com while logged
in, and export `cookies.txt` to their Downloads folder. Without fresh cookies
the high-quality formats and AI subtitles are not available.

Ask the user for the video URL if it was not given, and agree on the `SLUG`.

## Step 2 — Download into `video/`

Download from inside `video/` so the mp4 and the srt both land there:

```sh
mkdir -p video && cd video

yt-dlp \
  --cookies /mnt/c/Users/fulim/Downloads/cookies.txt \
  -f "30064+30280" \
  --write-subs \
  --sub-langs ai-zh \
  --sub-format srt \
  --merge-output-format mp4 \
  "<bilibili-url>"
```

### yt-dlp flags

| Flag                        | What it does                                                                     |
| --------------------------- | -------------------------------------------------------------------------------- |
| `--cookies <file>`          | Netscape-format cookie jar; required for logged-in quality and AI subtitles      |
| `-f "30064+30280"`          | Explicit format ids: `30064` = 720p video, `30280` = 192k audio, merged together |
| `--write-subs`              | Write the subtitle track to a file next to the video                             |
| `--sub-langs ai-zh`         | Bilibili's AI-generated Chinese subtitles                                        |
| `--sub-format srt`          | Preferred subtitle format                                                        |
| `--merge-output-format mp4` | Remux the separate video and audio streams into one mp4                          |

Reference flags for when a download misbehaves (not part of the standard run):
`-F` lists the format ids available for that video, `--list-subs` lists its
subtitle tracks, `--skip-download` fetches subtitles only.

### Rename

yt-dlp names files after the Bilibili title, e.g.
`168 - zap logger [1597967].mp4`. Rename both to the `SLUG` before continuing:

```sh
mv "<downloaded-name>.mp4" "<SLUG>.mp4"
mv "<downloaded-name>.ai-zh.srt" "<SLUG>.ai-zh.srt"
cd ..
```

Verify with `ls video/` — you should have exactly `<SLUG>.mp4` and
`<SLUG>.ai-zh.srt`. If the srt is missing, the cookies were stale; refresh
them and rerun with `--skip-download` added.

## Step 3 — Read `resources/` if present

Explore the current directory. If a `resources/` folder exists, read **every**
file in it — these are the code snippets and slides that accompany the video,
and they are more authoritative than anything read off a video frame.

## Step 4 — Extract frames into `frames/`

The script lives in this skill's `scripts/` folder:

```sh
python3 <skill-dir>/scripts/extract_frames.py \
  "video/<SLUG>.mp4" \
  --title "<SLUG>" \
  --interval 1 \
  --threshold 60 \
  --output "frames"
```

Output: `frames/<SLUG>_HH-MM-SS.jpg` plus `frames/frames.tsv`, a
`filename → timestamp → seconds` index used to line frames up with the SRT.

### extract_frames.py flags

| Flag                   | Default        | What it does                                                                                                                                               |
| ---------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `video` (positional)   | —              | Path to the input mp4                                                                                                                                      |
| `--interval <seconds>` | `10`           | Seconds between sampled frames. Lower for fast-moving slides, higher for talking-head videos                                                               |
| `--threshold <int>`    | `5`            | Perceptual-hash distance below which a frame counts as a duplicate of the last kept frame. **Higher removes more**; `0` keeps everything but exact repeats |
| `--title <text>`       | video filename | Prefix used in frame filenames                                                                                                                             |
| `--output <dir>`       | `frames`       | Output directory                                                                                                                                           |
| `--max-width <px>`     | `1280`         | Downscale wider frames to cut vision-model cost; `0` keeps the original resolution                                                                         |
| `--keep-existing`      | off            | Append to the output directory instead of clearing it first                                                                                                |

Tuning: if slides are being dropped, lower `--threshold` (try `2`) or shorten
`--interval`. If you get hundreds of near-identical frames, raise
`--threshold` to `6`–`8`.

## Step 5 — Read everything

1. Read `frames/frames.tsv` first to get the timeline.
2. Read **every** frame image in `frames/` — none may be skipped. Work in
   timestamp order and in batches so the ordering stays intact. (Must use a GPT Vision model to read and anlayze the image)
3. Read `video/<SLUG>.ai-zh.srt` in full.
4. Cross-check both against `resources/` where it exists.

Frame timestamps and SRT timestamps share the same clock, so use them to
attach each transcript passage to the slide that was on screen.

## Step 6 — Write the notes

Write two files:

**`notes/<SLUG>-teaching-note.md`**

- Refer [Example Teaching Notes](./references/Example_Teaching_Note.md)
- Use the frames/\*.jpg as much as possible (but the repeat frame, don't use too many to confuse user) in the newly created teaching-note.md

## Notes and caveats

- The AI subtitles are auto-generated and get technical terms wrong; trust the
  frames and `resources/` over the transcript for identifiers and API names.
- Re-running step 4 clears `frames/` unless `--keep-existing` is passed.
- Cookies expire quickly. A sudden drop to low-quality formats or missing
  subtitles almost always means stale cookies, not a broken command.
