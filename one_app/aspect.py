import jsii
import aws_cdk as _cdk
import os

@jsii.implements(_cdk.IAspect)
class PactRoleName:

  def visit(self, node):
    _var = node.node.path.split("/")
    _stack_name = ''
    if _stack_name == '':
        _stack_name = _var[0]
    #print(node.node.path)
    #_path = _stack_name + 
    if "CloudWatchRole/Resource" in node.node.path:
        node.role_name = _stack_name + "-CloudWatchRole-" + os.environ["CDK_DEFAULT_REGION"]
    if "pm-lambda-dydb-role/Resource" in node.node.path:
        _var1 = node.node.path.split("/")
        node.role_name = _stack_name + "-pm-lambda-dydb-role" + "-" + os.environ["CDK_DEFAULT_REGION"]

    
