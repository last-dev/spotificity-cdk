from aws_cdk import RemovalPolicy, Stack
from aws_cdk.aws_dynamodb import AttributeType, StreamViewType, TableEncryptionV2, TableV2
from constructs import Construct

from ..helpers.helpers import generate_name, get_removal_policy

from ..constants import AwsAccount


class DatabaseStack(Stack):

    @property
    def artist_table(self) -> TableV2:
        """Returns the DynamoDB table name that holds the monitored artists."""
        return self.table

    def __init__(self, scope: Construct, id: str, account: AwsAccount, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        artist_table_name = generate_name('MonitoredArtistsTable', account)
        self.table = TableV2(
            self,
            artist_table_name,
            partition_key={'name': 'artist_id', 'type': AttributeType.STRING},
            encryption=TableEncryptionV2.aws_managed_key(),
            removal_policy=RemovalPolicy.RETAIN,
            dynamo_stream=StreamViewType.NEW_IMAGE,
            table_name=artist_table_name,
            point_in_time_recovery=True,
        )
        self.table.apply_removal_policy(get_removal_policy(account.stage))
