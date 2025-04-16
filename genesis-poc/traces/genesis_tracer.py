import os
import uuid
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from traces.cw_exporter import CloudWatchExporter  # You'll need to implement this
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from dotenv import load_dotenv

class GenesisTracer:

    _instance = None

    def __new__(cls, service_name=None):
        if not cls._instance:
            cls._instance = super(GenesisTracer, cls).__new__(cls)
            cls._instance._initiate(service_name)
        return cls._instance
    
    def _initiate(self, service_name):
        """Initialize the tracer with CloudWatch integration"""
        load_dotenv()
        self.tracer_provider = None
        self.service_name = service_name

        # Set up the tracer provider
        self.tracer_provider = TracerProvider()
        trace.set_tracer_provider(self.tracer_provider)

        self.tracer = trace.get_tracer(self.service_name)
            
        # Create and register exporters
        self._register_exporters()

    def get_tracer_provider(self):
        """Get the tracer instance"""
        return self.tracer_provider
    
    def get_tracer(self):
        """Get the tracer instance"""
        return self.tracer

    def configure(self, **kwargs):
        """Configure tracer settings"""
        
        # Configure CloudWatch settings
        cw_config = kwargs.get('cloudwatch_config', {
            'log_group_name': '/aws/langchain/traces',
            'log_stream_name': 'production',
            'region': 'us-west-2'
        })
        self._configure_cloudwatch(**cw_config)
        
    def _register_exporters(self):
        """Register span processors and exporters"""        
        # Create and register CloudWatch exporter
        cloudwatch_exporter = CloudWatchExporter(
            log_group_name=f"/aws/otel/{self.service_name}",
            log_stream_name="traces_" + str(uuid.uuid4())
        )
        self.tracer_provider.add_span_processor(
            BatchSpanProcessor(cloudwatch_exporter)
        )

        self.tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    def _configure_cloudwatch(self, **kwargs):
        """Configure CloudWatch specific settings"""
        log_group = kwargs.get('log_group_name')
        log_stream = kwargs.get('log_stream_name')
        region = kwargs.get('region', 'us-west-2')
        
        # Update CloudWatch configuration
        if log_group:
            os.environ['OTEL_CLOUDWATCH_LOG_GROUP'] = log_group
        if log_stream:
            os.environ['OTEL_CLOUDWATCH_LOG_STREAM'] = log_stream
        if region:
            os.environ['AWS_REGION'] = region
