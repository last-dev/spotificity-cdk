import os
from dataclasses import dataclass
from enum import Enum


class Stage(Enum):
    Prod = 'Prod'
    Beta = 'Beta'


class AwsRegion(Enum):
    IAD = 'us-east-1'


@dataclass(frozen=True)
class AwsAccount:
    account_id: str
    stage: Stage
    region: AwsRegion


# Define my development accounts for each stage
@dataclass
class Accounts:
    beta: AwsAccount = AwsAccount(
        account_id=os.environ['SPOTIFICITY_BETA_ACCT'],
        stage=Stage.Beta,
        region=AwsRegion.IAD,
    )
    prod: AwsAccount = AwsAccount(
        account_id=os.environ['SPOTIFICITY_PROD_ACCT'],
        stage=Stage.Prod,
        region=AwsRegion.IAD,
    )
