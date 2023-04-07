
from aws_cdk import aws_dynamodb as dynamodb
from one_app.sls.utils import utils

class gutils:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def fn_fetch_throughput(obj):
        ret_obj = {}
        wsc = obj
        ret_obj["wmax"] = wsc["maxCapacity"]
        ret_obj["wmin"] = wsc["minCapacity"]
        ret_obj["wseed"] = wsc["seedCapacity"]
        ret_obj["wtarget"] = wsc["targetTrackingScalingPolicyConfiguration"]["targetValue"]

        return ret_obj

    def fn_attr_def(attr, key):
        at = dynamodb.CfnGlobalTable.AttributeDefinitionProperty(
                    attribute_name=key["name"],
                    attribute_type=key["type"]
                )
        attr.append(at)
        return attr

    def fn_key_schema(attr, key):
        at = dynamodb.CfnGlobalTable.KeySchemaProperty(
                    attribute_name=key["name"],
                    key_type="HASH"
                )
        attr.append(at)
        return attr

    def fn_gsi_projection(obj):
        if not utils.fn_try(obj, "NonKeyAttributes") == 'E':
            nk = obj["NonKeyAttributes"]

        if not utils.fn_try(obj, "ProjectionType") == 'E':
            pt = obj["ProjectionType"]

        proj = dynamodb.CfnGlobalTable.ProjectionProperty(
                        non_key_attributes=nk,
                        projection_type=pt
                    )
        
        return proj

    def fn_capacity_auto_scaling(obj):
        cas = dynamodb.CfnGlobalTable.CapacityAutoScalingSettingsProperty(
                            max_capacity=obj["wmax"],
                            min_capacity=obj["wmin"],
                            target_tracking_scaling_policy_configuration=dynamodb.CfnGlobalTable.TargetTrackingScalingPolicyConfigurationProperty(
                                target_value=obj["wtarget"],
                            ),
                            # the properties below are optional
                            seed_capacity=obj["wseed"]
                        )
        return cas

    def fn_write_throughput(obj):
        cas = gutils.fn_capacity_auto_scaling(obj)
        wth = dynamodb.CfnGlobalTable.WriteProvisionedThroughputSettingsProperty(
                        write_capacity_auto_scaling_settings=cas
                    )
        return wth

    def fn_read_throughput(obj):
        cas = gutils.fn_capacity_auto_scaling(obj)
        rth = dynamodb.CfnGlobalTable.ReadProvisionedThroughputSettingsProperty(
                read_capacity_auto_scaling_settings=cas,
                read_capacity_units=obj["wseed"]
            )
        return rth

    def fn_gsi(attr, key, attr_def, wth):
        pk = key["keySchema"]
        gutils.fn_attr_def(attr_def, pk)
        key_a = []
        key_ = gutils.fn_key_schema(key_a, pk)

        if not utils.fn_try(key, "Projection") == 'E':
            proj_obj = key["Projection"]
            proj = gutils.fn_gsi_projection(proj_obj)

        if not utils.fn_try(key, "writeProvisionedThroughputSettings") == 'E':
            gsi_wtr = key["writeProvisionedThroughputSettings"]
            wth_ = gutils.fn_fetch_throughput(gsi_wtr)
            wth_inst = gutils.fn_write_throughput(wth_)
        else:
            wth_inst = gutils.fn_write_throughput(wth)

        gsi = dynamodb.CfnGlobalTable.GlobalSecondaryIndexProperty(
                    index_name=key["indexName"],
                    key_schema=key_,
                    projection=proj,
                    write_provisioned_throughput_settings=wth_inst
                )
        attr.append(gsi)
        return attr

    def fn_replica_gsi(gsi, i, inst):
        print(i)
        rgsi = dynamodb.CfnGlobalTable.ReplicaGlobalSecondaryIndexSpecificationProperty(
                        index_name=i["indexName"],
                        read_provisioned_throughput_settings=inst
                    )
        gsi.append(rgsi)
        return gsi

    def fn_replica(key, rth, repl, table):
        obj = key

        if not utils.fn_try(key, "readProvisionedThroughputSettings") == 'E':
            gsi_rtr = key["readProvisionedThroughputSettings"]
            rth_ = gutils.fn_fetch_throughput(gsi_rtr)
            rth_inst = gutils.fn_read_throughput(rth_)
        else:
            rth_inst = gutils.fn_read_throughput(rth)

        rgsi = []
        if not utils.fn_try(table, "globalSecondaryIndex") == 'E':
            gsi_obj = table["globalSecondaryIndex"]
            for i in gsi_obj:
                gsi_def = gutils.fn_replica_gsi(rgsi, i, rth_inst)

        rpl = dynamodb.CfnGlobalTable.ReplicaSpecificationProperty(
            region=obj["region"],

            point_in_time_recovery_specification=dynamodb.CfnGlobalTable.PointInTimeRecoverySpecificationProperty(
                point_in_time_recovery_enabled=obj["pointInTimeRecovery"]
            ),
            read_provisioned_throughput_settings=rth_inst,
            global_secondary_indexes=gsi_def
            # sse_specification=dynamodb.CfnGlobalTable.ReplicaSSESpecificationProperty(
            #     kms_master_key_id="kmsMasterKeyId"
            # ),
            # table_class="tableClass",
            # tags=[CfnTag(
            #     key="key",
            #     value="value"
            # )]
        )

        repl.append(rpl)
        return repl


