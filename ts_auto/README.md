npm install


npm install @aws/aws-distro-opentelemetry-node-autoinstrumentation


export NODE_OPTIONS="--require @aws/aws-distro-opentelemetry-node-autoinstrumentation/register" 


env OTEL_METRICS_EXPORTER=none \
OTEL_LOGS_EXPORTER=none \
OTEL_TRACES_EXPORTER=console,otlp \
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
OTEL_RESOURCE_ATTRIBUTES="service.name=test_app" \
npx ts-node  call_bedrock.ts