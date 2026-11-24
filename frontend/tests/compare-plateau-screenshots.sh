#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 3 ]]; then
  printf 'Usage: bash %s BASELINE_DIR CANDIDATE_DIR COMPARISON_DIR\n' "$0" >&2
  exit 2
fi

before=$1
after=$2
output=$3
mkdir -p "$output"

for page in home assessment admin; do
  for width in 1440 390; do
    file="$page-$width.png"
    height=$([[ $width == 1440 ]] && printf 1000 || printf 844)
    for source in "$before/$file" "$after/$file"; do
      [[ -f $source ]]
      dimensions=$(identify -format '%wx%h' "$source")
      if [[ $dimensions != "${width}x${height}" ]]; then
        printf '%s: expected %sx%s, received %s\n' "$source" "$width" "$height" "$dimensions" >&2
        exit 1
      fi
    done
    convert "$before/$file" -background '#e8e0d6' -gravity northwest -splice 0x32 \
      -font DejaVu-Sans -pointsize 14 -fill '#2b2725' -annotate +14+21 'BEFORE  /  da39acc' \
      \( "$after/$file" -background '#e8e0d6' -gravity northwest -splice 0x32 \
      -font DejaVu-Sans -pointsize 14 -fill '#2b2725' -annotate +14+21 'AFTER  /  editorial' \) \
      +append "$output/$file"
  done
done
