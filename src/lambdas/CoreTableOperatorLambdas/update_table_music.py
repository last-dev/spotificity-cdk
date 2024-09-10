import logging
import os

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event: dict, context) -> dict:
    """
    Handler for Lambda that will update the attributes for each
    artist in the "Monitored Artists" DynamoDB table with the latest musical releases
    """

    log.info(f'Passed in artist payload: {event}')
    artist_name: str = event['artist_name']
    artist_id: str = event['artist_id']
    last_album_details: dict = event['last_album_details']
    last_single_details: dict = event['last_single_details']

    try:
        ddb = boto3.client('dynamodb')
        table = os.getenv('ARTIST_TABLE_NAME')
        log.info(f'Initiating PUT request to update {table} with {artist_name}\'s latest releases...')

        response = ddb.update_item(
            TableName=table,
            Key={'artist_id': {'S': artist_id}},
            UpdateExpression='SET last_album_details = :last_album_details, last_single_details = :last_single_details',
            ExpressionAttributeValues={
                ':last_album_details': {
                    'M': {
                        'last_album_name': {'S': last_album_details['last_album_name']},
                        'last_album_release_date': {'S': last_album_details['last_album_release_date']},
                        'last_album_artists': {'L': [{'S': artist} for artist in last_album_details['last_album_artists']]},
                    }
                },
                ':last_single_details': {
                    'M': {
                        'last_single_name': {'S': last_single_details['last_single_name']},
                        'last_single_release_date': {'S': last_single_details['last_single_release_date']},
                        'last_single_artists': {'L': [{'S': artist} for artist in last_single_details['last_single_artists']]},
                    }
                },
            },
            ReturnConsumedCapacity='TOTAL',
            ReturnValues='UPDATED_OLD',
        )
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.debug(f'Returned payload: {response}')
        log.info(f'PUT request successful. {artist_name}\'s latest releases have been updated in {table}.')

        return {'statusCode': 200, 'payload': {'returnPayloadFromUpdate': response}}
