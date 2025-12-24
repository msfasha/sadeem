#!/bin/bash
# Demo script: Spark writes Iceberg table -> Trino reads it
# Prerequisites: dataplane Helm chart deployed, kubectl configured

set -e

echo "=== Spark -> Iceberg -> Trino Demo ==="

# Wait for services to be ready
echo "Waiting for services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/minio || true
kubectl wait --for=condition=available --timeout=300s deployment/postgres || true
kubectl wait --for=condition=available --timeout=300s deployment/iceberg-catalog || true
kubectl wait --for=condition=available --timeout=300s deployment/trino-coordinator || true

# Get service endpoints
MINIO_ENDPOINT="http://minio:9000"
TRINO_ENDPOINT="http://trino-coordinator:8080"
ICEBERG_CATALOG_URI="http://iceberg-catalog:8181"

echo "MinIO endpoint: $MINIO_ENDPOINT"
echo "Trino endpoint: $TRINO_ENDPOINT"
echo "Iceberg catalog URI: $ICEBERG_CATALOG_URI"

# Step 1: Create a Spark job that writes an Iceberg table
echo ""
echo "=== Step 1: Creating Spark job to write Iceberg table ==="

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: spark-write-iceberg-demo
spec:
  template:
    spec:
      serviceAccountName: spark
      containers:
      - name: spark-submit
        image: apache/spark-py:3.5.0
        command:
        - /bin/bash
        - -c
        - |
          pip install pyiceberg
          python3 <<PYTHON
          from pyspark.sql import SparkSession
          from pyspark.sql.types import StructType, StructField, StringType, IntegerType
          
          spark = SparkSession.builder \\
              .appName("IcebergWriteDemo") \\
              .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \\
              .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \\
              .config("spark.sql.catalog.iceberg.type", "rest") \\
              .config("spark.sql.catalog.iceberg.uri", "$ICEBERG_CATALOG_URI") \\
              .config("spark.sql.catalog.iceberg.warehouse", "s3://warehouse/") \\
              .config("spark.hadoop.fs.s3a.endpoint", "$MINIO_ENDPOINT") \\
              .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \\
              .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \\
              .config("spark.hadoop.fs.s3a.path.style.access", "true") \\
              .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \\
              .getOrCreate()
          
          # Create sample data
          data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
          schema = StructType([
              StructField("name", StringType(), True),
              StructField("age", IntegerType(), True)
          ])
          df = spark.createDataFrame(data, schema)
          
          # Write to Iceberg
          df.write \\
              .format("iceberg") \\
              .mode("overwrite") \\
              .save("iceberg.default.demo_users")
          
          print("Successfully wrote Iceberg table: iceberg.default.demo_users")
          spark.stop()
          PYTHON
        env:
        - name: SPARK_HOME
          value: "/opt/spark"
      restartPolicy: Never
EOF

echo "Waiting for Spark job to complete..."
kubectl wait --for=condition=complete --timeout=600s job/spark-write-iceberg-demo || kubectl logs job/spark-write-iceberg-demo

# Step 2: Query from Trino
echo ""
echo "=== Step 2: Querying Iceberg table from Trino ==="

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: trino-query-demo
spec:
  template:
    spec:
      containers:
      - name: trino-cli
        image: trinodb/trino:451
        command:
        - /bin/bash
        - -c
        - |
          trino --server $TRINO_ENDPOINT --execute "
          SHOW CATALOGS;
          SHOW SCHEMAS FROM iceberg;
          SHOW TABLES FROM iceberg.default;
          SELECT * FROM iceberg.default.demo_users;
          "
      restartPolicy: Never
EOF

echo "Waiting for Trino query job to complete..."
kubectl wait --for=condition=complete --timeout=300s job/trino-query-demo || kubectl logs job/trino-query-demo

echo ""
echo "=== Demo completed! ==="
echo "Check logs:"
echo "  kubectl logs job/spark-write-iceberg-demo"
echo "  kubectl logs job/trino-query-demo"

