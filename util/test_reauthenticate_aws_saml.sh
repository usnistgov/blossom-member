#!/usr/bin/env bash
# Tests AWS CLI for valid credentials and reauthenticates if credentials are
# invalid or expired.
# This script also manages the creation of a Python virtual environment.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"
source "${SCRIPT_DIR}/util-common.bash"

if ! [ -x "$(command -v python3)" ]; then
  msg 'Error: Python (python3) is not in the PATH, is it installed?'
  exit 1
fi

if ! [ -x "$(command -v aws)" ]; then
  msg 'Error: AWS-CLI (aws) is not in the PATH, is it installed?'
  exit 1
fi

if aws sts get-caller-identity --profile=$AWS_PROFILE > /dev/null 2>&1; then
    # Credentials are valid, no need to continue
    exit 0
fi

test_setup_venv

(
  cd "$SCRIPT_DIR"
  source ./venv/bin/activate

  msg "Enter your Functional credentials:"
  python3 aws_saml_auth.py
)
