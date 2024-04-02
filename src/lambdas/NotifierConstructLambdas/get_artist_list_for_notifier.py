import logging
import os

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event: dict, context) -> dict:
    """
    Returns a list of all current artists being monitored.
    """

    try:
        ddb = boto3.client('dynamodb')
        table = os.getenv('ARTIST_TABLE_NAME')
        log.info(f'Sending scan request to {table}...')

        response = ddb.scan(
            TableName=table, Select='ALL_ATTRIBUTES', ReturnConsumedCapacity='TOTAL'
        )
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.debug(f'Returned payload: {response}')
        log.debug('Parsing returned payload...')

        if response.get('Error'):
            log.error('Error occurred while trying to scan table. Returning error to client.')
            return {
                'payload': {
                    'status_code': response['ResponseMetadata']['HTTPStatusCode'],
                    'error': response['Error'],
                }
            }
        elif len(response['Items']) == 0:
            log.warning('No artists found. Returning empty list to client.')
            return {'payload': {'status_code': 204, 'artists': []}}
        else:
            log.debug(f'Returned payload: {response}')
            log.info(
                'Successfully received list of artists. Sending list to next task in step function.'
            )

            # Extract out only artist ID and name. Then add all artists into a list of dicts
            current_artists_with_id: list[dict] = [
                {'artist_id': artist['artist_id']['S'], 'artist_name': artist['artist_name']['S']}
                for artist in response['Items']
            ]

            # Extract out only artist name. Then add all artists into a list
            current_artists_names: list[str] = [
                artist['artist_name']['S'] for artist in response['Items']
            ]

            return {
                'payload': {
                    'status_code': 200,
                    'access_token': event,
                    'artists': {
                        'current_artists_names': current_artists_names,
                        'current_artists_with_id': current_artists_with_id,
                    },
                }
            }
