locals {
  content_type_map = {
    "html" = "text/html"
    "css"  = "text/css"
    "js"   = "text/javascript"
    "png"  = "image/png"
    "ico"  = "image/x-icon"
    "svg"  = "image/svg+xml"
    "txt"  = "text/plain"
    "json" = "application/json"
    "map"  = "application/json"
  }
  webcontent_builddir = "${path.module}/../../blossom-dashboard/dist"
}

output "vite_dev_env" {
  value       = <<-EOT
  VITE_CLIENT_ID=${resource.aws_cognito_user_pool_client.client.id}
  VITE_CLIENT_SECRET=${resource.aws_cognito_user_pool_client.client.client_secret}
  VITE_AUTH_URL=https://${local.cognito_domain_prefix}.auth.${var.aws_region}.amazoncognito.com
  PROXY_URL=${local.apigw_url}
  EOT
  description = "The developer environment used by the dashboard"
  sensitive   = true
}

output "vite_prod_env" {
  value       = <<-EOT
  VITE_CLIENT_ID=${resource.aws_cognito_user_pool_client.client.id}
  VITE_CLIENT_SECRET=${resource.aws_cognito_user_pool_client.client.client_secret}
  VITE_AUTH_URL=https://${local.cognito_domain_prefix}.auth.${var.aws_region}.amazoncognito.com
  BASE_URL=/${aws_api_gateway_stage.gw-stage.stage_name}/
  EOT
  description = "The production environment used by the dashboard"
  sensitive   = true
}

# # [3:45 PM] Lee, Li-Hui (Fed)
# # take out this too, "attach_public_policy = false"
# # [3:46 PM] Lee, Li-Hui (Fed)
# # or don't use the "terraform-aws-modules/s3-bucket/aws" module to create the bucket
# #
# # [3:47 PM] Lee, Li-Hui (Fed)
# # use terraform Resource: aws_s3_bucket instead
# # resource "aws_s3_bucket" "s3_content_bucket" {
# #     bucket = "${local.prefix}-content"
# #     tags     = local.tags
# #     }
# #     
# #    

module "s3_content_bucket" {
  source               = "terraform-aws-modules/s3-bucket/aws"
  version              = "4.1.0"
  bucket               = "${local.prefix}-content"
  tags                 = local.tags
  # acl                  = "private"
  # attach_public_policy = false
  # block_public_acls    = true

  # Allow deletion of non-empty bucket
  force_destroy = true
}

# resource "aws_s3_bucket" "s3_content_bucket" {
#   bucket = "${local.prefix}-content"
#   tags     = local.tags
# }

resource "aws_s3_object" "web-content" {
  bucket   = module.s3_content_bucket.s3_bucket_id
  for_each = fileset(local.webcontent_builddir, "**/*")
  key      = each.value
  source   = "${local.webcontent_builddir}/${each.value}"
  etag     = filemd5("${local.webcontent_builddir}/${each.value}")
  tags = merge({
    "Purpose" = "blossom-frontend"
  }, local.tags)
  # extract the extension, apply it to the content_type_map
  content_type = local.content_type_map[split(".", each.value)[length(split(".", each.value)) - 1]]
}
