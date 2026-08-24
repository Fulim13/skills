#!/usr/bin/env bash

set -euo pipefail

URL="$1"
SLUG="${2:-}"
COOKIE="/mnt/c/Users/fulim/Downloads/cookies.txt"

# Without a slug, yt-dlp names files after the Bilibili title.
OUTPUT_ARGS=()

if [ -n "$SLUG" ]; then
    OUTPUT_ARGS=(-o "$SLUG.%(ext)s")
fi

FORMATS=(
  "30080+30280"
  "30064+30280"
  "30032+30280"
  "30016+30280"
)

for FORMAT in "${FORMATS[@]}"; do
    echo "Trying $FORMAT..."

    if yt-dlp \
        --cookies "$COOKIE" \
        -f "$FORMAT" \
        "${OUTPUT_ARGS[@]}" \
        --write-subs \
        --sub-langs ai-zh \
        --sub-format srt \
        --merge-output-format mp4 \
        "$URL"
    then
        echo "Success with $FORMAT"
        exit 0
    fi

    echo "Failed: $FORMAT"
done

echo "All formats failed."
exit 1
