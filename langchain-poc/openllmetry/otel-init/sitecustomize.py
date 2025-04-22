import os
import logging
import boto3

# Configure logging for better debugging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("sitecustomize")

# Set your environment variables
os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")
os.environ.setdefault("OTEL_PYTHON_DISTRO", "aws_distro")
os.environ.setdefault("OTEL_PYTHON_CONFIGURATOR", "aws_configurator")
os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
# Get region from boto3 session and use it for X-Ray endpoint
session = boto3.Session()
region = session.region_name or "us-east-1"  # Default to us-east-1 if no region found
os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"https://xray.{region}.amazonaws.com/v1/traces")
os.environ.setdefault("OTEL_RESOURCE_ATTRIBUTES", "service.name=langchain-app")
# Specifically don't disable botocore since it's needed for AWS SigV4 auth
os.environ.setdefault("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS",
                      "http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,urllib3,requests")
os.environ["OTEL_PROPAGATORS"] = "xray,tracecontext,baggage,b3,b3multi"
os.environ["OTEL_PYTHON_ID_GENERATOR"] = "xray"

# Check and log AWS credentials
session = boto3.Session()
credentials = session.get_credentials()
if credentials:
    logger.info(f"AWS credentials found for: {session.get_credentials().access_key[:4]}***")
    logger.info(f"AWS region: {session.region_name}")
else:
    logger.error("No AWS credentials found! X-Ray exporting will fail.")

from amazon.opentelemetry.distro.aws_opentelemetry_distro import AwsOpenTelemetryDistro
from amazon.opentelemetry.distro.aws_opentelemetry_configurator import AwsOpenTelemetryConfigurator
from amazon.opentelemetry.distro.otlp_aws_span_exporter import OTLPAwsSpanExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

logger.info("Initializing AWS OpenTelemetry components...")

# Initialize the distro first (sets up base OpenTelemetry configuration)
distro = AwsOpenTelemetryDistro()
distro._configure(apply_patches=True)
logger.info("AWS OpenTelemetry Distro initialized")

# Initialize the configurator (sets up AWS-specific components)
configurator = AwsOpenTelemetryConfigurator()
configurator._configure()
logger.info("AWS OpenTelemetry Configurator initialized")

# Explicitly create and configure the X-Ray exporter
try:
    # Create a custom exporter with debug logging
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"https://xray.{region}.amazonaws.com/v1/traces")
    logger.info(f"Using X-Ray endpoint: {endpoint}")

    xray_exporter = OTLPAwsSpanExporter(endpoint=endpoint)

    # Get the current tracer provider or create one if it doesn't exist
    tracer_provider = trace.get_tracer_provider()

    # Add the X-Ray exporter
    tracer_provider.add_span_processor(BatchSpanProcessor(xray_exporter))

    # Instrument LangChain
    LangchainInstrumentor().instrument(tracer_provider=tracer_provider)

    logger.info("X-Ray and Console exporters configured, LangChain instrumented")
except Exception as e:
    logger.exception(f"Error configuring X-Ray exporter: {e}")

logger.info("AWS OpenTelemetry components initialized successfully")
