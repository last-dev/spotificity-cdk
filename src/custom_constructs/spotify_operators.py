from aws_cdk.aws_dynamodb import Table
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime, StartingPosition
from aws_cdk.aws_lambda_event_sources import DynamoEventSource
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct

from ..constants import AwsAccount

from ..helpers.helpers import generate_name, get_removal_policy


class CoreSpotifyOperatorsConstruct(Construct):
    """
    Custom construct for core resources that will interact with
    the Spotify API.
    """

    @property
    def access_token_lambda(self) -> Function:
        return self.get_access_token_lambda

    @property
    def artist_id_lambda(self) -> Function:
        return self.get_artist_id_lambda

    def __init__(
        self,
        scope: Construct,
        id: str,
        account: AwsAccount,
        artist_table_arn: str,
        artist_table_stream_arn: str | None,
        update_table_music_lambda: Function,
        requests_layer: LayerVersion,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        get_access_token_lambda_name = generate_name('GetAccessTokenLambda', account)
        self.get_access_token_lambda = Function(
            self,
            get_access_token_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreSpotifyOperatorLambdas'),
            handler='get_access_token.handler',
            function_name=get_access_token_lambda_name,
            description=f'Calls Spotify\'s API to get an access token.',
            layers=[requests_layer],
        )

        get_artist_id_lambda_name = generate_name('GetArtist-IDLambda', account)
        self.get_artist_id_lambda = Function(
            self,
            get_artist_id_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreSpotifyOperatorLambdas'),
            handler='get_artist_id.handler',
            function_name=get_artist_id_lambda_name,
            description=f'Queries the Spotify\'s API for the artist\'s ID.',
            layers=[requests_layer],
        )

        # Grant read permissions to my Spotify client secrets
        __spotify_secrets = Secret.from_secret_name_v2(
            self, 'ImportedSpotifySecrets', secret_name='SpotifySecrets'
        )
        __spotify_secrets.grant_read(self.get_access_token_lambda)

        get_latest_music_lambda_name = generate_name('GetLatestMusicLambda', account)
        _get_latest_music_lambda = Function(
            self,
            get_latest_music_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreSpotifyOperatorLambdas'),
            handler='get_latest_music.handler',
            function_name=get_latest_music_lambda_name,
            description='Queries a series of Spotify API\'s for the artist\'s latest music.',
            layers=[requests_layer],
            environment={
                'GET_ACCESS_TOKEN_LAMBDA': self.get_access_token_lambda.function_name,
                'UPDATE_TABLE_MUSIC_LAMBDA': update_table_music_lambda.function_name,
            },
        )
        self.get_access_token_lambda.grant_invoke(_get_latest_music_lambda)
        _get_latest_music_lambda.add_event_source(
            DynamoEventSource(
                table=Table.from_table_attributes(
                    self,
                    f'MonitoredArtistTable-{account.stage.value.lower()}',
                    table_arn=artist_table_arn,
                    table_stream_arn=artist_table_stream_arn,
                ),
                starting_position=StartingPosition.LATEST,
                retry_attempts=3,
                bisect_batch_on_error=True,
            )
        )
        update_table_music_lambda.grant_invoke(_get_latest_music_lambda)
