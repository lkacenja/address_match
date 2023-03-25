import argparse
import os.path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='Address Matcher',
        description='Matches voter addresses to polling places via precinct name.')
    docker_disclaimer = 'Must be exposed to the container via volume.'
    parser.add_argument('voter_address_file', help='The path to the voter address file. ' + docker_disclaimer)
    parser.add_argument('polling_place_file', help='The path to the polling place file. ' + docker_disclaimer)
    return parser.parse_args()


def get_assets(voter_address_file: str, polling_place_file: str) -> tuple:
    if not os.path.exists(voter_address_file):
        raise RuntimeError('Provided voter_address_file, "{}" does not seem to exist.'.format(voter_address_file))
    if not os.path.exists(polling_place_file):
        raise RuntimeError('Provided polling_place_file, "{}" does not seem to exist.'.format(polling_place_file))
    voter_address_df = pd.read_csv(voter_address_file, low_memory=False)
    polling_place_df = pd.read_csv(polling_place_file, low_memory=False)
    return voter_address_df, polling_place_df


def address_match(voter_address_df: pd.DataFrame, polling_place_df: pd.DataFrame) -> pd.DataFrame:
    pass


def output_data(output_df: pd.DataFrame) -> None:
    pass


def run_address_match() -> None:
    args = parse_args()
    voter_address_df, polling_place_df = get_assets(args.voter_address_file, args.polling_place_file)
    output_df = address_match(voter_address_df, polling_place_df)
    output_data(output_df)


if __name__ == '__main__':
    run_address_match()
