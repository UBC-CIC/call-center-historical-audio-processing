:: deploy.bat bucket-name:<AWS_BUCKET_NAME> aws-region:<AWS_REGION> aws-profile:<AWS_PROFILE> stack-name:<STACK_NAME>
@echo off
SET tempvar1=%~1
SET tempvar2=%~2
SET tempvar3=%~3
SET tempvar4=%~4
SET bucket-name=%tempvar1:~12,250%
SET aws-region=%tempvar2:~11,250%
SET aws-profile=%tempvar3:~12,250%
SET stack-name=%tempvar4:~11,250%

CALL aws s3api create-bucket --bucket %bucket-name% ^
--create-bucket-configuration LocationConstraint=%aws-region% ^
--region %aws-region% --profile %aws-profile%

CALL sam build

CALL sam package --s3-bucket %bucket-name% --output-template-file out.yaml --profile %aws-profile%

CALL sam deploy --template-file out.yaml --stack-name %stack-name% ^
--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND ^
--profile %aws-profile% --region %aws-region%