import json
import logging
import os
from random import choice

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event, context) -> None:
    """
    This Lambda publishes a message to a SNS topic with any new
    musical releases! If there are no changes, we let the user know
    there are no updates.
    """

    log.debug(f'Event: {event}')
    confirm_email_subscription()

    # Check if passed in list is empty. If so, send email that there is no music to report
    if not event:
        log.info('No new music to report. Sending email...')
        send_no_music_email()
    else:
        log.info('New music to report. Sending email...')
        send_email_with_new_music(event)


def send_no_music_email() -> None:
    """
    This function sends an email to the user that there is no new music
    to report.
    """

    try:
        log.debug('Attempting to publish email to SNS topic...')
        topic_arn = os.getenv('SNS_TOPIC_ARN')
        sns = boto3.client('sns')

        response = sns.publish(
            TopicArn=topic_arn,
            Subject='Spotificity: No New Music to Report 😔',
            Message='There is no new music to report! We\'ll check back in next week!',
        )
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.info('Successfully published email to SNS topic.')
        log.debug(f'Published message ID is: {response["MessageId"]}')


def send_email_with_new_music(event: list) -> None:
    """
    This function sends an email to the user that there is new music
    to report.
    """

    greetings = [
        'Hello',
        'Hi',
        'Hey',
        'Greetings',
        'Salutations',
        'Howdy',
        'Yo',
        "What's up",
        'Hola',
        'Bonjour',
        'Konnichiwa',
        'Namaste',
    ]

    # Format artist names into a string
    artists: list[str] = [artist['artist_name'] for artist in event]
    artists_str = ', '.join(artist for artist in artists)
    log.debug(f'Formatted artist names into a string: {artists_str}')

    # Format new music into a string
    email_list_of_strings: list[str] = []
    for index, artist in enumerate(event, start=1):
        artist_name = artist['artist_name']
        last_album_name = artist['last_album_details']['last_album_name']
        last_single_name = artist['last_single_details']['last_single_name']
        last_album_release_date = artist['last_album_details']['last_album_release_date']
        last_single_release_date = artist['last_single_details']['last_single_release_date']

        if artist.get('last_album_details'):
            email_list_of_strings.append(
                f'{index}. \n\t{artist_name} dropped "{last_album_name}" on {last_album_release_date}.'
            )
        elif artist.get('last_single_details'):
            email_list_of_strings.append(
                f'{index}. \n\t{artist_name} dropped "{last_single_name}" on {last_single_release_date}.'
            )
    log.debug(f'Formatted new music into a string: {email_list_of_strings}')

    # Join all strings together to create one long string for the email
    new_music_str = '\n'.join(email_list_of_strings)

    try:
        log.debug('Attempting to publish email to SNS topic...')
        topic_arn = os.getenv('SNS_TOPIC_ARN')
        sns = boto3.client('sns')

        response = sns.publish(
            TopicArn=topic_arn,
            Subject='Spotificity: 🎶 New Music to Report! 🎶',
            Message=f"""{choice(greetings)}!
            
There are {len(event)} artists with new music! Artists that dropped: {artists_str}

Here is the latest:\n
{new_music_str}
            """,
        )
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.info('Successfully published email to SNS topic.')
        log.debug(f'Published message ID is: {response["MessageId"]}')


def confirm_email_subscription() -> None:
    """
    This function checks to see if my email is already subscribed to the
    SNS topic. If not, it will raise an exception. I'll manually confirm it
    in the AWS Console
    """

    log.info('Checking to see if my email is already subscribed...')

    try:
        log.debug('Attempting to pull my email from AWS Secrets Manager...')

        ssm = boto3.client('secretsmanager')
        response = ssm.get_secret_value(SecretId='EmailSecret')
    except ClientError as err:
        log.error(f'Client Error: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.info('Successfully retrieved email from AWS Secrets Manager.')

        # Extract email from returned payload
        email_secret_payload: dict = json.loads(response['SecretString'])
        my_email: str = email_secret_payload['MY_EMAIL']

    # Check if my email is already subscribed to the SNS topic
    try:
        log.info('Pulling list of subscriptions from SNS topic...')

        topic_arn = os.getenv('SNS_TOPIC_ARN')
        sns = boto3.client('sns')
        response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
    except ClientError as err:
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.info('Successfully pulled list of subscriptions from SNS topic.')
        log.info('Checking to see if my email is already subscribed...')
        subscriptions: list[dict] = response['Subscriptions']
        for subscription in subscriptions:
            if subscription['Endpoint'] == my_email:
                log.info('My email is already subscribed to the SNS topic.')
            else:
                log.error('My email is not subscribed to the SNS topic.')
                raise Exception('My email is not subscribed to the SNS topic.')
