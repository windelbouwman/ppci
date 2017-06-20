#!/bin/bash

# Create a video of the development using the gource program:

gource --file-filter examples --viewport 1280x720 \
  --seconds-per-day 0.1 \
  --title "ppci development" \
  --elasticity 0.02 \
  --highlight-dirs \
  --highlight-users \
  --stop-at-end \
  --date-format %F \
  --output-framerate 25 \
  --path .. --output-ppm-stream - | ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libvpx -b 10000K gource.webm
