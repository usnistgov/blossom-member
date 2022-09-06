module "lambda_bucket" {
  source = "../infrastructure/terraform/modules/aws/s3"
  # attach_public_policy = var.attach_public_policy
  bucket               = "${local.prefix}-lambda"
  tags                 = local.tags
  acl                  = "private"
  attach_public_policy = false
  block_public_acls    = true
  # server_side_encryption_configuration = try(lookup(var.server_side_encryption_configuration, "rule"), {
  #   "rule" : {
  #     "apply_server_side_encryption_by_default" : {
  #       "sse_algorithm" : "aws:kms"
  #       "kms_master_key_id" : data.aws_kms_alias.s3.arn
  #     }
  #   }
  # })
}

resource "aws_lambda_function" "query" {
  runtime          = "nodejs16.x"
  function_name    = "handler"
  s3_bucket        = aws_s3_object.query_lambda.bucket
  s3_key           = aws_s3_object.query_lambda.key
  handler          = "handler.handle"
  source_code_hash = data.archive_file.query_lambda.output_base64sha256
  role             = data.aws_iam_role.lambda_role.arn
  tags             = local.tags
  environment {
    variables = {
      CHANNEL_NAME    = module.vars.env.channel_name
      CONTRACT_NAME   = module.vars.env.contract_name
      PROFILE_ENCODED = filebase64("${path.module}/conn-profile-${module.vars.env.network_name}-${module.vars.env.member_name}.yaml")
    }
  }
}

locals {
  lambda_filename = "lambda.zip"
}

data "aws_iam_role" "lambda_role" {
  name = "nistitlblossom-auto-tagging-lambda-role"
}

data "archive_file" "query_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/${local.lambda_filename}"
}

resource "aws_s3_object" "query_lambda" {
  bucket = module.lambda_bucket.s3_bucket_id

  key    = local.lambda_filename
  source = data.archive_file.query_lambda.output_path
  tags   = local.tags
  etag   = filesha1(data.archive_file.query_lambda.output_path)
}
