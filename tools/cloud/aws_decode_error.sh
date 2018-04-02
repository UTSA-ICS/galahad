#!/bin/bash
err=$1
aws sts decode-authorization-message --output=text --encoded-message $err | python -m json.tool
