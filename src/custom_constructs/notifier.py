from aws_cdk import Duration
from aws_cdk.aws_dynamodb import TableV2
from aws_cdk.aws_ec2 import SubnetSelection, SubnetType
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import SfnStateMachine
from aws_cdk.aws_iam import Effect, PolicyStatement
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime
from aws_cdk.aws_logs import LogGroup, RetentionDays
from aws_cdk.aws_secretsmanager import Secret
from aws_cdk.aws_sns import Topic
from aws_cdk.aws_stepfunctions import Choice, Condition, StateMachine
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct

from ..constants import AwsAccount
from ..helpers.helpers import generate_name, get_removal_policy
from ..stacks.vpc_stack import VpcStack


class NotifierConstruct(Construct):
    """
    Custom construct for all resources that will enable the
    app to email me every week with any new music that is released
    by any of the artists I follow.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        account: AwsAccount,
        artist_table: TableV2,
        requests_layer: LayerVersion,
        access_token_lambda: Function,
        vpc_stack: VpcStack
    ) -> None:
        super().__init__(scope, id)

        # All Lambdas throughout our StepFunction
        get_artists_list_lambda_name = generate_name('GetArtistsListFor-ForNotifier', account)
        _fetch_artists_list_lambda = Function(
            self,
            get_artists_list_lambda_name,
            description='Pulls the current list of artists being monitored',
            function_name=get_artists_list_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/NotifierConstructLambdas'),
            handler='get_artist_list_for_notifier.handler',
            layers=[requests_layer],
            environment={'ARTIST_TABLE_NAME': artist_table.table_name},
            timeout=Duration.seconds(10),
            log_group=LogGroup(
                self, 'NotifierFetchArtistsLogGroup',
                retention=RetentionDays.ONE_YEAR,
                removal_policy=get_removal_policy(account.stage)
            ),
            security_groups=[vpc_stack.lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        artist_table.grant_read_data(_fetch_artists_list_lambda)

        _topic = Topic(self, 'NotifierTopic', topic_name='SpotificityNotifierTopic')

        email_if_no_artists_lambda_name = generate_name('MessageIfNoArtistsLambda', account)
        _email_if_no_artists_lambda = Function(
            self,
            email_if_no_artists_lambda_name,
            description='Publishes a message to a SNS topic if there are currently no artists in the table',
            function_name=email_if_no_artists_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            timeout=Duration.seconds(5),
            code=Code.from_asset('src/lambdas/NotifierConstructLambdas'),
            handler='message_if_no_artists.handler',
            environment={'SNS_TOPIC_ARN': _topic.topic_arn},
            log_group=LogGroup(
                self, 'NotifierMessageIfNoArtistsLogGroup',
                retention=RetentionDays.ONE_YEAR,
                removal_policy=get_removal_policy(account.stage)
            ),
            security_groups=[vpc_stack.lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        _email_if_no_artists_lambda.add_to_role_policy(
            PolicyStatement(
                actions=['sns:ListSubscriptionsByTopic', 'sns:Publish'],
                resources=[_topic.topic_arn],
                effect=Effect.ALLOW,
            )
        )

        fetch_music_lambda_name = generate_name('GetLatestMusicLambda-ForNotifier', account)
        _fetch_music_lambda = Function(
            self,
            fetch_music_lambda_name,
            description='Fetches the latest music released by any of the artists being monitored',
            function_name=fetch_music_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            timeout=Duration.minutes(3),
            code=Code.from_asset('src/lambdas/NotifierConstructLambdas'),
            handler='get_latest_music_for_notifier.handler',
            layers=[requests_layer],
            log_group=LogGroup(
                self, 'NotifierFetchMusicLogGroup',
                retention=RetentionDays.ONE_YEAR,
                removal_policy=get_removal_policy(account.stage)
            ),
            security_groups=[vpc_stack.lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_WITH_EGRESS)
        )

        update_table_music_lambda_name = generate_name('UpdateTableMusicLambda-ForNotifier', account)
        _update_table_music_lambda = Function(
            self,
            update_table_music_lambda_name,
            description=f'Updates {artist_table.table_name} with the latest music released by all of the artists being monitored',
            function_name=update_table_music_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            timeout=Duration.seconds(45),
            code=Code.from_asset('src/lambdas/NotifierConstructLambdas'),
            handler='update_table_music_for_notifier.handler',
            environment={'ARTIST_TABLE_NAME': artist_table.table_name},
            log_group=LogGroup(
                self, 'NotifierUpdateTableMusicLogGroup',
                retention=RetentionDays.ONE_YEAR,
                removal_policy=get_removal_policy(account.stage)
            ),
            security_groups=[vpc_stack.lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        artist_table.grant_write_data(_update_table_music_lambda)

        email_new_music_lambda_name = generate_name('MessageNewMusicLambda', account)
        _email_new_music_lambda = Function(
            self,
            email_new_music_lambda_name,
            description='Publishes a message to a SNS topic with new music.',
            function_name=email_new_music_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/NotifierConstructLambdas'),
            handler='message_new_music.handler',
            environment={'SNS_TOPIC_ARN': _topic.topic_arn},
            timeout=Duration.seconds(5),
            log_group=LogGroup(
                self, 'NotifierMessageNewMusicLogGroup',
                retention=RetentionDays.ONE_YEAR,
                removal_policy=get_removal_policy(account.stage)
            ),
            security_groups=[vpc_stack.lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        _email_new_music_lambda.add_to_role_policy(
            PolicyStatement(
                actions=['sns:ListSubscriptionsByTopic', 'sns:Publish'],
                resources=[_topic.topic_arn],
            )
        )

        # Tasks within our Step Function workflow
        _fetch_access_token_task = LambdaInvoke(
            self,
            'FetchAccessToken',
            lambda_function=access_token_lambda,  # type: ignore
            output_path='$.access_token',
            payload_response_only=True,
        )

        _scan_task = LambdaInvoke(
            self,
            'ScanArtistTable',
            lambda_function=_fetch_artists_list_lambda,  # type: ignore
            output_path='$.payload',
            payload_response_only=True,
        )

        # If `_scan_task` returns with a status code of 204, we immediately publish SNS message to the topic.
        # Otherwise, we invoke the lambda to fetch the latest music released all artists
        _choice_state = Choice(self, 'Artists in the list, or not?')

        # Define tasks for choice state
        _if_no_artists_publish_task = LambdaInvoke(
            self,
            'PublishEmailIfNoArtists',
            lambda_function=_email_if_no_artists_lambda,  # type: ignore
        )

        _fetch_latest_music_task = LambdaInvoke(
            self,
            'FetchLatestMusic',
            lambda_function=_fetch_music_lambda,  # type: ignore
            output_path='$.latest_music',
            payload_response_only=True,
        )

        # Add conditions to the choice state
        _choice_state.when(Condition.number_equals('$.status_code', 204), _if_no_artists_publish_task)
        _choice_state.otherwise(_fetch_latest_music_task)

        # Continue listing the rest of the tasks in our Step Function workflow
        _update_table_task = LambdaInvoke(
            self,
            'UpdateTableMusic',
            lambda_function=_update_table_music_lambda,  # type: ignore
            output_path='$.new_music',
            payload_response_only=True,
        )

        _publish_results_task = LambdaInvoke(
            self, 'PublishResults', lambda_function=_email_new_music_lambda  # type: ignore
        )

        # Connect tasks to be in order
        _fetch_access_token_task.next(_scan_task)
        _scan_task.next(_choice_state)
        _fetch_latest_music_task.next(_update_table_task)
        _update_table_task.next(_publish_results_task)

        # Instantiate StateMachine for our entire step function workflow
        _state_machine = StateMachine(
            self,
            'NotifierStateMachine',
            state_machine_name=generate_name('NotifierStateMachine', account),
            definition=_fetch_access_token_task,  # The initial task to invoke
        )

        # EventBridge rule to trigger Lambda StepFunction routine every Sunday at 8AM EST
        if account.stage.value == 'Prod':
            Rule(
                self,
                'NotificationRule',
                rule_name=generate_name('WeeklyMusicFetchNotificationRule', account),
                schedule=Schedule.cron(minute='0', hour='12', week_day='SUN'),
                description='Triggers Lambda every week to fetch the latest musical releases from my list of artists.',
                targets=[SfnStateMachine(_state_machine)],  # type: ignore
            )

        # Import my email address to grant some Lambdas permission to pull secrets
        __my_email = Secret.from_secret_name_v2(self, 'ImportedEmailAddress', secret_name='EmailSecret')
        __my_email.grant_read(_email_if_no_artists_lambda)
        __my_email.grant_read(_email_new_music_lambda)
