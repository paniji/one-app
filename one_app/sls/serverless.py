import aws_cdk as cdk_
import os
import datetime
from utils.utils import utils
from dydb.dynamodb import dyndb
import aws_cdk.aws_cloudformation as cloudformation
from aws_cdk import CustomResource

from aws_cdk import (aws_apigateway as apigateway_, Duration,
                     aws_certificatemanager as acm_,
                     aws_ec2 as ec2_,
                     aws_lambda as lambda_,
                     aws_iam as _iam,
                     custom_resources as _cr)

class ServerlessStack(cdk_.Stack):

    def __init__(self, scope: cdk_.App, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        print("Context: ", self.node.try_get_context("depl_from"))
        project_name = self.node.try_get_context("product_name")
        lambda_role = self.node.try_get_context("lambda_role")
        pact_env = self.node.try_get_context("pact_env") 
        sls_dir = self.node.try_get_context("sls_dir")
        sls_file = self.node.try_get_context("sls_file")
        depl_from = self.node.try_get_context("depl_from")
        config_file = self.node.try_get_context("config_file")

        if 'sls' in depl_from:
            depl_from = 'sls'
            sls_cfg_obj = utils.fn_sls_config_load(sls_dir)
        else:
            depl_from = 'cdk' 
        ## Default.. Check and crrect
        project_name = "one-app"
        depl_from = 'cdk'
        rs_dict = {}
        def fn_put_dict(key, value):
            rs_dict[key] = value

        rs_ent = {}
        def fn_put_ent(key, value):
            rs_ent[key] = value

        
        config = utils.fn_load_config(config_file)

#####
        #print("deploy from: ", depl_from)

        if depl_from == "sls" and not utils.fn_try(config["serverless"], "functions") == 'E':
            print("deployment from sls")
        else:
            print("deployment from cdk")
            depl_from = "cdk"
            #print("converting deploy_from from sls to cdk")
            
        if depl_from == "sls":
            proj = utils.fn_sls_project_load(sls_dir, sls_file)
            sls_obj = utils.fn_sls_config(sls_cfg_obj, config, proj)
            sl = sls_obj["serverless"]
            role_ = utils.fn_sls_role(sls_dir, self)
            
        elif depl_from == "cdk":
            sl = config["serverless"]
            role_ = utils.fn_cdk_role(self, project_name, lambda_role)

        # Load objects
        api_name = sl["name"]
        try:
            gw = sl["apigw"]
        except:
            print("no API Gateway")

        try:
            stage = gw["stageOptions"]
        except:
            print("no API Gateway Stage")

        # Create Layer
        lyr_list = []
        if not utils.fn_try(sl, "layers") == 'E':
            for lyr in sl["layers"]:
                #layer_zip = os.getcwd() + "/" + sls_dir + "/" + sl["layers"][lyr]["package"]["artifact"]

                if depl_from == "sls":
                    layer_zip = os.getcwd() + "/" + sls_dir + "/" + sl["layers"][lyr]["package"]["artifact"]
                else:
                    layer_zip = os.getcwd() + '/'+ sl["layers"][lyr]["package"]["artifact"]

                #print(sl["layers"][lyr])
                layer = lambda_.LayerVersion(self, sl["layers"][lyr]["name"],
                    code=lambda_.Code.from_asset(layer_zip),
                    #compatible_runtimes=[lambda_.Runtime.NODEJS_14_X],
                    #license="Apache-2.0",
                    description=sl["layers"][lyr]["description"]
                )
                lyr_list.append(layer)

        dydb_flag = ""
        if not utils.fn_try(sl, "dynamodb") == 'E':
            dydb_flag = True

        vpc_flag = ""; _subnets = []
        #print(sl["vpc"])
        if not utils.fn_try(sl, "vpc") == 'E':
            vpc_flag = True
            #print(sl["vpc"]["id"])
            _VpcID = ec2_.Vpc.from_lookup(self, "VPC", vpc_id=sl["vpc"]["id"], is_default=False)

            # Subnets
            if not utils.fn_try(sl["vpc"], "subnet") == 'E':
                sn_obj = (sl["vpc"]["subnet"])
                for snkey in sn_obj:
                    
                    sn = sn_obj[snkey]
                    #print("Subnet: ", sn["id"])
                    if not utils.fn_try(sn, "rt") == 'E':
                        _subnets.append(ec2_.Subnet.from_subnet_attributes(self, snkey, subnet_id=sn["id"],
                                                                        route_table_id=sn["rt"]
                                                                    ))                
                    else:
                        _subnets.append(ec2_.Subnet.from_subnet_attributes(self, snkey, subnet_id=sn["id"]
                                                                        #route_table_id=sn["rt"]
                                                                    )) 

            _sg = ec2_.SecurityGroup(self, "GizmoSG",
                                vpc=_VpcID,
                                allow_all_outbound=False
                                #security_group_name="SecGroup for"
                                )

            _sg.add_egress_rule(ec2_.Peer.ipv4("0.0.0.0/0"), ec2_.Port.tcp(443))
            _sg.add_egress_rule(peer=_sg, connection=ec2_.Port.all_traffic())
            _sg.add_ingress_rule(peer=_sg, connection=ec2_.Port.all_traffic())

        # Create domain and API GW 3
        try:
            dmn = sl["domain"]
            dmn_name = dmn["name"]
            dmn_cert = dmn["certificate"]
            dmn_path=dmn["path"]
            cert = acm_.Certificate.from_certificate_arn(self, "Certificate", dmn_cert)

            deploy_options=apigateway_.StageOptions(
                logging_level=utils.fn_log_level(stage["loggingLevel"]), # INFO, ERROR, OFF
                data_trace_enabled=stage["dataTraceEnabled"],
                stage_name=pact_env
                #tracing_enabled=True
            )

            api_gw = apigateway_.RestApi(self, api_name,
                                domain_name=apigateway_.DomainNameOptions(
                                                            domain_name=dmn_name,
                                                            base_path=dmn_path,
                                                            #endpoint_type=utils.fn_endpoint(gw["endpoint"]),
                                                            certificate=cert),
                                rest_api_name=api_name,
                                deploy_options=deploy_options,
                                endpoint_configuration=utils.fn_endpoint(gw["endpoint"])
                            )
            cdk_.Tags.of(api_gw).add("c7n_fed-sec-apigateway-public-restapi", "exempt")
        except:
            print("no domain")

        # Usage Plan
        try:
            usage = gw["usagePlan"]
            try:
                apikey = gw["apiKey"]
                apikey_bl = True
            except:
                apikey_bl = False
                print("no API Key")

            if utils.fn_throttle(usage) == True:
                plan = api_gw.add_usage_plan("UsagePlan",
                                    name=usage["name"],
                                    throttle=apigateway_.ThrottleSettings(
                                        rate_limit=usage["throttle"]["rateLimit"],
                                        burst_limit=usage["throttle"]["burstLimit"]
                                    )
                                )
            else:
                plan = api_gw.add_usage_plan("UsagePlan",
                                    name=usage["name"],
                                )
            key = api_gw.add_api_key(apikey["name"])
            plan.add_api_key(key)

            plan.add_api_stage(
                        stage=api_gw.deployment_stage
                        )
        except:
            print("no usage plan")

        datex = datetime.datetime.now()
#        try:
        fns = sl["functions"]
        print(fns)
        for key in fns:
            print("Lambda: ", key)
            lambdaObj = fns[key] #["code"]
            print(lambdaObj["package"])
            if depl_from == "sls":
                fn_zip = './' + sls_dir + '/.serverless/' + key + '.zip'
            else:
                fn_zip = os.getcwd() + '/'+ lambdaObj["package"]["artifact"]
                print(fn_zip)

            if vpc_flag:
                #print("VPC Idenitied and applied")
                Fn = lambda_.Function(self, lambdaObj["name"],
                    function_name=lambdaObj["name"],
                    code=lambda_.Code.from_asset(fn_zip),    #utils.fn_lambda_code(self, meth, fn_zip),
                    handler=lambdaObj["handler"],
                    runtime=utils.fn_runtime(lambdaObj["runtime"]),
                    memory_size=lambdaObj["memory"],
                    timeout=Duration.seconds(lambdaObj["timeout"]),
                    role=role_,
                    layers=lyr_list,
                    vpc=_VpcID,
                    vpc_subnets=ec2_.SubnetSelection(subnets=_subnets),
                    security_groups=[_sg],
                    tracing=lambda_.Tracing.ACTIVE,
                    current_version_options=lambda_.VersionOptions(
                            removal_policy=cdk_.RemovalPolicy.RETAIN,  # retain old versions
                            retry_attempts=1
                        ),
                    environment={
                        "CodeVersionString": str(datex)
                        },
                    #log_retention=log_.RetentionDays.FIVE_MONTHS
                )
            else:
                Fn = lambda_.Function(self, lambdaObj["name"],
                    function_name=lambdaObj["name"],
                    code=lambda_.Code.from_asset(fn_zip),
                    handler=lambdaObj["handler"],
                    runtime=utils.fn_runtime(lambdaObj["runtime"]),
                    memory_size=lambdaObj["memory"],
                    timeout=Duration.seconds(lambdaObj["timeout"]),
                    role=role_,
                    layers=lyr_list,
                    tracing=lambda_.Tracing.ACTIVE,
                    current_version_options=lambda_.VersionOptions(
                            removal_policy=cdk_.RemovalPolicy.RETAIN,  # retain old versions
                            retry_attempts=1
                            ),
                    environment={
                        "CodeVersionString": str(datex)
                    },
                )

            #print("Function_Inst: ", Fn)

            try: 
                lenv_ = lambdaObj["environment"]
                for envv in lenv_:
                    Fn.add_environment(envv, lenv_[envv])
            except:
                print("no function env var: ", key)

            try:
                tags_ = lambdaObj["tags"]
                for tag in tags_:
                    cdk_.Tags.of(Fn).add(tag, tags_[tag])
            except:
                print("no function tags: ", key)

            if utils.fn_auth(fns[key]) == True:
                if not utils.fn_try(gw, "identitySource") == 'E':  
                    idsource = []                  
                    for id in gw["identitySource"]:
                        idsource.append(apigateway_.IdentitySource.header(id))
                    #print(idsource)

                print("Lambda Authorizer: ", key)
                if not utils.fn_try(gw, "authType") == 'E':
                    #print(gw["authType"])
                    if gw["authType"] == "Request":
                        auth = apigateway_.RequestAuthorizer(self, "Authorizer",
                            handler=Fn,
                            identity_sources=idsource
                        )
                    else:
                        auth = apigateway_.TokenAuthorizer(self, "Authorizer",
                            handler=Fn,
                            identity_sources=idsource
                        )                            
                else:
                    auth = apigateway_.TokenAuthorizer(self, "Authorizer",
                        handler=Fn,
                        identity_sources=idsource
                    )


            try:
                events = fns[key]["events"]
                #print(events)
            #    #utils.fn_events(self, events, Fn, auth, fns, key)
                for event in events:
                    rs_path = event["http"]["path"]
                    ar_path = rs_path.split("/")
                    for index, item in enumerate(ar_path):
                        val = rs_path + "/" + str(index)
                        
                        if index == 0:
                            if not rs_dict.get(item):
                                api_gw_entity_root = api_gw.root.add_resource(item)
                                fn_put_dict(item, val)
                        elif index == 1:
                            if not rs_dict.get(item):
                                api_gw_entity_v = api_gw_entity_root.add_resource(item)
                                fn_put_dict(item, val)
                        elif index == 2:
                            if not rs_dict.get(item):
                                api_gw_entity = api_gw_entity_v.add_resource(item)
                                fn_put_ent(rs_path, api_gw_entity)
                                fn_put_dict(item, val)
                            
                            try:
                                resp = event["http"]["response"]
                                
                                try:
                                    req = event["http"]["request"]
                                    lambda_integration = apigateway_.LambdaIntegration(
                                            Fn,
                                            proxy=False,
                                            passthrough_behavior=apigateway_.PassthroughBehavior.WHEN_NO_TEMPLATES,
                                            request_templates=req["template"],
                                            integration_responses=utils.fn_response(resp),
                                            #connection_type=apigateway_.ConnectionType.VPC_LINK,
                                            #vpc_link=link
                                        )
                                except:
                                    print("no request template")
                                    lambda_integration = apigateway_.LambdaIntegration(
                                            Fn,
                                            proxy=False,
                                            passthrough_behavior=apigateway_.PassthroughBehavior.WHEN_NO_TEMPLATES,
                                            integration_responses=utils.fn_response(resp)
                                        )                                        
                            except:
                                print("no response: ", key)

                            meth = event["http"]["method"]

                            api_gw_entity.add_cors_preflight=apigateway_.CorsOptions(
                                                            allow_methods=[meth.upper()],
                                                            allow_origins=apigateway_.Cors.ALL_ORIGINS)

                            try:
                                auth_true = event["http"]["authorizer"]
                                #print("auth: ", key)
                                rs_ent.get(rs_path).add_method(
                                meth.upper(), lambda_integration,
                                authorizer=auth,
                                api_key_required=apikey_bl,
                                method_responses=[{
                                        'statusCode': '200',
                                        'responseParameters': {
                                            'method.response.header.Access-Control-Allow-Origin': True,
                                        }
                                    }]
                                )
                            except:
                                #print("non-auth: ", key)
                                rs_ent.get(rs_path).add_method(
                                    meth.upper(), lambda_integration,
                                    api_key_required=apikey_bl,
                                    method_responses=[{
                                            'statusCode': '200',
                                            'responseParameters': {
                                                'method.response.header.Access-Control-Allow-Origin': True,
                                            }
                                        }]
                                    ) 

            except:
                print("no events: ", key)


        if not utils.fn_try(gw['usagePlan'], "id") == 'E':
            usage_plan = gw['usagePlan']["id"]

            lambda_path = os.getcwd() + "/lambda/cr/on_event.py" # dir_path + "/" + "lambda_fn.py"
            try:
                with open(lambda_path, mode=r"r") as f:
                    lambda_code = f.read()
                    # print(lambda_code)
            except OSError:
                print("Unable to read Fn code")

            _lambda_role = _iam.Role(self, "lambda_role1", role_name="pm-sl-lambda-servicerole",
                                    assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"))

            allow_1 = _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                       actions=["apigateway:PATCH"],
                                       resources=["*"])
            _lambda_role.add_to_policy(allow_1)
            on_event_lambda = lambda_.Function(self, "Custom_Private_Lambda1",
                                        runtime=lambda_.Runtime.PYTHON_3_9,
                                        handler="index.handler",
                                        code=lambda_.InlineCode(
                                            lambda_code
                                        ),
                                        role=_lambda_role)

            provider = _cr.Provider(self, "Provider",
                on_event_handler=on_event_lambda,
                #is_complete_handler=is_complete_lm,  # optional async "waiter"
                #role=_lambda_role
            )

            apiStage = api_gw.rest_api_id + ":" + pact_env
            cr1_ = CustomResource(self, "custom_resource_usage",
                        service_token=provider.service_token,
                        properties={'RequestType': 'Create', "usagePlanId" : usage_plan, "apiStage" : apiStage}
                        )

            cr1_.node.add_dependency(api_gw)
        # Create DynamoDB
        if not utils.fn_try(sl, "dynamodb") == 'E':
            dydb = utils.fn_try(sl, "dynamodb")
            dyndb.fn_table(self, dydb)


#####

