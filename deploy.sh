#!/bin/sh

set -e

RESET="\033[0m"
MAGENTA="\033[35m"
YELLOW="\033[33m"
RED="\033[31m"
GREEN="\033[32m"
beta_acc=$SPOTIFICITY_BETA_ACCT
prod_acc=$SPOTIFICITY_PROD_ACCT

############################
# Define script components #
############################

check_aws_profile_exists() {
    local profile_name=$1
    local aws_config_path="${HOME}/.aws/config"

    if [ ! -f "$aws_config_path" ]; then
        echo "${RED}AWS config file does not exist at: $aws_config_path"
        exit 1
    fi

    if ! grep -q "\[profile $profile_name\]" "$aws_config_path"; then
        echo "${RED}AWS profile '$profile_name' does not exist in: $aws_config_path"
        exit 1
    fi
}

set_account_envs() {
    if [[ $1 == *"beta"* ]]; then
        export CDK_DEFAULT_ACCOUNT=$beta_acc
        export CDK_DEFAULT_REGION='us-east-1'
    elif [[ $1 == *"prod"* ]]; then
        export CDK_DEFAULT_ACCOUNT=$prod_acc
        export CDK_DEFAULT_REGION='us-east-1'
    else
        echo "${RED}Error: Unsupported profile name '$1'${RESET}"
        echo "${YELLOW}Is the profile you provided not for SpotificityCDK?${RESET}"
        exit 1
    fi
}

##################
# Execute script #
##################

# Parse cli arg
while getopts "p:" opt; do
    case $opt in
        p) aws_profile="$OPTARG";;
        *) echo "${RED}Usage: $0 -p <awscli_profile_name>"; exit 1;;
    esac
done

# Ensure arg is given 
if [ -z "$aws_profile" ]; then
    echo "${RED}Error: An AWS Cli profile name is required."
    echo "Usage: $0 -p <awscli_profile_name>"
    exit 1
fi

# Ensure profile actually exists
check_aws_profile_exists "$aws_profile"

# Set account environment envs
set_account_envs "$aws_profile"

# Start deploying
prefix="✨ ${MAGENTA}Deploying SpotificityCDK resources with ${YELLOW}${aws_profile}${RESET} ${MAGENTA}profile! -${RESET}"

echo "\n${prefix} ${GREEN}Running bootstrap...${RESET}\n"
cdk bootstrap --profile $aws_profile --account $CDK_DEFAULT_ACCOUNT --region $CDK_DEFAULT_REGION

echo "\n${prefix} ${GREEN}Deploying all stacks into AWS account ${CDK_DEFAULT_ACCOUNT}...${RESET}\n"
cdk deploy --all --profile $aws_profile --account $CDK_DEFAULT_ACCOUNT --region $CDK_DEFAULT_REGION

echo "\n${GREEN}Deployment completed successfully! Here is a cake: 🍰${RESET}\n"