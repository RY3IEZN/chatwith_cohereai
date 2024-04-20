import json
import boto3

# import resourecs
client = boto3.client("bedrock-runtime")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("chat_response_db")

# check the version of boto3
print(boto3.__version__, "<- boto3 version")


def lambda_handler(event, context):
    # the prompt will be recieved as an event from api-gw
    print(event)
    user_prompt = event["user_prompt"]

    # create a response object,should be in json format
    response = client.invoke_model(
        accept="application/json",
        contentType="application/json",
        modelId="cohere.command-text-v14",
        body=json.dumps(
            {
                "prompt": user_prompt,
                "max_tokens": 20,
                "temperature": 0.9,
            }
        ),
    )
    print(response["body"])
    # convert the response body to bytes, then back to string
    response_byte = response["body"].read()
    response_string = json.loads(response_byte)

    # Extract AI response from the response
    ai_response = response_string["generations"][0]["text"]

    # Store user prompt and AI response in DynamoDB table
    response_db = table.put_item(
        Item={"user_prompt": user_prompt, "ai_response": ai_response}
    )

    print(response_db)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"response_db": response_db, "response_string": response_string}
        ),
    }
