#!/bin/bash

##################################################################################################
# Script Name : aws_get_mfa.sh
# Author : Prasad Domala (prasad.domala@gmail.com)
# Purpose : This script is used to generate IAM Session Token based on the MFA code
#           provided by the user. The session token is required to connect to AWS
#           using MFA authentication. The Session Token is valid for 12 hours by default.
#           This script checks the expiriration time of the existing session token and
#           creates a new one if it is expired. It also updates the AWS credentials file
#           located under user home.
# Usage : aws_get_mfa.sh arg1 [arg2]
# $ ./aws_get_mfa.sh target_profile_name-mfa [user_profile_name]
# Arguements
#   target_profile_name : This arguement specifies the target MFA profile name which contains
#          the temporary and dynamically generated AccessKey, SecretAccessKey
#          and SessionToken
#   user_profile_name : This parameter specifies the profile name used to call STS service which
#          contains AccessKey, SecretAccessKey of the IAM user.  If it is not provided, it will
#          use the defualt credentials.
##################################################################################################

# Get profile names from arguements
TARGET_PROFILE_NAME=$1
USER_PROFILE_NAME=$2


# Set the profile string if one is provided...otherwise use "default"
PROFILE_STR=""
if [ -n "$USER_PROFILE_NAME" ]; then
  PROFILE_STR="--profile $USER_PROFILE_NAME"
else
  echo "Using Defualt Profile"
fi
echo "Generating Profile '$TARGET_PROFILE_NAME'"

# Generate Security Token Flag
GENERATE_ST="true"

# Expiration Time: Each SessionToken will have an expiration time which by default is 12 hours and
# can range between 15 minutes and 36 hours
MFA_PROFILE_EXISTS=`more ~/.aws/credentials | grep $TARGET_PROFILE_NAME | wc -l`
if [ $MFA_PROFILE_EXISTS -eq 1 ]; then
    EXPIRATION_TIME=$(aws configure get expiration --profile $TARGET_PROFILE_NAME)
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    if [[ "$EXPIRATION_TIME" > "$NOW" ]]; then
        echo "The Session Token is still valid. New Security Token not required."
        GENERATE_ST="false"
    fi
fi

MFA_SERIAL=$(aws configure get mfa_serial $PROFILE_STR)
DEFAULT_REGION=$(aws configure get region $PROFILE_STR)
DEFAULT_OUTPUT=$(aws configure get output $PROFILE_STR)

if [ -z "$MFA_SERIAL" ]; then
    echo "Missing 'mfa_serial=' in credentials for $PROFILE_STR"
    exit 1
fi
if [ -z "$DEFAULT_REGION" ]; then
    echo "Missing 'region=' in config for $PROFILE_STR"
    exit 1
fi
if [ -z "$DEFAULT_OUTPUT" ]; then
    echo "Missing 'output=' in config for $PROFILE_STR"
    exit 1
fi

if [ "$GENERATE_ST" = "true" ];then
    read -p "Token code for MFA Device ($MFA_SERIAL): " TOKEN_CODE
    echo "Generating new IAM STS Token ..."
    echo "Running command: aws sts get-session-token $PROFILE_STR --output text --query 'Credentials.*' --serial-number $MFA_SERIAL --token-code $TOKEN_CODE" 
    read -r AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN EXPIRATION AWS_ACCESS_KEY_ID < <(aws sts get-session-token $PROFILE_STR --output text --query 'Credentials.*' --serial-number $MFA_SERIAL --token-code $TOKEN_CODE)
    if [ $? -ne 0 ];then
        echo "An error occured. AWS credentials file not updated"
    else
        aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile $TARGET_PROFILE_NAME
        aws configure set aws_session_token "$AWS_SESSION_TOKEN" --profile $TARGET_PROFILE_NAME
        aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID" --profile $TARGET_PROFILE_NAME
        aws configure set expiration "$EXPIRATION" --profile $TARGET_PROFILE_NAME
        aws configure set region "$DEFAULT_REGION" --profile $TARGET_PROFILE_NAME
        aws configure set output "$DEFAULT_OUTPUT" --profile $TARGET_PROFILE_NAME
        echo "STS Session Token generated and updated in AWS credentials file successfully."
    fi
fi

#create .boto file
echo "[Credentials]" > .boto
echo "aws_access_key_id = $AWS_ACCESS_KEY_ID" >> .boto
echo "aws_secret_access_key = $AWS_SECRET_ACCESS_KEY" >> .boto
echo "aws_security_token = $AWS_SESSION_TOKEN" >> .boto
echo "" >> .boto
echo "[boto]" >> .boto
echo "ec2_region_name = $DEFAULT_REGION" >> .boto
echo "ec2_region_endpoint = ec2.$DEFAULT_REGION.amazonaws.com" >> .boto
