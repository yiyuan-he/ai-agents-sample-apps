import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";

console.log('Loading function');

interface Event {
  input?: string;
  model?: string;
}

interface Context {
  // AWS Lambda context properties would go here
  // For simplicity, we're using an empty interface
}

interface BedrockResponse {
  content: {
    type: string;
    text: string;
  }[];
  // Other response fields would be defined here
}

interface LambdaResponse {
  statusCode: number;
  body: string;
}

async function lambdaHandler(event: Event, context: Context): Promise<LambdaResponse> {
  console.log("Received event: " + JSON.stringify(event, null, 2));
  console.log("Context: " + JSON.stringify(context));
  
  const inputStr = event.input;
  const modelStr = event.model;

  // Initialize the Bedrock Runtime client
  const bedrockRuntime = new BedrockRuntimeClient({ region: 'us-east-1' });
  
  // Define the model ID and input text
  const modelId = modelStr || 'us.anthropic.claude-3-5-sonnet-20241022-v2:0';
  const inputText = inputStr || "Please explain the concept of cloud computing.";
  
  // Prepare the request body
  const requestBody = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 300,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: inputText
          }
        ]
      }
    ],
    temperature: 0.5,
    top_p: 1
  };
  
  try {
    // Invoke the Bedrock model
    const command = new InvokeModelCommand({
      modelId: modelId,
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify(requestBody)
    });
    
    const response = await bedrockRuntime.send(command);
    
    // Parse and return the response
    const responseBody = JSON.parse(new TextDecoder().decode(response.body)) as BedrockResponse;
    
    // Debug print to see the actual response structure
    console.log("Response body:", JSON.stringify(responseBody, null, 2));
    
    return {
      statusCode: 200,
      body: JSON.stringify(responseBody.content[0].text)
    };
  } catch (e) {
    console.error(`Error invoking Bedrock model: ${e}`);
    return {
      statusCode: 500,
      body: JSON.stringify(`Error: ${e}`)
    };
  }
}

async function main(): Promise<void> {
  try {
    const result = await lambdaHandler({}, {});
    console.log(result);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}

export { lambdaHandler };
