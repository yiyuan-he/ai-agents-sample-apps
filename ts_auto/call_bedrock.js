"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.lambdaHandler = lambdaHandler;
const client_bedrock_runtime_1 = require("@aws-sdk/client-bedrock-runtime");
console.log('Loading function');
async function lambdaHandler(event, context) {
    console.log("Received event: " + JSON.stringify(event, null, 2));
    console.log("Context: " + JSON.stringify(context));
    const inputStr = event.input;
    const modelStr = event.model;
    // Initialize the Bedrock Runtime client
    const bedrockRuntime = new client_bedrock_runtime_1.BedrockRuntimeClient({ region: 'us-east-1' });
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
        const command = new client_bedrock_runtime_1.InvokeModelCommand({
            modelId: modelId,
            contentType: 'application/json',
            accept: 'application/json',
            body: JSON.stringify(requestBody)
        });
        const response = await bedrockRuntime.send(command);
        // Parse and return the response
        const responseBody = JSON.parse(new TextDecoder().decode(response.body));
        // Debug print to see the actual response structure
        console.log("Response body:", JSON.stringify(responseBody, null, 2));
        return {
            statusCode: 200,
            body: JSON.stringify(responseBody.content[0].text)
        };
    }
    catch (e) {
        console.error(`Error invoking Bedrock model: ${e}`);
        return {
            statusCode: 500,
            body: JSON.stringify(`Error: ${e}`)
        };
    }
}
async function main() {
    try {
        const result = await lambdaHandler({}, {});
        console.log(result);
    }
    catch (error) {
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
