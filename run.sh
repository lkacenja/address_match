#!/usr/bin/env bash

# Should provide the directory where this script lives in most cases.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# The name of our image from the Gitlab Container Registry.
IMAGE_NAME="address-match"

# Build the image with our special build args.
# These matter more on Jenkins, but need to be placeheld anyway.
docker image build -t $IMAGE_NAME .


# Run the container in a disposable manner.
# Add a volume to the current working dir.
docker run --rm -it -v $SCRIPT_DIR:/workspace $IMAGE_NAME bash
