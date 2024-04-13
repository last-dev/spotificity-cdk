from aws_cdk import Duration
from aws_cdk.aws_dynamodb import TableV2
from aws_cdk.aws_lambda import Code, Function, Runtime
from constructs import Construct

from ..constants import AwsAccount
from ..helpers.helpers import generate_name


class CoreTableOperatorsConstruct(Construct):
    """
    Custom construct for the core Setter, Getter, and Deleter Lambda
    functions for the DynamoDB table that stores the current
    monitored artists.
    """

    @property
    def fetch_artists_lambda(self) -> Function:
        return self.fetch_artists_lambda_

    @property
    def add_artist_lambda(self) -> Function:
        return self.add_artist_lambda_

    @property
    def remove_artist_lambda(self) -> Function:
        return self.remove_artist_lambda_

    @property
    def update_table_with_music_lambda(self) -> Function:
        return self.update_table_with_music_lambda_

    def __init__(self, scope: Construct, id: str, account: AwsAccount, artist_table: TableV2, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        fetch_artist_lambda_name = generate_name('FetchArtistLambda', account)
        self.fetch_artists_lambda_ = Function(
            self,
            fetch_artist_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreTableOperatorLambdas'),
            handler='list_artists.handler',
            environment={'ARTIST_TABLE_NAME': artist_table.table_name},
            function_name=fetch_artist_lambda_name,
            description=f'Returns a list of all current artists being monitored in DynamoDB table: {artist_table.table_name}.',
            timeout=Duration.seconds(20),
        )
        artist_table.grant_read_data(self.fetch_artists_lambda_)

        add_artist_lambda_name = generate_name('AddArtistLambda', account)
        self.add_artist_lambda_ = Function(
            self,
            add_artist_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreTableOperatorLambdas'),
            handler='add_artist.handler',
            environment={'ARTIST_TABLE_NAME': artist_table.table_name},
            function_name=add_artist_lambda_name,
            description=f'Adds a new artist to the DynamoDB table: {artist_table.table_name}.',
            timeout=Duration.seconds(20),
        )
        artist_table.grant_write_data(self.add_artist_lambda_)

        remove_artist_lambda_name = generate_name('RemoveArtistLambda', account)
        self.remove_artist_lambda_ = Function(
            self,
            remove_artist_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreTableOperatorLambdas'),
            handler='remove_artist.handler',
            environment={'ARTIST_TABLE_NAME': artist_table.table_name},
            function_name=remove_artist_lambda_name,
            description=f'Removes an artist from the DynamoDB table: {artist_table.table_name}.',
            timeout=Duration.seconds(20),
        )
        artist_table.grant_write_data(self.remove_artist_lambda_)

        update_table_with_music_lambda_name = generate_name('UpdateTableWithMusicLambda', account)
        self.update_table_with_music_lambda_ = Function(
            self,
            update_table_with_music_lambda_name,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset('src/lambdas/CoreTableOperatorLambdas'),
            handler='update_table_music.handler',
            environment={'ARTIST_TABLE_NAME': artist_table.table_name},
            function_name=update_table_with_music_lambda_name,
            description=f'Once the latest musical release is pulled, this updates {artist_table.table_name}\'s artist attributes.',
            timeout=Duration.seconds(20),
        )
        artist_table.grant_write_data(self.update_table_with_music_lambda_)
