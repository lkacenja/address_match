import argparse
import os.path

import numpy as np
import pandas as pd

"""
Joins voter and polling address data.
"""


def parse_args() -> argparse.Namespace:
    """
    Parses command line args.

    Returns
    -------
    args: argparse.Namespace
      The args as handled by the python core argparse module.
    """
    parser = argparse.ArgumentParser(
        prog='Address Matcher',
        description='Matches voter addresses to polling places via precinct name.')
    docker_disclaimer = 'Must be exposed to the container via volume.'
    parser.add_argument('voter_address_file', help='The path to the voter address file. ' + docker_disclaimer)
    parser.add_argument('polling_place_file', help='The path to the polling place file. ' + docker_disclaimer)
    return parser.parse_args()


def get_assets(voter_address_file: str, polling_place_file: str) -> tuple:
    """
    Gets and validates our file assets as dataframes.

    Parameters
    ----------
    voter_address_file: str
      The path to the voter address file.
    polling_place_file: str
      The path to the polling place address file.

    Returns
    -------
    (pd.Dataframe, pd.Dataframe)
        The voter_address and polling_place dataframes.
    """
    # Make sure files exist and provide a helpful message if not.
    if not os.path.exists(voter_address_file):
        raise RuntimeError('Provided voter_address_file, "{}" does not seem to exist.'.format(voter_address_file))
    if not os.path.exists(polling_place_file):
        raise RuntimeError('Provided polling_place_file, "{}" does not seem to exist.'.format(polling_place_file))
    voter_address_df = pd.read_csv(voter_address_file)
    polling_place_df = pd.read_csv(polling_place_file)
    # todo verify the integrity of both input files by checking column names and shape.
    return voter_address_df, polling_place_df


def merge_address_files(voter_address_df: pd.DataFrame, polling_place_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges the voter and polling place address data.

    Parameters
    ----------
    voter_address_df: pd.DataFrame
      A dataframe containing the voter address information.
    polling_place_df: pd.DataFrame
      A dataframe containing the polling place address information.

    Notes
    -----
    This process could do much more normalization of the data.
    Given time constraints, we simply flag bad rows for review.

    Todo:
    - Fix polling place rows, that have truncated column values.
    - Fix polling state precinct id mismatches.

    Returns
    -------
    The merged dataset.
    """
    # Some polling place data is truncated.
    # As a result we are missing "Precinct".
    # For now, mark them as malformed so the join will fail predictably.
    # todo Later we should attempt to fix them.
    na_precinct = polling_place_df['Precinct'].isna()
    polling_with_precinct_df = polling_place_df[~na_precinct].copy()
    polling_without_precinct_df = polling_place_df[na_precinct].copy()
    polling_without_precinct_df['Precinct'] = 'malformed-malformed'
    # Split up state and zip where possible.
    polling_with_precinct_df[['state_abbreviation', 'zip']] = polling_with_precinct_df['State/ZIP'].str.split(' ', n=1, expand=True)
    polling_with_precinct_df['zip'] = polling_with_precinct_df['zip'].astype(str)
    # Put them back together again.
    polling_place_df = pd.concat([polling_with_precinct_df, polling_without_precinct_df])
    # Current polling place "Precinct" column is formatted [state code]-[precinct id].
    # Split that column into two columns.
    polling_place_df[['state_code', 'precinct_id']] = polling_place_df['Precinct'].str.split('-', n=1, expand=True)
    polling_place_df['precinct_id'] = polling_place_df['precinct_id'].astype(str)
    # Prep for joining.
    # For consistency lowercase state.
    polling_place_df['state_abbreviation'] = polling_place_df['state_abbreviation'].str.lower()
    polling_place_df = polling_place_df.add_prefix('polling_')

    # Current polling place "Precinct ID" column is formatted [state id numeric]-[precinct id].
    # Split that column into two columns.
    voter_address_df[['state_id', 'precinct_id']] = voter_address_df['Precinct ID'].str.split('-', n=1, expand=True)
    voter_address_df['precinct_id'] = voter_address_df['precinct_id'].astype(str)
    # Prep for joining.
    # For consistency lowercase state.
    voter_address_df['State'] = voter_address_df['State'].str.lower()
    voter_address_df = voter_address_df.add_prefix('voter_')
    # Perform an outer join and add an indicator.
    # We use the indicator to determine non-matches.
    voter_address_df = voter_address_df.merge(polling_place_df, left_on=['voter_State', 'voter_precinct_id'],
                                              right_on=['polling_state_abbreviation', 'polling_precinct_id'],
                                              how='outer', indicator=True)
    # We aren't concerned with polling places that have no match at the moment.
    # Cut them off.
    voter_address_df = voter_address_df[voter_address_df['_merge'] != 'right_only']
    # Flag all rows that had no match.
    # @todo In the future we may be able to automate cleaning these rows.
    voter_address_df['requires_investigation'] = np.where(voter_address_df['_merge'] == 'left_only', True, False)
    # Normalize voter state.
    voter_address_df['voter_State'] = voter_address_df['voter_State'].str.upper()
    voter_address_df['polling_state_abbreviation'] = voter_address_df['polling_state_abbreviation'].str.upper()
    # Create a renaming map for our output.
    output_columns = {
        'voter_Street': 'voter_street',
        'voter_Apt': 'voter_apt',
        'voter_City': 'voter_city',
        'voter_State': 'voter_state',
        'voter_Zip': 'voter_zip',
        'polling_Street': 'polling_street',
        'polling_City': 'polling_city',
        'polling_state_abbreviation': 'polling_state',
        'polling_zip': 'polling_state_zip',
        'polling_Country': 'polling_country',
        'polling_precinct_id': 'polling_precinct_id',
        'requires_investigation': 'requires_investigation',
    }
    # Select the columns we want.
    voter_address_df = voter_address_df[output_columns.keys()]
    # Rename the columns consistently.
    voter_address_df = voter_address_df.rename(columns=output_columns)
    return voter_address_df


def output_data(output_df: pd.DataFrame) -> None:
    """
    Outputs our data.

    Notes
    -----
    This is meant to be a leaping off point.
    In the future this function could do something more sophisticated.
    For now, it simply outputs the csv data to stdout.

    Parameters
    ----------
    output_df: pd.Dataframe
        The data to output.
    """
    print(output_df.to_csv(index=False))


def run_address_match() -> None:
    """
    Runs all of our steps to match voter and polling place addresses.
    """
    args = parse_args()
    voter_address_df, polling_place_df = get_assets(args.voter_address_file, args.polling_place_file)
    output_df = merge_address_files(voter_address_df, polling_place_df)
    output_data(output_df)


if __name__ == '__main__':
    run_address_match()
