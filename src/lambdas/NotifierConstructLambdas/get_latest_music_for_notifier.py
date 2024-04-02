import logging

import requests
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event: dict, context) -> dict:
    """
    Queries a couple of Spotify's APIs to return back the latest musical releases
    for the artists.
    """

    log.debug(f'Passed in event: {event}')
    access_token: str = event['access_token']
    current_artists: list[dict] = event['artists']['current_artists_with_id']
    latest_music: list[dict] = []

    # For each artist, fetch the latest musical releases
    log.info('Starting iteration through artist list...')
    for artist in current_artists:
        artist_id: str = artist['artist_id']
        artist_name: str = artist['artist_name']

        # Get latest musical releases
        last_album_details: dict = get_latest_album(artist_id, artist_name, access_token)
        last_single_details: dict = get_latest_single(artist_id, artist_name, access_token)

        # Add to list of latest musical releases
        log.info(f'Adding {artist_name}\'s information to return payload...')
        latest_music.append(
            {
                'artist_id': artist_id,
                'artist_name': artist_name,
                'last_album_details': last_album_details,
                'last_single_details': last_single_details,
            }
        )

    # Return list of latest musical releases
    log.info('Successfully retrieved latest musical releases for all artists.')
    log.debug(f'Returning payload: {latest_music}')
    return {'latest_music': latest_music}


def get_latest_album(artist_id: str, artist_name: str, access_token: str) -> dict:
    """
    Queries the Spotify API to return the last album released by the
    artist.
    """

    endpoint: str = f'https://api.spotify.com/v1/artists/{artist_id}/albums'

    try:
        log.info(f'Initiating GET request for the {artist_name}\'s last album...')

        response = requests.get(
            url=endpoint,
            params={'limit': 1, 'offset': 0, 'include_groups': 'album', 'market': 'US'},
            headers={'Authorization': f'Bearer {access_token}'},
        )
        response.raise_for_status()
    except HTTPError as err:
        log.error(f'HTTP Error occurred: {err}')
        raise
    except Exception as err:
        log.error(f'Other error occurred: {err}')
        raise
    else:
        log.debug(f'Returned payload: {response.json()}')
        log.debug('Parsing returned payload...')
        album_search_results: dict = response.json()

        # Catch any errors that may occur when searching for the last album
        if album_search_results.get('error'):
            log.error(f'Error occurred: {album_search_results["error"]}')
            raise Exception(f'Error occurred: {album_search_results["error"]}')
        elif len(album_search_results['items']) == 0:
            log.warning(f'No albums found for {artist_name}. Returning empty details.')
            return {'last_album_name': '', 'last_album_release_date': '', 'last_album_artists': []}

        # Extract out the last album's details
        last_album: dict = album_search_results['items'][0]
        last_album_artists: list[str] = [artist['name'] for artist in last_album['artists']]

        log.info('Successfully retrieved last album details.')
        return {
            'last_album_name': last_album['name'],
            'last_album_release_date': last_album['release_date'],
            'last_album_artists': last_album_artists,
        }


def get_latest_single(artist_id: str, artist_name: str, access_token: str) -> dict:
    """
    Queries the Spotify API to return the last single released by the
    artist.
    """

    endpoint: str = f'https://api.spotify.com/v1/artists/{artist_id}/albums'

    try:
        log.info(f'Initiating GET request for the {artist_name}\'s last single...')

        response = requests.get(
            url=endpoint,
            params={'limit': 1, 'offset': 0, 'include_groups': 'single', 'market': 'US'},
            headers={'Authorization': f'Bearer {access_token}'},
        )
        response.raise_for_status()
    except HTTPError as err:
        log.error(f'HTTP Error occurred: {err}')
        raise
    except Exception as err:
        log.error(f'Other error occurred: {err}')
        raise
    else:
        log.debug(f'Returned payload: {response.json()}')
        log.debug('Parsing returned payload...')
        single_search_results: dict = response.json()

        # Catch any errors that may occur when searching for the last single
        if single_search_results.get('error'):
            log.error(f'Error occurred: {single_search_results["error"]}')
            raise Exception(f'Error occurred: {single_search_results["error"]}')
        elif len(single_search_results['items']) == 0:
            log.warning(f'No singles found for {artist_name}. Returning empty details.')
            return {
                'last_single_name': '',
                'last_single_release_date': '',
                'last_single_artists': [],
            }

        # Extract out the last single's details
        last_single: dict = single_search_results['items'][0]
        last_single_artists: list[str] = [artist['name'] for artist in last_single['artists']]

        log.info('Successfully retrieved last single details.')
        return {
            'last_single_name': last_single['name'],
            'last_single_release_date': last_single['release_date'],
            'last_single_artists': last_single_artists,
        }


"""
Unfortunately it turns out Spotify does not have a way to filter by songs the artist is featured on.
Until then, this will be commented out. 
"""

# def get_latest_tracks_artist_featured_on(artist_name: str, access_token: str) -> dict:
#     """
#     Queries the Spotify API to return the last track the artist was
#     featured on
#     """

#     endpoint: str = 'https://api.spotify.com/v1/search'

#     try:
#         print(f'Initiating GET request for the last track {artist_name} was featured on...')

#         response = requests.get(
#             url=endpoint,
#             params={
#                 'q': f'featured:{artist_name}',
#                 'type': 'track',
#                 'limit': 100,
#                 'offset': 0,
#                 'market': 'US'
#             },
#             headers={
#                 'Authorization': f'Bearer {access_token}'
#             }
#         )

#         # Catch any HTTP errors
#         response.raise_for_status()
#     except HTTPError as err:
#         print(f'HTTP Error occurred: {err}')
#         raise
#     except Exception as err:
#         print(f'Other error occurred: {err}')
#         raise
#     else:
#         print('Parsing JSON...')

#         # Sort the featured tracks by release date (descending)
#         featured_tracks: dict = response.json()
#         sorted_tracks: list = sorted(
#             featured_tracks['tracks']['items'],
#             key=lambda x: x['album']['release_date'],
#             reverse=True
#         )

#         # Only keep songs where artist is featured
#         songs: list = [
#             track for track in sorted_tracks
#             if any(artist['name'] == artist_name and artist != track['artists'][0] for artist in track['artists'])
#         ]

#         return {
#             'last_2_featured_tracks': songs[:2]
#         }
