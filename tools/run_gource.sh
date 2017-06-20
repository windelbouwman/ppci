#!/bin/bash

# Create a video of the development using the gource program:

gource --file-filter examples \
  --seconds-per-day 0.1 \
  --title "ppci development" \
  --elasticity 0.02 \
  --highlight-dirs \
  --highlight-users \
  --date-format %F \
  --path ..

