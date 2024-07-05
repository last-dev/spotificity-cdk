from aws_cdk import Stack
from aws_cdk.aws_ec2 import (
    FlowLogDestination,
    FlowLogOptions,
    FlowLogTrafficType,
    GatewayVpcEndpoint,
    GatewayVpcEndpointAwsService,
    InterfaceVpcEndpoint,
    InterfaceVpcEndpointAwsService,
    IpAddresses,
    Peer,
    Port,
    SecurityGroup,
    SubnetConfiguration,
    SubnetSelection,
    SubnetType,
    Vpc,
)
from aws_cdk.aws_logs import LogGroup, RetentionDays
from constructs import Construct


class VpcStack(Stack): 
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)
        
        # VPC and Flowlogs
        log_group = LogGroup(self, 'VPCLogGroup', retention=RetentionDays.ONE_YEAR)
        self.vpc = Vpc(
            self, 'VPC', 
            vpc_name='App_VPC',
            ip_addresses=IpAddresses.cidr('10.0.0.0/24'),
            max_azs=1,
            nat_gateways=1,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            flow_logs={
                'FlowLogs': FlowLogOptions(
                    destination=FlowLogDestination.to_cloud_watch_logs(log_group),
                    traffic_type=FlowLogTrafficType.ALL,
                )
            },
            subnet_configuration=[
                SubnetConfiguration(name='Public', subnet_type=SubnetType.PUBLIC),
                SubnetConfiguration(name='Private With NAT', subnet_type=SubnetType.PRIVATE_WITH_EGRESS),
                SubnetConfiguration(name='Private', subnet_type=SubnetType.PRIVATE_ISOLATED)
            ]
        )
        
        # Security groups and egress/ingress rules
        interface_endpoint_sg = SecurityGroup(
            self, 'Interface_Endpoint_SG', 
            vpc=self.vpc, 
            allow_all_outbound=True,
            description='Security Group for Interface VPC Endpoints'
        )
        interface_endpoint_sg.add_ingress_rule(
            Peer.ipv4(self.vpc.vpc_cidr_block), 
            Port.tcp(443), 
            'Allow all HTTPS traffic from within VPCs CIDR block'
        )
        self.lambda_sg = SecurityGroup(
            self, 'LambdaSecurityGroup', 
            vpc=self.vpc, 
            allow_all_outbound=False,
            description='Security Group for Lambda functions'
        )
        self.lambda_sg.add_egress_rule(
            interface_endpoint_sg, 
            Port.tcp(443), 
            'Allow traffic from Lambda to Interface VPC Endpoints'
        )
        
        # VPC Endpoints
        self.s3_gateway_endpoint = GatewayVpcEndpoint(
            self, 'S3Endpoint', 
            vpc=self.vpc,
            service=GatewayVpcEndpointAwsService.S3,
            subnets=[SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)]
        )
        self.dynamo_gateway_endpoint = GatewayVpcEndpoint(
            self, 'DynamoEndpoint',
            vpc=self.vpc,
            service=GatewayVpcEndpointAwsService.DYNAMODB,
            subnets=[SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)]
        )
        self.secretsmanager_interface_endpoint = InterfaceVpcEndpoint(
            self, 'SecretsManagerEndpoint',
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            private_dns_enabled=True,
            security_groups=[interface_endpoint_sg],
            subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        self.lambda_interface_endpoint = InterfaceVpcEndpoint(
            self, 'LambdaEndpoint',
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.LAMBDA_,
            private_dns_enabled=True,
            security_groups=[interface_endpoint_sg],
            subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        self.sns_interface_endpoint = InterfaceVpcEndpoint(
            self, 'SNSEndpoint',
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.SNS,
            private_dns_enabled=True,
            security_groups=[interface_endpoint_sg],
            subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        self.step_functions_interface_endpoint = InterfaceVpcEndpoint(
            self, 'StepFunctionEndpoint',
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.STEP_FUNCTIONS,
            private_dns_enabled=True,
            security_groups=[interface_endpoint_sg],
            subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        self.eventbridge_interface_endpoint = InterfaceVpcEndpoint(
            self, 'EventBridgeEndpoint',
            vpc=self.vpc,
            service=InterfaceVpcEndpointAwsService.EVENTBRIDGE,
            private_dns_enabled=True,
            security_groups=[interface_endpoint_sg],
            subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_ISOLATED)
        )
        