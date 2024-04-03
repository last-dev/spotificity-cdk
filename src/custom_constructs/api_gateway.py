from aws_cdk.aws_apigateway import AuthorizationType, LambdaIntegration, RestApi
from aws_cdk.aws_iam import Role, ServicePrincipal
from aws_cdk.aws_lambda import Function
from aws_cdk.aws_ssm import StringParameter
from constructs import Construct

from ..constants import AwsAccount

from ..helpers.helpers import generate_name, get_removal_policy


class ApiGatewayConstruct(Construct):
    """
    Custom construct for API Gateway resources that will be used
    to invoke `CoreTableOperator` Lambda functions.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        account: AwsAccount,
        fetch_artists_lambda: Function,
        add_artists_lambda: Function,
        remove_artists_lambda: Function,
        access_token_lambda: Function,
        get_artist_id_lambda: Function,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        api_gateway_role = Role(
            self,
            'ApiGatewayRole',
            role_name='ApiGatewayExecutionRole',
            assumed_by=ServicePrincipal('apigateway.amazonaws.com'),  # type: ignore
        )

        fetch_artists_lambda.grant_invoke(api_gateway_role)
        add_artists_lambda.grant_invoke(api_gateway_role)
        remove_artists_lambda.grant_invoke(api_gateway_role)
        access_token_lambda.grant_invoke(api_gateway_role)
        get_artist_id_lambda.grant_invoke(api_gateway_role)

        self._api = RestApi(
            self,
            'ApiForClientInvokes',
            rest_api_name=generate_name('ApiForClientInvokes', account),
            description="API Gateway for Lambdas invoked from client.",
            policy=api_gateway_role.assume_role_policy,
        )
        self._api.apply_removal_policy(get_removal_policy(account.stage))

        # Lambda Integrations
        fetch_artist_integration = LambdaIntegration(fetch_artists_lambda)  # type: ignore
        add_artist_integration = LambdaIntegration(add_artists_lambda)  # type: ignore
        remove_artist_integration = LambdaIntegration(remove_artists_lambda)  # type: ignore
        access_token_integration = LambdaIntegration(access_token_lambda)  # type: ignore
        get_artist_id_integration = LambdaIntegration(get_artist_id_lambda)  # type: ignore

        """
        Define resources and methods for all CoreTableOperator Lambda functions.
        Making sure that IAM Authentication is enabled for each Gateway method
        """
        # GET /token
        token_resource = self._api.root.add_resource('token')
        token_resource.add_method(
            'GET', access_token_integration, authorization_type=AuthorizationType.IAM
        )

        # GET /artist
        artist_resource = self._api.root.add_resource('artist')
        artist_resource.add_method(
            'GET', fetch_artist_integration, authorization_type=AuthorizationType.IAM
        )

        # POST/artist/id
        get_artist_id_resource = artist_resource.add_resource('id')
        get_artist_id_resource.add_method(
            'POST', get_artist_id_integration, authorization_type=AuthorizationType.IAM
        )

        # POST /artist
        add_artist_resource = artist_resource
        add_artist_resource.add_method(
            'POST', add_artist_integration, authorization_type=AuthorizationType.IAM
        )

        # DELETE /artist
        remove_artist_resource = artist_resource
        remove_artist_resource.add_method(
            'DELETE', remove_artist_integration, authorization_type=AuthorizationType.IAM
        )

        # Store the API Gateway URL in SSM for CLI users
        endpoint_url_param = StringParameter(
            self,
            generate_name('ApiGwUrlParameter', account),
            description='API Gateway Endpoint Url',
            parameter_name=f'/Spotificity/ApiGatewayEndpointUrl/{account.stage.value.lower()}',
            string_value=self._api.url,
        )
        endpoint_url_param.apply_removal_policy(get_removal_policy(account.stage))
