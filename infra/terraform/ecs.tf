resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-cluster"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "auth_service" {
  name              = "/ecs/${var.project_name}/auth-service"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-auth-service-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "qa_service" {
  name              = "/ecs/${var.project_name}/qa-service"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-qa-service-logs"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "auth_service" {
  family                   = "${var.project_name}-auth-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "auth-service"
    image = "${aws_ecr_repository.auth_service.repository_url}:latest"

    portMappings = [{
      containerPort = 8001
      protocol      = "tcp"
    }]

    environment = [
      { name = "APP_ENV", value = "production" },
      { name = "APP_PORT", value = "8001" },
      { name = "JWT_ALGORITHM", value = "HS256" },
      { name = "JWT_EXPIRY_MINUTES", value = "30" },
      { name = "DATABASE_URL", value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.auth.endpoint}/auth_db" },
      { name = "JWT_SECRET_KEY", value = var.jwt_secret_key }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.auth_service.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    essential = true
  }])

  tags = {
    Name        = "${var.project_name}-auth-service"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "qa_service" {
  family                   = "${var.project_name}-qa-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "qa-service"
    image = "${aws_ecr_repository.qa_service.repository_url}:latest"

    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]

    environment = [
      { name = "APP_ENV", value = "production" },
      { name = "APP_PORT", value = "8000" },
      { name = "JWT_ALGORITHM", value = "HS256" },
      { name = "DATABASE_URL", value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.qa.endpoint}/qa_db" },
      { name = "JWT_SECRET_KEY", value = var.jwt_secret_key },
      { name = "GROQ_API_KEY", value = var.groq_api_key },
      { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.qa_service.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    essential = true
  }])

  tags = {
    Name        = "${var.project_name}-qa-service"
    Environment = var.environment
  }
}

resource "aws_ecs_service" "auth_service" {
  name            = "${var.project_name}-auth-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.auth_service.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.auth_service.arn
    container_name   = "auth-service"
    container_port   = 8001
  }

  depends_on = [aws_lb_listener.main]

  tags = {
    Name        = "${var.project_name}-auth-service"
    Environment = var.environment
  }
}

resource "aws_ecs_service" "qa_service" {
  name            = "${var.project_name}-qa-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.qa_service.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.qa_service.arn
    container_name   = "qa-service"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.main]

  tags = {
    Name        = "${var.project_name}-qa-service"
    Environment = var.environment
  }
}
