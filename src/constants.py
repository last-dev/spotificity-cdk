import os
from dataclasses import dataclass
from enum import Enum


class Stage(Enum):
    Dev = 'Dev'
    Prod = 'Prod'
    Beta = 'Beta'


class AwsRegion(Enum):
    IAD = 'us-east-1'


@dataclass(frozen=True)
class AwsAccount:
    account_id: str
    stage: Stage
    region: AwsRegion
    disambiguator: str
    api_gw_endpoint_ssm_param_name: str


# Define my development accounts for each stage
@dataclass
class Accounts:
    beta: AwsAccount = AwsAccount(
        account_id=os.environ['SPOTIFICITY_BETA_ACCT'],
        stage=Stage.Beta,
        region=AwsRegion.IAD,
        disambiguator=f'spotificity',
        api_gw_endpoint_ssm_param_name='/Spotificity/ApiGatewayEndpointUrl/beta',
    )
    prod: AwsAccount = AwsAccount(
        account_id=os.environ['SPOTIFICITY_PROD_ACCT'],
        stage=Stage.Prod,
        region=AwsRegion.IAD,
        disambiguator=f'spotificity',
        api_gw_endpoint_ssm_param_name='/Spotificity/ApiGatewayEndpointUrl/prod',
    )
