provider "aws" {
  region = var.region
}

# VPC & Subnets
resource "aws_default_vpc" "main_vpc" {}

resource "aws_default_subnet" "subnet_us_east_1a" {
  availability_zone = "us-east-1a"
}

resource "aws_default_subnet" "subnet_us_east_1b" {
  availability_zone = "us-east-1b"
}

resource "aws_default_subnet" "subnet_us_east_1c" {
  availability_zone = "us-east-1c"
}

# SSL Certificate
resource "aws_acm_certificate" "ssl_cert" {
  domain_name       = var.custom_domain_name
  validation_method = "DNS"
  tags = {
    Name = "cloudysky.env-cert"
  }
}

resource "aws_route53_record" "ssl_cert_validation_record" {
  zone_id = var.hosted_zone_id
  name    = tolist(aws_acm_certificate.ssl_cert.domain_validation_options)[0].resource_record_name
  type    = tolist(aws_acm_certificate.ssl_cert.domain_validation_options)[0].resource_record_type
  records = [tolist(aws_acm_certificate.ssl_cert.domain_validation_options)[0].resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "ssl_cert_validation" {
  certificate_arn         = aws_acm_certificate.ssl_cert.arn
  validation_record_fqdns = [aws_route53_record.ssl_cert_validation_record.fqdn]
}

data "aws_ecr_repository" "sandbox_repo" {
  name = "sandbox"
}

# ECS Resources
resource "aws_ecs_cluster" "sandbox_cluster" {
  name = "sandbox-cluster"
}

# Add Cloudwatch Logs
resource "aws_cloudwatch_log_group" "sandbox_log_group" {
  name              = "/ecs/sandbox"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "sandbox_task" {
  family                = "sandbox-task"
  container_definitions = <<-DEFINITION
  [
    {
      "name": "sandbox-container",
      "image": "${data.aws_ecr_repository.sandbox_repo.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000
        }
      ],
      "memory": 512,
      "cpu": 256,
      "environment": [
        {
          "name": "BASE_URL",
          "value": "https://sandbox.cloudysky.link"
        },
        {
          "name": "DB_HOSTNAME",
          "value": "2iabtwondlw2bni7uxse6lobte.dsql.us-east-1.on.aws"
        },
        {
          "name": "DB_PORT",
          "value": "5432"
        }
      ],
      "secrets": [
        {
          "name": "GOOGLE_CLIENT_ID",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:273509275056:secret:google_client_id-ZqrjPm"
        },
        {
          "name": "GOOGLE_CLIENT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:273509275056:secret:GOOGLE_CLIENT_SECRET-6Y9PsM"
        },
        {
          "name": "SESSION_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:273509275056:secret:SESSION_SECRET_KEY-tcSf7N"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${aws_cloudwatch_log_group.sandbox_log_group.name}",
          "awslogs-region": "${var.region}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/api/ || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
  DEFINITION

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
}

data "aws_iam_policy_document" "ecs_role_assumption" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}





resource "aws_iam_role" "ecs_execution_role" {
  name               = "sandbox-ECSTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_role_assumption.json
}

resource "aws_iam_role" "ecs_task_role" {
  name               = "sandbox-ECSTaskRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_role_assumption.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_attach_cloudwatch" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_policy" "sandbox_bedrock" {
  name        = "sandbox-ecs-task-policy-bedrock"
  description = "Policy that allows access to Bedrock"
  policy      = <<EOF
{
   "Version": "2012-10-17",
   "Statement": [
       {
           "Effect": "Allow",
           "Action": [
                "bedrock:*"
           ],
           "Resource": "*"
       }
   ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_attach_bedrock" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.sandbox_bedrock.arn
}

resource "aws_iam_policy" "aurora_dsql" {
  name        = "ecs-task-policy-dsql"
  description = "Policy that allows access to Aurora DSQL"
  policy      = <<EOF
{
   "Version": "2012-10-17",
   "Statement": [
       {
           "Effect": "Allow",
           "Action": [
                "dsql:DbConnectAdmin"
           ],
           "Resource": "*"
       }
   ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_attach_dsql" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.aurora_dsql.arn
}

resource "aws_iam_policy" "cloudformation" {
  name        = "ecs-task-policy-cf"
  description = "Policy that allows access to Cloudformation"
  policy      = <<EOF
{
   "Version": "2012-10-17",
   "Statement": [
       {
           "Effect": "Allow",
           "Action": [
                "cloudformation:*"
           ],
           "Resource": "*"
       }
   ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_attach_cf" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.cloudformation.arn
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy_attach" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_execution_role_policy_attach_sm" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = [
      "arn:aws:secretsmanager:us-east-1:273509275056:secret:google_client_id-ZqrjPm",
      "arn:aws:secretsmanager:us-east-1:273509275056:secret:GOOGLE_CLIENT_SECRET-6Y9PsM",
      "arn:aws:secretsmanager:us-east-1:273509275056:secret:SESSION_SECRET_KEY-tcSf7N"
    ]
  }
}

resource "aws_iam_role_policy" "ecs_execution_role_policy_sm" {
  name   = "ecs-execution-role-policy-sm"
  role   = aws_iam_role.ecs_execution_role.id
  policy = data.aws_iam_policy_document.ecs_execution_role_policy_attach_sm.json
}

# ALB & Security Groups
resource "aws_security_group" "sandbox_alb_sg" {
  name = "sandbox-alb-SecurityGroup"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_alb" "sandbox_alb" {
  name               = "sandbox-ALB"
  load_balancer_type = "application"
  subnets = [
    aws_default_subnet.subnet_us_east_1a.id,
    aws_default_subnet.subnet_us_east_1b.id,
    aws_default_subnet.subnet_us_east_1c.id
  ]
  security_groups = [aws_security_group.sandbox_alb_sg.id]
}

resource "aws_lb_target_group" "sandbox_tg" {
  name        = "sandbox-TargetGroup"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_default_vpc.main_vpc.id

  health_check {
    path                = "/api/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-299"
  }
}

resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_alb.sandbox_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate_validation.ssl_cert_validation.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.sandbox_tg.arn
  }
}

# Route53 Record
resource "aws_route53_record" "sandbox_domain_record" {
  zone_id = var.hosted_zone_id
  name    = var.custom_domain_name
  type    = "A"

  alias {
    name                   = aws_alb.sandbox_alb.dns_name
    zone_id                = aws_alb.sandbox_alb.zone_id
    evaluate_target_health = false
  }
}

# ECS Service
resource "aws_ecs_service" "sandbox_service" {
  name                 = "sandbox-Service"
  cluster              = aws_ecs_cluster.sandbox_cluster.id
  task_definition      = aws_ecs_task_definition.sandbox_task.arn
  launch_type          = "FARGATE"
  desired_count        = 1
  force_new_deployment = true

  load_balancer {
    target_group_arn = aws_lb_target_group.sandbox_tg.arn
    container_name   = "sandbox-container"
    container_port   = 8000
  }

  network_configuration {
    subnets          = [aws_default_subnet.subnet_us_east_1a.id, aws_default_subnet.subnet_us_east_1b.id, aws_default_subnet.subnet_us_east_1c.id]
    assign_public_ip = true
    security_groups  = [aws_security_group.ecs_service_sg.id]
  }
}

resource "aws_security_group" "ecs_service_sg" {
  name = "sandbox-ecs-service-securityGroup"
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.sandbox_alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
