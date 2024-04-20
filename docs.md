<!-- @format -->

Generative AI refers to a class of artificial intelligence techniques that enable computers to generate content, such as images, text, or even music, autonomously. Unlike traditional AI systems that rely on predefined rules or patterns, generative AI models are trained on large datasets and can produce new, original content that closely mimics human creations.

Generative AI Deployment involves implementing generative AI models into real-world applications. This process typically involves integrating the AI model with existing infrastructure, such as cloud services or APIs, to process user inputs and generate relevant outputs. Deploying generative AI effectively requires considerations such as scalability, efficiency, and ethical use of the generated content.

In this guide, I'll walk you through the steps to deploy a generative AI model using serverless infrastructure. We'll make use of serverless technologies such as AWS Lambda, API Gateway, and DynamoDB to efficiently handle user inputs, process them through the AI model, and deliver dynamic outputs.

## Setting up Infrastructure

First, we'll get access to CohereAI through Amazon Bedrock. Next, we will head over to DynamoDB and create a table, storing everything from user inputs to the generated outputs, We'll then create Lambda function that connects seamlessly with CohereAI via Amazon Bedrock. for API Gateway. We'll use it to create an endpoint that'll expose our Lambda function as a RESTful API and also cloudwatch to store the logs of all the activities going on.

NB: Everything will be deployed in us-west-2 (Oregon), and all resources have to be in the same region for it to work seamlessly

### Step 1 Setting up access to AWS Bedrock

Head over to the aws Console and search Bedrock, should be a shiny new green icon that looks like this, select it and click "get started"

![alt](/images/awsbdrk1.JPG)

On the panel on the left select model access and then in the middle click on "manage model access", follow the prompt, select the model you want to use, in this case cohere ai and click request access, it should quickly give you access to use the models, i believe most of them are generally available to the public.

![alt](/images/awsbdrk2.JPG)

You should be granted access fairly quickly and ready to use. Next up storage

### Step 2 Creating the db for storage

Head on to the aws console, search for dynamodb and get started

![alt](/images/awsddb1.JPG)

Click on create table and fill in the details

![alt](/images/awsddb2.JPG)

take note of the name as we will refer to it in the lambda function

![alt](/images/awsddb3.JPG)

Leave the remaining options as default and click create, we should have a fresh db ready to go.

![alt](/images/awsddb4.JPG)

## Step 3a. Create our lambda roles and permission

Before we go running to create our lambda, which is the brains of the operations. we need to give the service permissions to call some other services on our behalf. we will create the following permissions

1. Dynamodb full access: To be able to CRUD the db
1. Cloudwatch full access: To store logs and activities
1. Bedrock Full access: To be able to send and receive information for the bedrock service.

We can do all these at once, so head over to IAM and create a role.

![alt](/images/awsiam1.JPG)

remember the name of the role, so that we can apply it when we are creating the lambda function

## Step 3b. Create our lambda function

Buckle up, as we have a lot to do here. ready? head over to the console and search for lambda, usually the 1st thing to pop up.

![alt](/images/awslamba1.JPG)

Here we are going to author our function, give it a name and set the runtime to a python runtime, NB:Please select a runtime of v3.11, as we need the version of our boto3 to be atleast > v1.28.

![alt](/images/awslamb1.JPG)

Under the permissions section, select an existing execution role, and select the role we created earlier in the IAM section
and then go ahead and create the function

![alt](/images/awslamb2.JPG)

go ahead and click create... and lets get to it

briefly lets check the version of boto3 before we continue

```py
import boto3

print(boto3.__version__, "<- show boto3 version")
```

![alt](/images/awslamb4.JPG)

click on deploy then test, then we should see the outcome in the execution results

![alt](/images/awslamb5.JPG)

Great our boto3 version is okay, we can now proceed to write our actual function, the function will receive the user prompt and send it to aws bedrock which will process it using the cohereAI model and send us a dynamic response.

Now we can replace the code with our actual code.

```py
import json
import boto3

# import resources
client = boto3.client("bedrock-runtime")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("<DynamoDbTableName>")

# check the version of boto3
print(boto3.__version__, "<- boto3 version")

def lambda_handler(event, context):
    # the prompt will be received as an event from api-gw
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

    # Extracting AI response from the response
    ai_response = response_string["generations"][0][
        "text"
    ]

    # Store user prompt and AI response in DynamoDB table
    response_db = table.put_item(
        Item={"user_prompt": user_prompt, "ai_response": ai_response}
    )

    print(response_db)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"response_string": response_string,"response_db": response_db,}
        ),
    }
```

Click on deploy then test, then we should get a response from our model.

![alt](/images/awslamb6.JPG)

Great our lambda function is working fine,its sending and receiving prompts and also storing it in the db. We can now proceed to the final steps and create api gateway
