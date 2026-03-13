#!/bin/bash

set -e

# Variables
CLUSTER_NAME="customer-analysis-cluster"
REGION="us-east-1"
PROFILE="aws-academy"
DB_INSTANCE_ID="sentiments-db"
DB_NAME="sentiments"
DB_USERNAME="postgres"
DB_PASSWORD="postgres123"
DB_INSTANCE_CLASS="db.t3.micro"
ALLOCATED_STORAGE="20"
SG_NAME="rds-postgres-sg"

echo "=== Creating RDS PostgreSQL Database ==="

# Obtener VPC ID del cluster EKS
echo "Getting VPC ID from EKS cluster..."
VPC_ID=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --profile $PROFILE --query 'cluster.resourcesVpcConfig.vpcId' --output text)
echo "VPC ID: $VPC_ID"

# Obtener CIDR block de la VPC
VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --region $REGION --profile $PROFILE --query 'Vpcs[0].CidrBlock' --output text)
echo "VPC CIDR: $VPC_CIDR"

# Crear Security Group para RDS
echo "Creating security group for RDS..."
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
    --region $REGION \
    --profile $PROFILE \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    echo "Security group does not exist. Creating new one..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SG_NAME \
        --description "Security group for RDS PostgreSQL" \
        --vpc-id $VPC_ID \
        --region $REGION \
        --profile $PROFILE \
        --query 'GroupId' \
        --output text)
    echo "Security Group ID: $SG_ID"
    
    # Agregar regla de ingreso para PostgreSQL desde la VPC
    echo "Adding ingress rule for PostgreSQL..."
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 5432 \
        --cidr $VPC_CIDR \
        --region $REGION \
        --profile $PROFILE
else
    echo "Security group already exists with ID: $SG_ID"
fi


# Obtener subnets privadas del cluster
echo "Getting private subnets..."
SUBNETS=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --profile $PROFILE --query 'cluster.resourcesVpcConfig.subnetIds' --output text)
SUBNET_ARRAY=($SUBNETS)

# Crear DB Subnet Group
echo "Creating DB subnet group..."
SUBNET_GROUP_NAME="${DB_INSTANCE_ID}-subnet-group"

# Verificar si el subnet group ya existe
SUBNET_GROUP_EXISTS=$(aws rds describe-db-subnet-groups \
    --db-subnet-group-name $SUBNET_GROUP_NAME \
    --region $REGION \
    --profile $PROFILE \
    --query 'DBSubnetGroups[0].DBSubnetGroupName' \
    --output text 2>/dev/null || echo "None")

if [ "$SUBNET_GROUP_EXISTS" == "None" ] || [ -z "$SUBNET_GROUP_EXISTS" ]; then
    echo "Subnet group does not exist. Creating new one..."
    aws rds create-db-subnet-group \
        --db-subnet-group-name $SUBNET_GROUP_NAME \
        --db-subnet-group-description "Subnet group for ${DB_INSTANCE_ID}" \
        --subnet-ids ${SUBNET_ARRAY[@]} \
        --region $REGION \
        --profile $PROFILE
    echo "Subnet group created: $SUBNET_GROUP_NAME"
else
    echo "Subnet group already exists: $SUBNET_GROUP_NAME"
fi

# Crear instancia RDS PostgreSQL
echo "Creating RDS PostgreSQL instance..."
aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine postgres \
    --engine-version 17.6 \
    --master-username $DB_USERNAME \
    --master-user-password $DB_PASSWORD \
    --allocated-storage $ALLOCATED_STORAGE \
    --db-name $DB_NAME \
    --vpc-security-group-ids $SG_ID \
    --db-subnet-group-name "${DB_INSTANCE_ID}-subnet-group" \
    --no-publicly-accessible \
    --backup-retention-period 7 \
    --region $REGION \
    --profile $PROFILE

echo "Waiting for RDS instance to be available..."
aws rds wait db-instance-available \
    --db-instance-identifier $DB_INSTANCE_ID \
    --region $REGION \
    --profile $PROFILE

# Obtener endpoint de la base de datos
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --region $REGION \
    --profile $PROFILE \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo ""
echo "=== RDS PostgreSQL Created Successfully ==="
echo "DB Instance ID: $DB_INSTANCE_ID"
echo "DB Endpoint: $DB_ENDPOINT"
echo "DB Name: $DB_NAME"
echo "DB Username: $DB_USERNAME"
echo "DB Password: $DB_PASSWORD"
echo "Security Group ID: $SG_ID"
echo ""
echo "Connection String:"
echo "postgresql://${DB_USERNAME}:${DB_PASSWORD}@${DB_ENDPOINT}:5432/${DB_NAME}"
