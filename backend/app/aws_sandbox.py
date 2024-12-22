import boto3

cloudformation = boto3.client("cloudformation")


def create_sandbox(name):
    """
    Create a new sandbox with the given name.
    """

    template_body = """
    AWSTemplateFormatVersion: '2010-09-09'
    Resources:
      SandboxInstance:
        Type: 'AWS::EC2::Instance'
        Properties:
          InstanceType: 't3.micro'
          ImageId: 'ami-0c02fb55956c7d316'  # Amazon Linux 2 AMI
          Tags:
            - Key: 'Environment'
              Value: 'Sandbox'
    """
    response = cloudformation.create_stack(
        StackName=name,
        TemplateBody=template_body,
        Tags=[{"Key": "Environment", "Value": "Sandbox"}],
    )
    return {"stack_id": response["StackId"], "status": "ACTIVE"}


def terminate_sandbox(stack_id):
    """
    Terminate a sandbox environment by deleting the stack.
    """
    response = cloudformation.delete_stack(StackName=stack_id)
    return {"stack_id": stack_id, "status": "TERMINATED"}
