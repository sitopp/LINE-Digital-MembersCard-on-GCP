import { Stack, StackProps, CfnOutput, RemovalPolicy } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { CloudFrontToS3 } from '@aws-solutions-constructs/aws-cloudfront-s3';
import { BucketDeployment, Source } from 'aws-cdk-lib/aws-s3-deployment';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';

export class CdkStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // https://github.com/aws-samples/cdk-chart-app-sample/blob/main/lib/frontend-stack.ts
    // https://github.com/aws-samples/aws-observability-workshop-web-app/blob/76f634778c6c6379e3b9c3c6fabe19fefa289098/lib/wild-rydes-app-stack.ts
    // AWS Solutions Constructs - CloudFront + S3
    const { s3Bucket, cloudFrontWebDistribution } = new CloudFrontToS3(this, 'WebAppCloudFrontS3', {
      insertHttpSecurityHeaders: false,
      bucketProps: {
        removalPolicy: RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
      },
      loggingBucketProps: {
        removalPolicy: RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
      }
    });

    // Deploy webapp by s3deployment
    new BucketDeployment(this, 'WebAppDeploy', {
      destinationBucket: s3Bucket!,
      distribution: cloudFrontWebDistribution,
      sources: [
        // Build and deploy a React frontend app
        Source.asset('line-api-use-case-MembersCard/front'),
      ]
    });
    
    // create CFn output but not to be exported - website URL
    new CfnOutput(this, 'EndpointUrl', {
      value: 'https://' + cloudFrontWebDistribution!.distributionDomainName,
    });
    
    new CfnOutput(this, 'BucketName', {
      value: s3Bucket!.bucketName,
    });

    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda-readme.html#bundling-asset-code
    // https://docs.aws.amazon.com/cdk/v2/guide/context.html
    const lambdaFunction = new lambda.Function(this, 'MyLambdaStack', {
      code: lambda.Code.fromAsset(path.join(__dirname, '/../line-api-use-case-MembersCard/backend'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_9.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output'
          ],
        },
      }),
      environment: {
        LIFF_CHANNEL_ID: this.node.tryGetContext('LIFF_CHANNEL_ID'),
        CHANNEL_ACCESS_TOKEN: this.node.tryGetContext('CHANNEL_ACCESS_TOKEN'),
      },
      handler: 'app.lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
    });
    
    
    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda-readme.html#anonymous-function-urls
    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda-readme.html#cors-configuration-for-function-urls
    const functionUrl = lambdaFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        // Allow this to be called from websites on https://example.com.
        // Can also be ['*'] to allow all domain.
        allowedOrigins: ['https://' + cloudFrontWebDistribution!.distributionDomainName],
        
        // More options are possible here, see the documentation for FunctionUrlCorsOptions
      },
    });
    
    new CfnOutput(this, 'FunctionUrl', {
      value: functionUrl.url,
    });
    
    
    // Create DynamoDB
    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_dynamodb.Table.html
    const dynamodbTable = new dynamodb.Table(this, "MembersCardUserInfo", {
      partitionKey: {
        name: "userId",
        type: dynamodb.AttributeType.STRING
      },
      tableName: "MembersCardUserInfo",
      removalPolicy: RemovalPolicy.DESTROY,
    });
    // Add authority FullAccess
    // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_dynamodb.Table.html#grantwbrfullwbraccessgrantee
    dynamodbTable.grantFullAccess(lambdaFunction); 
  }
}
