import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event: dict, context) -> dict:
    """
    Adds a new artist to the "Monitored Artists" DynamoDB table
    """

    log.debug(f'Received event: {event}')
    log.info(f'Passed in artist payload: {event["body"]}')
    payload: dict = json.loads(event['body'])
    artist_name: str = payload['artist_name']
    artist_id: str = payload['artist_id']

    try:
        ddb = boto3.client('dynamodb')
        table = os.getenv('ARTIST_TABLE_NAME')
        log.info(f'Attempting to add {artist_name} to {table}...')

        response = ddb.put_item(
            TableName=table,
            Item={'artist_id': {'S': artist_id}, 'artist_name': {'S': artist_name}},
            ReturnConsumedCapacity='TOTAL',
        )
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        log.warning('Error occurred while trying to add artist. Returning error message to client.')
        return {
            'statusCode': err.response['ResponseMetadata']['HTTPStatusCode'],
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': err.response['Error'], 'error_type': 'Client'}),
        }
    else:
        log.debug(f'Returned payload: {response}')
        log.info(f'PUT request successful. Now monitoring {artist_name}. Returning payload to client.')
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'returned_response_from_put': response}),
        }
