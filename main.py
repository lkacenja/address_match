import argparse
import os.path

import pandas as pd
import numpy as np


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
    voter_address_df = pd.read_csv(voter_address_file)
    polling_place_df = pd.read_csv(polling_place_file)
    state_map = pd.read_csv('./data/metadata/state_map.csv')
    return voter_address_df, polling_place_df, state_map


def address_match(voter_address_df: pd.DataFrame, polling_place_df: pd.DataFrame,
                  state_map: pd.DataFrame) -> pd.DataFrame:
    # Find rows with bad formatting.
    # bad_polling_places = polling_place_df[polling_place_df['Precinct'].isna()]
    # for column in bad_polling_places.columns:
    polling_place_df = polling_place_df[~polling_place_df['Precinct'].isna()].copy()


    state_map['abbreviation'] = state_map['abbreviation'].str.lower()
    state_map['state_name'] = state_map['state_name'].str.lower().replace(' ', '', regex=True)
    state_map['precinct_4'] = state_map['state_name'].str[:4]
    state_map['precinct_3'] = state_map['state_name'].str[:3]
    state_map['precinct'] = np.where(state_map['precinct_3'].duplicated(), state_map['precinct_4'], state_map['precinct_3'])
    state_map = state_map.drop(columns=['precinct_4', 'precinct_3'])
    state_map = state_map.add_prefix('map_')

    polling_place_df[['state_code', 'precinct_id']] = polling_place_df['Precinct'].str.split('-', n=1, expand=True)
    polling_place_df['state_code'] = polling_place_df['state_code'].str.lower()
    polling_place_df = polling_place_df.add_prefix('polling_')
    before_count = len(polling_place_df)
    polling_place_df = polling_place_df.merge(state_map, how='left', left_on='polling_state_code', right_on='map_precinct')
    assert before_count == len(polling_place_df), 'Row expansion occurred after joining polling place and state map.'

    voter_address_df[['state_id', 'precinct_id']] = voter_address_df['Precinct ID'].str.split('-', n=1, expand=True)
    voter_address_df['State'] = voter_address_df['State'].str.lower()
    voter_address_df = voter_address_df.add_prefix('voter_')
    voter_address_df = voter_address_df.merge(polling_place_df, left_on=['voter_State', 'voter_precinct_id'], right_on=['map_abbreviation', 'polling_precinct_id'], how='outer', indicator=True)

    # Prep map.
    # Glue datasets together.


def output_data(output_df: pd.DataFrame) -> None:
    pass


def run_address_match() -> None:
    args = parse_args()
    voter_address_df, polling_place_df, state_map = get_assets(args.voter_address_file, args.polling_place_file)
    output_df = address_match(voter_address_df, polling_place_df, state_map)
    output_data(output_df)


if __name__ == '__main__':
    run_address_match()
