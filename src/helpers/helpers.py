from aws_cdk import RemovalPolicy

from src.constants import Account, Stage


def get_removal_policy(stage: Stage) -> RemovalPolicy:
    """
    Determines the appropriate removal policy for resource based on
    the deployment stage.
    """
    if stage == Stage.Prod:
        return RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE
    return RemovalPolicy.DESTROY


def generate_name(name: str, account: Account) -> str:
    """
    Generates a name for a resource based on the deployment stage and
    account.
    """
    return f'{name}-{account.stage.value.lower()}'
