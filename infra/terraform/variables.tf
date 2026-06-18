variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ca-central-1"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "ai-qa-microservice"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
}
