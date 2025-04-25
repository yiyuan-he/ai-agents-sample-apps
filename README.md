# AI Agents Sample Apps
This repo contains Agentic AI applications instrumented using third-party OpenTelemetry libraries. When running the application, the [ADOT Python SDK](https://github.com/aws-observability/aws-otel-python-instrumentation) will automatically forward the span/trace data to the [OTLP X-Ray endpoint](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLPEndpoint.html) providing enhanced observability for your AI systems within AWS CloudWatch.

Instructions for how to setup and run each sample app can be found in each subdirectory: `./<framework>-poc/<instrumentation_sdk>`

![image](https://github.com/user-attachments/assets/75759adc-9aef-455f-90bd-f8b56562b465)
