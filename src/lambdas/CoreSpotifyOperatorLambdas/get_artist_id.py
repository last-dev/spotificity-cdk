import json
import logging

import requests
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event: dict, context) -> dict:
    """
    Queries the Spotify `Search` API for the artist's Spotify ID.
    """

    log.debug(f'Received event: {event}')
    log.info(f'Passed in artist payload: {event["body"]}')
    payload: dict = json.loads(event['body'])
    artist_name: str = payload['artist_name']
    access_token: str = payload['access_token']
    endpoint: str = 'https://api.spotify.com/v1/search'

    try:
        log.info('Initiating GET request for artist ID...')

        response = requests.get(
            url=endpoint,
            params={'q': artist_name, 'type': 'artist', 'limit': 5, 'offset': 0, 'market': 'US'},
            headers={'Authorization': f'Bearer {access_token}'},
        )
        response.raise_for_status()
    except HTTPError as err:
        log.error(f'HTTP Error occurred: {err}')
        log.warning(f'Unsuccessful retrieval from Spotify `Search` API. Returning error to client.')
        return {
            'statusCode': err.response.status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': err.response.text, 'error_type': 'HTTP'}),
        }
    else:
        log.info(
            f'Successfully received response from Spotify `Search` API. HTTP Status code: {response.status_code}'
        )
        log.debug(f'Returned Payload: {response.json()}')
        artist_search_results: dict = response.json()

        log.info(
            'Successfully retrieved list of artists with their respective Spotify IDs. Returning list to client.'
        )
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(
                {'artistSearchResultsList': artist_search_results['artists']['items']}
            ),
        }
