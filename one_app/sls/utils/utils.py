
from aws_cdk import ( aws_lambda, aws_apigateway, aws_iam )
from aws_cdk.aws_dynamodb import Attribute, AttributeType, ProjectionType
import json
import os
import yaml
from aws_cdk import aws_dynamodb as dynamodb

from aws_cdk import (Stage, aws_apigateway as apigateway_,
                     aws_s3 as s3_,
                     aws_lambda as lambda_,
                     aws_iam as iam_,
                     aws_logs as log_)

class utils:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def fn_lambda_code(self, meth, path):
        if meth == "S3":
            s3_path = path.split("/")
            bucket_ = s3_.Bucket.from_bucket_name(self, "lambda_bucket" + meth, s3_path[2])
            s3_fn_path = path.split(s3_path[2])
            return lambda_.Code.from_bucket(bucket=bucket_, key=s3_fn_path[1][1:])
        elif meth == "DIR":
            return lambda_.Code.from_asset(path)
        else:
            return lambda_.Code.from_asset(path)

    def fn_try(obj, key):
        try:
            return obj[key]
        except:
            #print("No ", key)
            return 'E'     

    def fn_billing_mode(type):
        if type == "PROVISIONED":
            bm = dynamodb.BillingMode.PROVISIONED
        elif type == "PAY_PER_REQUEST":
            bm = dynamodb.BillingMode.PAY_PER_REQUEST

        return bm

    def fn_attr_type(type):
        if type == "String":
            s_type = AttributeType.STRING
        elif type == "Number":
            s_type = AttributeType.NUMBER
        elif type == "Binary":
            s_type = AttributeType.BINARY

        return s_type

    def fn_table_attr(name, type):
        if type == "String":
            s_type = AttributeType.STRING
        elif type == "Number":
            s_type = AttributeType.NUMBER
        elif type == "Binary":
            s_type = AttributeType.BINARY
        elif type == "S":
            s_type = AttributeType.STRING
        elif type == "N":
            s_type = AttributeType.NUMBER
        elif type == "B":
            s_type = AttributeType.BINARY

        return Attribute(name=name, type = s_type)

    def fn_endpoint(ep):
        if ep == "REGIONAL":
            return aws_apigateway.EndpointConfiguration(
                        types=[aws_apigateway.EndpointType.REGIONAL])
        if ep == "EDGE": 
            return aws_apigateway.EndpointConfiguration(
                        types=[aws_apigateway.EndpointType.EDGE])
        if ep == "PRIVATE":
            return aws_apigateway.EndpointConfiguration(
                        types=[aws_apigateway.EndpointType.PRIVATE])

    def fn_load_config(config_file):
        if "config.yml" in config_file:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            file = dir_path + "/" + config_file
        else:
            dir_path = os.getcwd()
            file = dir_path + "/" + config_file
        print(os.getcwd(), file)
        with open(file) as file:
            try:
                config = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print("Error while reading config.yml")
        return config

    def fn_sls_project_load(sls_dir, sls_file):
        dir_path = os.getcwd() #os.path.dirname(os.path.realpath(__file__))
        #print("project:", dir_path)
        file = dir_path + "/" + sls_dir + "/" + sls_file
        #print("projectfile:", file)
        with open(file) as file:
            try:
                config = yaml.load(file, Loader=yaml.BaseLoader)
                #yaml.load('Foo: !Ref bar', Loader=yaml.BaseLoader)
                #print(config["layers"])
            except yaml.YAMLError as exc:
                print ("Error while parsing YAML file:")
                if hasattr(exc, 'problem_mark'):
                    if exc.context != None:
                        print ('  parser says\n' + str(exc.problem_mark) + '\n  ' +
                            str(exc.problem) + ' ' + str(exc.context) +
                            '\nPlease correct data and retry.')
                    else:
                        print ('  parser says\n' + str(exc.problem_mark) + '\n  ' +
                            str(exc.problem) + '\nPlease correct data and retry.')
                else:
                    print ("Something went wrong while parsing yaml file")
        return config

    def fn_sls_config_load(sls_dir):
        sls_config = './' + sls_dir + '/.serverless/serverless-state.json'
        with open(sls_config, 'r') as slsfile:
            data=slsfile.read()

        # parse file 5
        sls_cfg_obj = json.loads(data)
        return sls_cfg_obj

    def fn_cdk_role(self, project_name, lambda_role):
        role_arn_ = "arn:aws:iam::" + os.environ["CDK_DEFAULT_ACCOUNT"] + ":role/" + project_name + "-" + lambda_role + "-" + os.environ["CDK_DEFAULT_REGION"]
        cdk_role = aws_iam.Role.from_role_arn(self, id="Admin1",
                               role_arn=role_arn_
                               )

        return cdk_role

    def fn_sls_role(sls_dir, self):
        # # read file
        with open('./' + sls_dir + '/iamRoleStatements.json', 'r') as policyDoc: 
            data1=policyDoc.read()

        x = json.dumps(data1)
        #print(x)
        y = x.replace("${self:custom.account}", os.environ["CDK_DEFAULT_ACCOUNT"])
        z = json.loads(y)
        # # # parse file
        pdoc = json.loads(z)
        sls_role = aws_iam.Role(self, "LambdaRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com")
            )
        for pst in pdoc:
            sls_role.add_to_policy(aws_iam.PolicyStatement.from_json(pst))

        sls_role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"))
        return sls_role

    def fn_sls_config(sls_cfg_obj, config, proj):
        #print(proj)

        sls_obj = { "serverless": {} }
        auth_fn = ""
        lenv_ = sls_cfg_obj["service"]["provider"]["environment"]
        for key in config["serverless"]:
            if key != "functions":
                if key == "name":
                    sls_obj["serverless"][key] = sls_cfg_obj["service"]["service"]
                else:
                    sls_obj["serverless"][key] = config["serverless"][key]
        sls_obj["serverless"]["functions"] = {}
        # Add layers if any
        if not utils.fn_try(proj, "layers") == 'E':
            sls_obj["serverless"]["layers"] = proj["layers"]

        # if not utils.fn_try(config["serverless"], "vpc") == 'E':
        #     sls_obj["serverless"]["vpc"] = config["serverless"]["vpc"]
            
        for key in sls_cfg_obj["service"]["functions"]:
            sls_obj["serverless"]["functions"][key] = sls_cfg_obj["service"]["functions"][key]
            sls_obj["serverless"]["functions"][key]["environment"] = {}
            sls_obj["serverless"]["functions"][key]["environment"] = lenv_
            
            if "authorizer" in key:
                sls_obj["serverless"]["functions"][key]["authorizer"] = {}
                #auth_fn = key
                sls_obj["serverless"]["functions"][key]["authorizer"] = { 'type': True }
            # else:
            #     sls_obj["serverless"]["functions"][key]["authorizer"] = {'type': 'REQUEST', 'name': auth_fn }

        return sls_obj

    def fn_auth(fn):
        try:
            #print(fn["authorizer"]["type"])
            return fn["authorizer"]["type"]
        except:
            return False

    def fn_response(resp):
        restmpl = []
        sts = resp["statusCodes"]
        
        cnttyp = resp['headers']['Content-Type']
        #print(cnttyp)
        cnttyp = cnttyp.replace('"', '')
        cnttyp = cnttyp.replace("'", '')
        for res in sts:
            #print(res)
            try:
                tmpl = (sts[res]['template'])
                ptrn = (sts[res]['pattern'])
                r = aws_apigateway.IntegrationResponse(status_code=res,
                                            response_templates={
                                                cnttyp: tmpl
                                                },
                                            selection_pattern=ptrn)
                restmpl.append(r)
            except:
                ptrn = (sts[res]['pattern'])
                r = aws_apigateway.IntegrationResponse(status_code=res,
                                            #response_templates={cnttyp, tmpl},
                                            selection_pattern=ptrn)
                restmpl.append(r)

        return restmpl

    def fn_throttle(usage):
        try:
            usage["throttle"]
            return True
        except:
            return False

    def fn_log_level(log):
        if log == "INFO":
            return aws_apigateway.MethodLoggingLevel.INFO
        if log == "ERROR":
            return aws_apigateway.MethodLoggingLevel.ERROR
        if log == "OFF":
            return aws_apigateway.MethodLoggingLevel.OFF

    def fn_runtime(lambda_runtime):
        if lambda_runtime == "DOTNET_CORE_1":
            return aws_lambda.Runtime.DOTNET_CORE_1
        if lambda_runtime == "DOTNET_CORE_2":
            return aws_lambda.Runtime.DOTNET_CORE_2
        if lambda_runtime == "DOTNET_CORE_2_1":
            return aws_lambda.Runtime.DOTNET_CORE_2_1
        if lambda_runtime == "DOTNET_CORE_3_1":
            return aws_lambda.Runtime.DOTNET_CORE_3_1
        if lambda_runtime == "FROM_IMAGE":
            return aws_lambda.Runtime.FROM_IMAGE
        if lambda_runtime == "GO_1_X":
            return aws_lambda.Runtime.GO_1_X
        if lambda_runtime == "JAVA_11":
            return aws_lambda.Runtime.JAVA_11
        if lambda_runtime == "JAVA_8":
            return aws_lambda.Runtime.JAVA_8
        if lambda_runtime == "JAVA_8_CORRETTO":
            return aws_lambda.Runtime.JAVA_8_CORRETTO
        if lambda_runtime == "NODEJS":
            return aws_lambda.Runtime.NODEJS
        if lambda_runtime == "NODEJS_10_X":
            return aws_lambda.Runtime.NODEJS_10_X
        if lambda_runtime == "NODEJS_12_X":
            return aws_lambda.Runtime.NODEJS_12_X
        if lambda_runtime == "nodejs14.x":
            return aws_lambda.Runtime.NODEJS_14_X
        if lambda_runtime == "NODEJS_4_3":
            return aws_lambda.Runtime.NODEJS_4_3
        if lambda_runtime == "NODEJS_6_10":
            return aws_lambda.Runtime.NODEJS_6_10
        if lambda_runtime == "NODEJS_8_10":
            return aws_lambda.Runtime.NODEJS_8_10
        if lambda_runtime == "PROVIDED":
            return aws_lambda.Runtime.PROVIDED
        if lambda_runtime == "PROVIDED_AL2":
            return aws_lambda.Runtime.PROVIDED_AL2
        if lambda_runtime == "PYTHON_2_7":
            return aws_lambda.Runtime.PYTHON_2_7
        if lambda_runtime == "PYTHON_3_6":
            return aws_lambda.Runtime.PYTHON_3_6
        if lambda_runtime == "PYTHON_3_7":
            return aws_lambda.Runtime.PYTHON_3_7
        if lambda_runtime == "PYTHON_3_8":
            return aws_lambda.Runtime.PYTHON_3_8
        if lambda_runtime == "PYTHON_3_9":
            return aws_lambda.Runtime.PYTHON_3_9
        if lambda_runtime == "RUBY_2_5":
            return aws_lambda.Runtime.RUBY_2_5
        if lambda_runtime == "RUBY_2_7":
            return aws_lambda.Runtime.RUBY_2_7