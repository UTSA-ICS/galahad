#! /bin/bash

##################################################################################################
# Script Name : aws_set_sts_token.sh
# Author : Farhan Patwa (farhan.patwa@starlab.io)
# Purpose : This script is used to generate IAM Session Token based on the MFA code
#           provided by the user. The session token is required to connect to AWS
#           using MFA authentication. The Session Token is valid for 12 hours by default.
#           This script creates a new session token everytime it is called.
#           It will also set the following environment variables to use with AWS cli and
#           boto3 client. 
#           AWS_ACCESS_KEY_ID
#           AWS_SECRET_ACCESS_KEY
#           AWS_SESSION_TOKEN
#
# Usage : aws_set_sts_token.sh
# $ . ./aws_set_sts_token.sh
# Please Note that this script needs to be sourced at the current shell.
##################################################################################################

mfa_serial=""

echo ""

# Unset any previous AWS credentials
function cleanup {
  unset AWS_ACCESS_KEY_ID
  unset AWS_SECRET_ACCESS_KEY
  unset AWS_SESSION_TOKEN
}

# Get current user information: username and mfa_serial.
function get_user_info {
  userinfo=$(aws iam get-user 2>&1)
  $(echo $userinfo |grep -q "AccessDenied")
  if [ $? = 0 ]; then
    username=$(echo $userinfo |grep "aws:iam" |cut -d"/" -f 2 |cut -d" " -f 1)
  else
    username=$(echo $userinfo |python -c "import sys,json; print (json.load(sys.stdin)['User']['UserName'])")
  fi
  echo "Getting MFA SERIAL for user: $username"

  mfa_serial=$(aws iam list-virtual-mfa-devices |python -c "exec(\"import sys,json; mfa = json.load(sys.stdin)['VirtualMFADevices']\nfor i in mfa:   print (i['SerialNumber'])\")" |grep $username)

  echo "The MFA SERIAL is: $mfa_serial"
}

# Get the STS Token and set the appropriate environment variables for AWS Credentials.
function set_token {
  echo ""
  read -p "Please enter Token Code for MFA Device: " TOKEN_CODE
  echo ""
  echo "Getting the STS Token..."
  session_token=$(aws sts get-session-token --serial-number $mfa_serial --token-code $TOKEN_CODE)
  if [[ $? != 0 ]]; then
    echo "Error in getting the correct mfa serial number!"
    return -1
  fi
  #session_token=$(aws sts get-session-token)

  AccessKeyId=$(echo $session_token |python -m json.tool |grep AccessKeyId |cut -d'"' -f 4)
  SecretAccessKey=$(echo $session_token |python -m json.tool |grep SecretAccessKey |cut -d'"' -f 4)
  SessionToken=$(echo $session_token |python -m json.tool |grep SessionToken |cut -d'"' -f 4)

  echo "New STS credentials and Token are:"
  echo ""
  #echo $session_token |python -m json.tool
  echo AWS_ACCESS_KEY_ID=$AccessKeyId
  echo AWS_SECRET_ACCESS_KEY=$SecretAccessKey
  echo AWS_SESSION_TOKEN=$SessionToken

  export AWS_ACCESS_KEY_ID=$AccessKeyId
  export AWS_SECRET_ACCESS_KEY=$SecretAccessKey
  export AWS_SESSION_TOKEN=$SessionToken
}

cleanup
get_user_info
set_token
aws ecr get-login --no-include-email --region us-east-2
