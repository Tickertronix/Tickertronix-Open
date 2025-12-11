#!/bin/bash -e

# Use the previous stage's rootfs as the starting point for this stage.
if [ ! -d "${ROOTFS_DIR}" ]; then
  copy_previous
fi
