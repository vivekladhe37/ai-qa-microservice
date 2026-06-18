output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "auth_service_ecr_url" {
  description = "ECR repository URL for auth service"
  value       = aws_ecr_repository.auth_service.repository_url
}

output "qa_service_ecr_url" {
  description = "ECR repository URL for qa service"
  value       = aws_ecr_repository.qa_service.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}
