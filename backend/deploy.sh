#!/usr/bin/env bash
# ./deploy.sh --bucket-name <AWS_BUCKET_NAME> --aws-region <AWS_REGION> --aws-profile <AWS_PROFILE> --stack-name <STACK_NAME>

bucketName=${2}
awsRegion=${4}
awsProfile=${6}
stackName=${8}

aws s3api create-bucket \
  --bucket ${bucketName} \
  --create-bucket-configuration \
  LocationConstraint=${awsRegion:-us-west-2} \
  --region ${awsRegion:-us-west-2} \
  --profile ${awsProfile:-default}

sam build

sam package --s3-bucket ${bucketName} --output-template-file out.yaml --profile ${awsProfile:-default}

sam deploy \
  --template-file out.yaml \
  --stack-name ${stackName} \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --profile ${awsProfile:-default} --region ${awsRegion:-us-west-2}