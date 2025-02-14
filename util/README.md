# NIST BLOSSOM Utilities

The utility scripts in this directory help automate some maintenance and development operations of the BLOSSOM network.

## Collection Config Generation

This is a simple script that generates a `collections-config` file, which is consumed in the channel creation and channel update step.

### Installation
This script does not require any external dependencies. You do NOT need to install the `requirements.txt` dependencies.

### Usage
```
cd path/to/blossom
./util/gen-collection-config.py --admin <admin member id> --approved <member id 1> <member id 2> --unapproved <member id 3>
```
Note that the IDs described here are NOT "names" but ids (`m-...`).

## NIST AWS SAML Authentication for AWS

### Installation

To be able to use the `aws` command-line utility on a developer workstation and
a properly configured EC2 instance in a NIST AWS account, developers must use
the following procedure to create an AWS STS token for time-limited session for
use with the `aws` utility.

To bootstrap this utility _after_ you cloned the repository, you must run the
following commands to install necessary dependencies.

```sh
cd path/to/blossom
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r ./util/requirements.txt
```

### Usage

After the dependencies are installed, a developer must log into the NIST VPN
system and then authenticate with their NIST General Realm username and the
password with the following command.

```sh
cd path/to/blossom
source bin ./venv/bin/activate
python3 infrastructure/aws_saml_auth.py
Username: nistrealmid
Password: *************
```

If there is no output, the STS token generation was successful. You can double
check the token is valid with the following command.

```sh
aws --profile saml sts get-caller-identity
{
    "UserId": "AROAABCDEFGHABCDABC:nistrealmid",
    "Account": "012345678910",
    "Arn": "arn:aws:sts::012345678910:assumed-role/ADFS-project-Dev/nistrealmid"
}
```

### Configuration

#### Profile Environment Variables

If you do not wish to specify the profile with `--profile saml` every time, you
must export the environment variable `export AWS_PROFILE=saml` or configure it
for every shell with your `~/.bashrc` or preferred shell configuration file. Or
you can set `AWS_PROFILE` when running the script to set a different config
name, such as `export AWS_PROFILE_SECTION=default`.

```sh
export AWS_PROFILE=saml
aws sts get-caller-identity
{
    "UserId": "AROAABCDEFGHABCDABC:nistrealmid",
    "Account": "012345678910",
    "Arn": "arn:aws:sts::012345678910:assumed-role/ADFS-project-Dev/nistrealmid"
}
# It works, make it permanent.
echo "export AWS_PROFILE=saml" | tee -a ~/.bashrc
```

#### Username, Password, and Additional Environment Variables

Username and password can be set as environment variables to more efficiently
re-generate updated tokens.

```
# DO NOT DO THE BELOW WITHOUT THIS OR THE USERNAME AND
# PASSWORD WILL SHOW IN YOUR BASH HISTORY
export HISTCONTROL=ignoreboth
  export USERNAME=nistrealmid  # always start with one or more spaces
  export IDP_PASS=MySuperSecretPassword # always start with one or more spaces
source ./venv/bin/activate
python3 infrastructure/aws_saml_auth.py
# Will generate without any prompts
```

There are multiple environment variables available for quick configuration
without modifying the script source, such as:

- `AWS_DEFAULT_REGION`: set the default region for AWS commands
- `AWS_SHARED_CREDENTIALS_FILE`: default path for credentials file, otherwise
the default `~/.aws/credentials`
- `AWS_PROFILE_SECTION`: the section name used in `AWS_SHARED_CREDENTIALS_FILE`
as profile name for configuration and credentials and configs, otherwise `saml`
- `IDP_VERIFY_TLS`: whether or not to validate TLS certificate for NIST IdP
server, otherwise `True`
- `IDP_ENTRY_URL`: custom IdP server and endpoint to generate SAML session and
token, otherwise auth.nist.gov
- `IDP_REALM`: custom realm for NIST user authentication, otherwise `nist`
as part of `nist\\nistrealmid`
- `IDP_USER`: NIST general realm username, otherwise the user is prompted
- `IDP_PASS`: NIST general realm password, otherwise the user is prompted

### Common Errors

#### Response did not contain a valid SAML assertion

After entering your password, if you see the error "Response did not contain a
valid SAML assertion" you must confirm you are connected to the VPN. If you a
Windows Subsystem for Linux (WSL) or a Linux virtual machine, you must ensure
your `/etc/resolv.conf` has configured NIST VPN nameservers. You cannot use any
other DNS resolver. There is a publicly resolvable address returned by other DNS
servers. There will be no explicit error to suggest a DNS misconfiguration.

#### NoAuthHandlerFound: No handler was ready to authenticate

If you confirmed proper use of NIST General Realm username and password, but you
receive the error "NoAuthHandlerFound: No handler was ready to authenticate. 1
handlers were checked. ['HmacAuthV4Handler']" check your that you have at least
boilerplate section and variables in your `AWS_SHARED_CREDENTIALS_FILE` file,
which in most cases is `~/.aws/credentials`. At a minimum, you will want this.

```
[default]
output = json
region = us-east-1
aws_access_key_id = 
aws_secret_access_key = 

[saml]
output = json
```

## Connection Profile Generation

This is a simple script that generates a connection profile for a network.

### Installation
Like the AWS SAML Authentication script, this script relies on `boto3`. You can iehter reuse the environment you generated for the NIST AWS SAML Authentication script, or install boto3 with `pip install --user boto3`.

### Usage
```
cd path/to/blossom
./util/gen-connection-profile.py --network_id <network id> --channels <channel 1> <channel 2>
```
Note that the ID described here is NOT the network "name". It should look like `n-...`.
