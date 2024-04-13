import base64
import json
import logging

import boto3
import requests
from botocore.exceptions import ClientError
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event, context) -> dict:
    """
    Fetches an access token from the Spotify `/token/` API.
    This access token is needed for all future Spotify API calls.
    """

    # Print event to log which source invoked this lambda function
    log.info(f'Event: {event}')

    try:
        log.info('Attempting to pull Spotify client credentials from AWS Secrets Manager...')
        ssm = boto3.client('secretsmanager')

        response = ssm.get_secret_value(SecretId='SpotifySecrets')
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.info('Successfully retrieved Spotify client credentials from AWS Secrets Manager')

        # Extract client creds from returned payload
        client_creds = json.loads(response['SecretString'])
        client_id = client_creds['SPOTIFY_CLIENT_ID']
        client_secret = client_creds['SPOTIFY_CLIENT_SECRET']

        # Request access token
        log.debug("Entering request_token function...")
        access_token = request_token(client_id, client_secret)

        # Return appropriate format based on lambda invocation source
        # If invoked from API Gateway, return HTTP response
        if 'httpMethod' in event:
            log.debug('Lambda invoked from API Gateway. Returning HTTP response...')
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'access_token': access_token}),
            }
        else:
            log.debug('Lambda invoked by another Lambda function. Returning payload...')
            return {'access_token': access_token}


def request_token(client_id: str, client_secret: str) -> str:
    """
    Sends POST request to Spotify Token API to get an access token
    """

    client_creds: str = f'{client_id}:{client_secret}'
    endpoint: str = 'https://accounts.spotify.com/api/token'

    try:
        log.info("Initiating POST request for Access Token...")

        response = requests.post(
            url=endpoint,
            headers={
                # Encode the client credentials to base64
                'Authorization': f'Basic {base64.b64encode(client_creds.encode()).decode()}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={'grant_type': 'client_credentials'},
        )
        response.raise_for_status()
    except HTTPError as err:
        log.error(f'HTTP Error occurred: {err}')
        raise
    else:
        log.info(f'Successfully received response from Spotify Token API. HTTP Status code: {response.status_code}')
        log.debug(f'Returned Payload: {response.json()}')

        # Check if error occurred while attempting to retrieve access token. If not, return token
        if response.json().get('error'):
            log.error(f'Unsuccessful response from Spotify Token API. Error: {response.json()["error"]}')
            raise Exception(f'Error: {response.json()["error"]}')
        else:
            log.debug("Exiting request_token function...")
            return response.json()['access_token']
