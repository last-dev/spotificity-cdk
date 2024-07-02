from aws_cdk import Stack
from aws_cdk.aws_dynamodb import TableV2
from aws_cdk.aws_lambda import Code, LayerVersion, Runtime
from constructs import Construct

from .vpc_stack import VpcStack

from ..constants import AwsAccount
from ..custom_constructs.api_gateway import ApiGatewayConstruct
from ..custom_constructs.notifier import NotifierConstruct
from ..custom_constructs.spotify_operators import CoreSpotifyOperatorsConstruct
from ..custom_constructs.table_operators import CoreTableOperatorsConstruct


class BackendStack(Stack):
    def __init__(self, scope: Construct, id: str, account: AwsAccount, artist_table: TableV2, vpc_stack: VpcStack) -> None:
        super().__init__(scope, id)

        # Lambda layer that bundles `requests` module
        requests_layer = LayerVersion(
            self,
            'RequestsLayer',
            code=Code.from_asset('src/lambdas/lambda_layers/requests_v2-31-0.zip'),
            layer_version_name='Requests_v2-31-0',
            description='Bundles the "requests" module.',
            compatible_runtimes=[Runtime.PYTHON_3_12],
        )

        # Custom construct with setter, getter, and deleter Lambda functions
        # for manipulating DynamoDB table
        table_operators = CoreTableOperatorsConstruct(
            self, 
            'TableManipulatorsConstruct', 
            account,
            artist_table=artist_table,
            vpc_stack=vpc_stack
        )

        # Custom construct for the resources that will interact with the Spotify API
        spotify_operators = CoreSpotifyOperatorsConstruct(
            self,
            'SpotifyOperatorsConstruct',
            account,
            artist_table.table_arn,
            artist_table.table_stream_arn,
            table_operators.update_table_with_music_lambda,
            requests_layer,
        )

        # Custom construct for the step function workflow that will be triggered by an EventBridge rate expression
        NotifierConstruct(
            self,
            'NotifierConstruct',
            account,
            artist_table,
            requests_layer,
            spotify_operators.get_access_token_lambda,
        )

        # Custom construct for the API Gateway that will be used to invoke the Lambda functions
        ApiGatewayConstruct(
            self,
            'ApiGatewayConstruct',
            account,
            table_operators.fetch_artists_lambda,
            table_operators.add_artist_lambda,
            table_operators.remove_artist_lambda,
            spotify_operators.get_access_token_lambda,
            spotify_operators.get_artist_id_lambda,
        )
