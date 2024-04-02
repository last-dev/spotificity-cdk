import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def handler(event, context) -> None:
    """
    This Lambda publishes a message to a SNS topic when there are
    no artists in the table being monitored.
    """

    confirm_email_subscription()
    try:
        log.info('Attempting to publish email to SNS topic...')
        topic_arn = os.getenv('SNS_TOPIC_ARN')
        sns = boto3.client('sns')

        response = sns.publish(
            TopicArn=topic_arn,
            Subject='Spotificity: ❌ No Artists Found In List ❌',
            Message='There are no artists currently being monitored. No new music to report!\n Please run Spotificity CLI to add artists to the list.',
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
        log.error(f'Client Error Message: {err.response["Error"]["Message"]}')
        log.error(f'Client Error Code: {err.response["Error"]["Code"]}')
        raise
    else:
        log.info('Successfully retrieved email from AWS Secrets Manager.')
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
