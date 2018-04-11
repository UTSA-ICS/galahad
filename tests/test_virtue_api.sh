#! /bin/bash

# This will test the virtue REST API endpoints from the perspective of a user client.
# These REST endpoints will be called by a user in canvas.

FLASK_SERVER="172.30.1.44:5002"
API_CALL=""
API_PARAMETER=""
ACCESS_TOKEN=$1

if [ "$#" -ne 1 ]; then
  echo "#################################################################"
  echo "ERROR: No Access Token specified. Please pass in the Access Token"
  echo "#################################################################"
  exit
fi

URL="https://$FLASK_SERVER/"
CURL_CMD="curl -s --insecure --header \"Authorization: Bearer $ACCESS_TOKEN\" "

function check_result() {
  error=$(echo $3 |grep -v "\{")
  if [[ $error != "" ]]; then
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "ERROR: Failed with error:"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!"
  else
    echo "SUCCESS: Result of REST Call:"
  fi
  result=""
  for i in "${@}"; do
    result="$result $i"
  done
  echo "RESULT: $result"
}

# role_get
API_CALL="virtue/user/role/get?roleId="
API_PARAMETER="Test"
echo "#########################"
echo "Test [role get]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# user_role_list
API_CALL="virtue/user/role/list"
API_PARAMETER=""
echo "#########################"
echo "Test [role list]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# user_virtue_list
API_CALL="virtue/user/virtue/list"
API_PARAMETER=""
echo "#########################"
echo "Test [virtue list]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# virtue_get
API_CALL="virtue/user/virtue/get?virtueId="
API_PARAMETER="TestVirtue2"
echo "#########################"
echo "Test [virtue get]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# virtue_create - Existing Virtue
API_CALL="virtue/user/virtue/create?roleId="
API_PARAMETER="Test"
echo "#########################"
echo "Test [virtue create - Existing Virtue]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# virtue_create - New Virtue
API_CALL="virtue/user/virtue/create?roleId="
API_PARAMETER="EmptyRole"
echo "#########################"
echo "Test [virtue create - New Virtue]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""


# virtue_launch
API_CALL="virtue/user/virtue/launch?virtueId="
API_PARAMETER="TestVirtue2"
echo "#########################"
echo "Test [virtue launch]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# virtue_stop
API_CALL="virtue/user/virtue/stop?virtueId="
API_PARAMETER="TestVirtue2"
echo "#########################"
echo "Test [virtue stop]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# virtue_destroy
API_CALL="virtue/user/virtue/destroy?virtueId="
API_PARAMETER="TestVirtue2"
echo "#########################"
echo "Test [virtue destroy]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# application_get
API_CALL="virtue/user/application/get?appId="
API_PARAMETER="firefox1"
echo "#########################"
echo "Test [application get]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER')
check_result $result
echo ""
echo ""

# application_launch
API_CALL="virtue/user/application/launch?appId="
API_PARAMETER="firefox1"
API_CALL2="&virtueId="
API_PARAMETER2="TestVirtue2"
echo "#########################"
echo "Test [application launch]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER$API_CALL2$API_PARAMETER2'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER$API_CALL2$API_PARAMETER2')
check_result $result
echo ""

# application_stop
API_CALL="virtue/user/application/stop?appId="
API_PARAMETER="firefox1"
API_CALL2="&virtueId="
API_PARAMETER2="TestVirtue2"
echo "#########################"
echo "Test [application stop]"
echo "#########################"
echo "$CURL_CMD'$URL$API_CALL$API_PARAMETER$API_CALL2$API_PARAMETER2'"
result=$(eval $CURL_CMD'$URL$API_CALL$API_PARAMETER$API_CALL2$API_PARAMETER2')
check_result $result
echo ""
echo ""

