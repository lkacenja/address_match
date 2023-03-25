# Address Match
A script for matching voter address information with polling place address information.
The script currently does some normalization on both input datasets. Then uses a list of full state name and abbreviations to join our datasets.

## Usage
To run the script, build the docker image and then execute it via `docker run`.
1. `docker image build -t address-match .`
2. `docker run --rm -it -v <path to repo>:/workspace address-match python main.py <path to voter address data> <path to pollling place address data>`

Additionally a bash script for local development is provided. See `run.sh`.

## Todo
Due to time constraints, we took a strategy of marking questionable rows as needing review.
There are several flaws in the data that could be fixed within this script. Here is a running log of them.
* Fix polling place rows, that have truncated column values.
* Fix polling state precinct id mismatches.
* Normalize address columns for output, voting and polling files currently have different formats.
