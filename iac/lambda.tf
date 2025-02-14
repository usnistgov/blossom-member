locals {
  # the output zip file containing the packaged lambda contents
  lambda_outpath = "lambda.zip"
  # the output directory for the built lambda
  lambda_builddir = "lambda/dist"

  connection_profile_path = "${path.module}/connection_profiles/${terraform.workspace}.json"
}

# This bucket stores the lambda's build artifacts
module "lambda_bucket" {
  source               = "terraform-aws-modules/s3-bucket/aws"
  version              = "4.1.0"
  bucket               = "${local.prefix}-lambda"
  tags                 = local.tags
  # acl                  = "private"
  # attach_public_policy = false
  # block_public_acls    = true

  # Allow deletion of non-empty bucket
  # force_destroy = true 
}


resource "aws_lambda_function" "query" {
  runtime          = "nodejs20.x"
  function_name    = "${local.prefix}-lambda"
  memory_size      = 512
  publish          = true
  s3_bucket        = aws_s3_object.query_lambda.bucket
  s3_key           = aws_s3_object.query_lambda.key
  handler          = "index.handler"
  source_code_hash = data.archive_file.query_lambda.output_base64sha256
  role             = data.aws_iam_role.lambda_role.arn
  tags             = local.tags
  timeout          = 300
  vpc_config {
    subnet_ids = [
      "subnet-0e55c3a77dad7f698",
      "subnet-09e992c8f703e3662",
    ]
    security_group_ids = [
      # "sg-0b94936c423b8e9ee",
      # "sg-064e0191188232c57"
      "sg-0684c5e7745022782",
      "sg-0fd219d83dfeb68ff",
    ]
  }
  
  environment {
    # ugly ternary that optionally adds HFC_LOGGING to lambda if hlf_debug variable is set
    variables = merge({
      CHANNEL_NAME    = module.vars.env.channel_name
      CONTRACT_NAME   = module.vars.env.contract_name

      ALL_CHANNELS    = module.vars.env.all_channels
      ALL_CONTRACTS   = module.vars.env.all_contracts

      PROFILE_ENCODED = filebase64(local.connection_profile_path)
      SSM_PREFIX      = module.vars.env.identities_ssm_prefix

      }, var.hlf_debug ? {
      HFC_LOGGING = "{\"debug\":\"console\",\"error\":\"console\",\"info\":\"console\",\"warning\":\"console\"}"
    } : {})
  }
}

# NIST OISM team manages IAM roles externally, consult docs for details
data "aws_iam_role" "lambda_role" {
  name = module.vars.env.lambda_execution_iam_role_name
}

data "archive_file" "query_lambda" {
  type        = "zip"
  source_dir  = local.lambda_builddir
  output_path = local.lambda_outpath
}

resource "aws_s3_object" "query_lambda" {
  bucket = module.lambda_bucket.s3_bucket_id

  key    = "lambda.zip"
  source = data.archive_file.query_lambda.output_path
  tags   = local.tags
}
