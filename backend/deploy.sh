#!/usr/bin/env bash
# ./deploy.sh --bucket-name <AWS_BUCKET_NAME> --aws-region <AWS_REGION> --aws-profile <AWS_PROFILE> --stack-name <STACK_NAME>

aws s3api create-bucket \
  --bucket ${bucket-name} \
  --create-bucket-configuration \
  LocationConstraint=${aws-region:-us-west-2} \
  --region ${aws-region:-us-west-2} \
  --profile ${aws-profile:-default}

sam build

sam package --s3-bucket ${bucket-name} --output-template-file out.yaml --profile ${aws-profile:-default}

sam deploy \
  --template-file out.yaml \
  --stack-name ${stack-name} \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --profile ${aws-profile:-default} --region ${aws-region:-us-west-2}