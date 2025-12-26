#!/bin/bash
set -e

echo "=== Big Data Platform Demo: Spark -> Iceberg -> Trino ==="

# Get the namespace (default to default)
NAMESPACE=${NAMESPACE:-default}
RELEASE_NAME=${RELEASE_NAME:-dataplane}

# Service names
MINIO_SVC="${RELEASE_NAME}-minio"
TRINO_SVC="${RELEASE_NAME}-trino"
ICEBERG_CATALOG_SVC="${RELEASE_NAME}-iceberg-catalog"

echo "Using namespace: ${NAMESPACE}"
echo "Release name: ${RELEASE_NAME}"

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n ${NAMESPACE} --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=trino -n ${NAMESPACE} --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=iceberg-catalog -n ${NAMESPACE} --timeout=300s || true

echo ""
echo "Services are ready!"

# Get MinIO endpoint
MINIO_ENDPOINT="http://${MINIO_SVC}:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"

# Get Trino endpoint
TRINO_ENDPOINT="http://${TRINO_SVC}:8080"

# Get Iceberg catalog endpoint
ICEBERG_CATALOG_ENDPOINT="http://${ICEBERG_CATALOG_SVC}:8181"

echo ""
echo "MinIO endpoint: ${MINIO_ENDPOINT}"
echo "Trino endpoint: ${TRINO_ENDPOINT}"
echo "Iceberg catalog endpoint: ${ICEBERG_CATALOG_ENDPOINT}"

# Step 1: Create a SparkApplication that writes data to Iceberg
echo ""
echo "=== Step 1: Creating SparkApplication to write Iceberg table ==="

cat <<EOF | kubectl apply -f -
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: spark-iceberg-write-demo
  namespace: ${NAMESPACE}
spec:
  type: Scala
  mode: cluster
  image: "apache/spark-py:3.5.0"
  imagePullPolicy: Always
  mainClass: org.apache.spark.sql.SparkSession
  mainApplicationFile: "local:///opt/spark/examples/jars/spark-examples_2.12-3.5.0.jar"
  sparkVersion: "3.5.0"
  restartPolicy:
    type: Never
  driver:
    cores: 1
    coreLimit: "1200m"
    memory: "512m"
    labels:
      version: 3.5.0
    serviceAccount: ${RELEASE_NAME}-spark-operator
  executor:
    cores: 1
    instances: 1
    memory: "512m"
    labels:
      version: 3.5.0
  sparkConf:
    "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
    "spark.sql.catalog.demo": "org.apache.iceberg.spark.SparkCatalog"
    "spark.sql.catalog.demo.type": "rest"
    "spark.sql.catalog.demo.uri": "${ICEBERG_CATALOG_ENDPOINT}"
    "spark.sql.catalog.demo.io-impl": "org.apache.iceberg.aws.s3.S3FileIO"
    "spark.sql.catalog.demo.s3.endpoint": "${MINIO_ENDPOINT}"
    "spark.sql.catalog.demo.s3.access-key-id": "${MINIO_ACCESS_KEY}"
    "spark.sql.catalog.demo.s3.secret-access-key": "${MINIO_SECRET_KEY}"
    "spark.sql.catalog.demo.s3.path-style-access": "true"
  arguments:
    - "--conf"
    - "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
    - "--conf"
    - "spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog"
    - "--conf"
    - "spark.sql.catalog.demo.type=rest"
    - "--conf"
    - "spark.sql.catalog.demo.uri=${ICEBERG_CATALOG_ENDPOINT}"
    - "--conf"
    - "spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO"
    - "--conf"
    - "spark.sql.catalog.demo.s3.endpoint=${MINIO_ENDPOINT}"
    - "--conf"
    - "spark.sql.catalog.demo.s3.access-key-id=${MINIO_ACCESS_KEY}"
    - "--conf"
    - "spark.sql.catalog.demo.s3.secret-access-key=${MINIO_SECRET_KEY}"
    - "--conf"
    - "spark.sql.catalog.demo.s3.path-style-access=true"
EOF

echo "Waiting for SparkApplication to complete..."
kubectl wait --for=condition=completed sparkapplication/spark-iceberg-write-demo -n ${NAMESPACE} --timeout=600s || {
    echo "SparkApplication failed or timed out"
    kubectl describe sparkapplication spark-iceberg-write-demo -n ${NAMESPACE}
    exit 1
}

echo "SparkApplication completed successfully!"

# Step 2: Query the table using Trino
echo ""
echo "=== Step 2: Querying Iceberg table with Trino ==="

# Note: In a real scenario, we would use a Trino client or REST API
# For this demo, we'll show how to do it via kubectl exec
echo "To query with Trino, you can:"
echo "1. Port-forward Trino: kubectl port-forward svc/${TRINO_SVC} 8080:8080 -n ${NAMESPACE}"
echo "2. Use Trino CLI or REST API to query:"
echo "   SELECT * FROM demo.default.demo_table;"

echo ""
echo "=== Demo completed! ==="
echo ""
echo "Next steps:"
echo "- Check SparkApplication logs: kubectl logs spark-iceberg-write-demo-driver -n ${NAMESPACE}"
echo "- Query Trino: kubectl exec -it <trino-pod> -n ${NAMESPACE} -- trino-cli --server ${TRINO_ENDPOINT}"
echo "- Access MinIO console: kubectl port-forward svc/${MINIO_SVC} 9001:9001 -n ${NAMESPACE}"




