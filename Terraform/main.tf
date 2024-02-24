provider "aws" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
  token      = var.session_token
}

resource "aws_lambda_function" "my_lambda_function" {
  filename      = "${path.module}/lambda_function/aws_lambda.zip"  
  function_name = "aws_lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "aws_lambda.lambda_handler"      
  runtime       = "python3.11"         
}


data "archive_file" "zip_the_python_code" {
 type        = "zip"
 source_dir  = "${path.module}/lambda_function/"
 output_path = "${path.module}/lambda_function/aws_lambda.zip"
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda_role"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "secrets_manager_policy" {
  name        = "SecretsManagerPolicy"
  description = "IAM policy to allow read access to Secrets Manager secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = "arn:aws:secretsmanager:us-east-1:309085972162:secret:rds!db-32b4142f-1543-4a41-b3f0-d8e4a4672cb0-b7je2m"  
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_manager_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.secrets_manager_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_rds_access_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
}

resource "aws_lambda_layer_version" "python311-requests-layer" {
  filename = "${path.module}/layers/python_requests.zip"
  layer_name = "python_libraries"
  source_code_hash = "${filebase64sha256("${path.module}/layers/python_requests.zip")}"
  compatible_runtimes = ["python3.11"]
  
}