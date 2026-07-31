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
├── resources/      # OPTIONAL, user-supplied code snippets and slides
└── notes/
    ├── assets/<slug>/          # deduplicated frames + frames.tsv (step 4)
    └── <SLUG>-teaching-note.md # teaching note (step 6)
```

`SLUG` below means a short name for the video, formed as
`<episode-number>-<topic-in-english>`, e.g. `168-zap-logger`. It becomes a
filename, so use only `a`–`z`, `0`–`9` and hyphens — no spaces, no Chinese
characters, no uppercase. Pick it once in step 1 and reuse it everywhere;
`<SLUG>` and `<slug>` in this document mean the same string.

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

Ask the user for the video URL if it was not given. Then propose a `SLUG`
derived from the video title using the rule above, and confirm it with the
user before downloading anything.

## Step 2 — Download into `video/`

Download from inside `video/` so the mp4 and the srt both land there:

```sh
mkdir -p video && cd video
bash "<skill-dir>/scripts/download_video.sh" "<bilibili-url>" "<SLUG>"
```

### What `download_video.sh` runs

| Flag                        | What it does                                                                                                                                                        |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--cookies <file>`          | Netscape-format cookie jar; required for logged-in quality and AI subtitles                                                                                         |
| `-f "<video>+<audio>"`      | Explicit format ids, tried in this order until one succeeds: `30080` (1080p), `30064` (720p), `30032` (480p), `30016` (360p), each paired with `30280` (192k audio) |
| `--write-subs`              | Write the subtitle track to a file next to the video                                                                                                                |
| `--sub-langs ai-zh`         | Bilibili's AI-generated Chinese subtitles                                                                                                                           |
| `--sub-format srt`          | Preferred subtitle format                                                                                                                                           |
| `--merge-output-format mp4` | Remux the separate video and audio streams into one mp4                                                                                                             |

Reference flags for when a download misbehaves (not part of the standard run):
`-F` lists the format ids available for that video, `--list-subs` lists its
subtitle tracks, `--skip-download` fetches subtitles only.

### Verify

The second argument names the files, so no renaming is needed:

```sh
ls -l
cd ..
```

You should have exactly `<SLUG>.mp4` and
`<SLUG>.ai-zh.srt`. If the srt is missing, the cookies were stale; refresh
them and rerun with `--skip-download` added.

## Step 3 — Read `resources/` if present

Explore the current directory. If a `resources/` folder exists, read **every**
file in it — these are the code snippets and slides that accompany the video,
and they are more authoritative than anything read off a video frame.

## Step 4 — Extract frames into `notes/assets/<slug>`

The script lives in this skill's `scripts/` folder:

```sh
mkdir -p notes
python3 <skill-dir>/scripts/extract_frames.py \
  "video/<SLUG>.mp4" \
  --title "<SLUG>" \
  --interval 1 \
  --threshold 50 \
  --output "notes/assets/<slug>"
```

Output: `notes/assets/<slug>/<SLUG>_HH-MM-SS.jpg` plus
`notes/assets/<slug>/frames.tsv`, a
`filename → timestamp → seconds` index used to line frames up with the SRT.

### extract_frames.py flags

| Flag                   | Default        | What it does                                                                                                                                                           |
| ---------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `video` (positional)   | —              | Path to the input mp4                                                                                                                                                  |
| `--interval <seconds>` | `10`           | Seconds between sampled frames. Lower for fast-moving slides, higher for talking-head videos                                                                           |
| `--threshold <int>`    | `50`           | Perceptual-hash distance (`0`–`256`) below which a frame counts as a duplicate of the last kept frame. **Higher removes more**; `0` keeps everything but exact repeats |
| `--title <text>`       | video filename | Prefix used in frame filenames                                                                                                                                         |
| `--output <dir>`       | `frames`       | Output directory                                                                                                                                                       |
| `--max-width <px>`     | `1280`         | Downscale wider frames to cut vision-model cost; `0` keeps the original resolution                                                                                     |

Tuning: if slides are being dropped, lower `--threshold` (try `30`–`40`) or
shorten `--interval`. If you get hundreds of near-identical frames, raise
`--threshold` to `60`–`70`.

## Step 5 — Read everything

1. Read `notes/assets/<slug>/frames.tsv` first to get the timeline.
2. Read **every** frame image in `notes/assets/<slug>/` — none may be skipped. Work in
   timestamp order and in batches so the ordering stays intact. (Must read and analyze the image)
3. Read `video/<SLUG>.ai-zh.srt` in full.
4. Cross-check both against `resources/` where it exists.

Frame timestamps and SRT timestamps share the same clock, so use them to
attach each transcript passage to the slide that was on screen.

## Step 6 — Write the teaching notes

Write one files: **`notes/<SLUG>-teaching-note.md`**

- Follow [Example Teaching Notes](./references/Example_Teaching_Note.md) for the outline and note constructions, the content is just the example
- Embed a frame (from `./assets/<slug>/*.jpg`) in the newly created teaching-note.md as much as possible — a slide, a code screen, a terminal result. For Duplicated frame, don't put it. Link them as `./assets/<slug>/<file>.jpg`, relative to the note itself.

## Step 7 - Clean up all the unused image

- Clean up all the unused image that are not used in the newly created `<SLUG>-teaching-note.md`

## Notes and caveats

- The AI subtitles are auto-generated and get technical terms wrong; trust the
  frames and `resources/` over the transcript for identifiers and API names.
- Cookies expire quickly. A sudden drop to low-quality formats or missing
  subtitles almost always means stale cookies, not a broken command.
