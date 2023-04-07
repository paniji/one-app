from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk.aws_dynamodb import Attribute, AttributeType, ProjectionType
from one_app.sls.utils import utils
from one_app.sls.gutils import gutils
import os

class gldyndb:
    def __init__(self, dydb):
        print(dydb)

    def fn_table(self, table, config):

        aws_region=os.environ["CDK_DEFAULT_REGION"]
        attr = []
        key_sch = []
        gsi = []
        repl = []
        name = table["tableName"]
        #print("TableName:", name)
        #print("Table: ", name)

        # Partition Key
        if not utils.fn_try(table, "partitionKey") == 'E':
            pk = table["partitionKey"]
            attr_def = gutils.fn_attr_def(attr, pk)
            key_def = gutils.fn_key_schema(key_sch, pk)      
        # Sort Key
        if not utils.fn_try(table, "sortKey") == 'E':
            sk = table["sortKey"]
            attr_def = gutils.fn_attr_def(attr, sk)

        if not utils.fn_try(table, "tableClass") == 'E':
            mode = table["tableClass"]
        else:
            mode = "PROVISIONED"

        if not utils.fn_try(table, "streamSpecification") == 'E':
            stream_view = table["streamSpecification"]["streamViewType"]

        if not utils.fn_try(table, "billingMode") == 'E':
            bm = table["billingMode"]
        else:
            bm = "PROVISIONED"
            
        lconfig = ""
        if not utils.fn_try(table, "config") == 'E':
            lconfig = utils.fn_try(table, "config")
        else:
            lconfig = config
        
        # Replication region
        rr = []
        if not utils.fn_try(table, "replicaRegion") == 'E':
            rgn = table["replicaRegion"]
            for k in rgn:
                rr.append(k["region"])
        # point_in_time_recovery
        if not utils.fn_try(lconfig, "pointInTimeRecovery") == 'E':
            ptr = lconfig["pointInTimeRecovery"]
        else:
            ptr = True
        # autoScaleWriteCapacity
        if not utils.fn_try(lconfig, "autoScaleWriteCapacity") == 'E':
            aswc = lconfig["autoScaleWriteCapacity"]
            minc = aswc["minCapacity"]
            maxc = aswc["maxCapacity"]
            targetp = aswc["targetUtilizationPercent"]
        else:
            minc = 1
            maxc = 10
            targetp = 75

       # autoScaleReadCapacity
        if not utils.fn_try(lconfig, "autoScaleReadCapacity") == 'E':
            asrc = lconfig["autoScaleReadCapacity"]
            _rd_minc = asrc["minCapacity"]
            _rd_maxc = asrc["maxCapacity"]
            _rd_targetp = asrc["targetUtilizationPercent"]
        else:
            _rd_minc = 1
            _rd_maxc = 10
            _rd_targetp = 75

## CDK L2
        if not utils.fn_try(table, "sortKey") == 'E':
            sk = table["sortKey"]
            dy = dynamodb.Table(self, name,
                    table_name=name,
                    replication_regions=rr,
                    partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
                    sort_key=utils.fn_table_attr(sk["name"], sk["type"]),
                    point_in_time_recovery=ptr,
                    encryption=dynamodb.TableEncryption.AWS_MANAGED,
                    billing_mode=utils.fn_billing_mode(bm)
                    )
                    
        else:
            dy = dynamodb.Table(self, name,
                    table_name=name,
                    replication_regions=rr,
                    partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
                    point_in_time_recovery=ptr,
                    encryption=dynamodb.TableEncryption.AWS_MANAGED,
                    billing_mode=utils.fn_billing_mode(bm)
                    )   

        if bm == "PROVISIONED":
            dy.auto_scale_write_capacity(
                min_capacity=minc,
                max_capacity=maxc
                ).scale_on_utilization(target_utilization_percent=targetp)

            dy.auto_scale_read_capacity(
                min_capacity=_rd_minc,
                max_capacity=_rd_maxc
                ).scale_on_utilization(target_utilization_percent=_rd_targetp)

        if not utils.fn_try(table, "globalSecondaryIndex") == 'E':
            gsi = table["globalSecondaryIndex"]
            for gsikey in gsi:
                # print(gsikey)
                pk = gsikey["keySchema"]
                
                #print(gsikey)
                nka = []
                if not utils.fn_try(gsikey, "nonKeyAttributes") == 'E':         
                    nka = utils.fn_try(gsikey, "nonKeyAttributes")

                
                if not utils.fn_try(gsikey, "projectionType") == 'E':         
                    pt = utils.fn_try(gsikey, "projectionType")
                    #print(gsikey, pt)
                    if pt == "INCLUDE":
                        pti = dynamodb.ProjectionType.INCLUDE
                    elif pt == "ALL":
                        pti = dynamodb.ProjectionType.ALL
                    elif pt == "KEYS_ONLY":
                        pti == dynamodb.ProjectionType.KEYS_ONLY
                    else:
                        pti = dynamodb.ProjectionType.ALL
                else:
                    pti = dynamodb.ProjectionType.ALL

                if not utils.fn_try(gsikey, "sortKey") == 'E':
                    sk = gsikey["sortKey"]
                    #print(sk)
                    if nka:
                        dy.add_global_secondary_index( 
                                    partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
                                    sort_key=utils.fn_table_attr(sk["name"], sk["type"]),
                                    index_name=gsikey["indexName"],
                                    non_key_attributes=nka,
                                    projection_type=pti
                                    )
                    else:
                        dy.add_global_secondary_index( 
                                    partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
                                    sort_key=utils.fn_table_attr(sk["name"], sk["type"]),
                                    index_name=gsikey["indexName"],
                                    projection_type=pti
                                    )                        
                    if bm == "PROVISIONED":
                        if not utils.fn_try(gsikey, "autoScaleGsiWriteCapacity") == 'E':
                            gsi_aswc = gsikey["autoScaleGsiWriteCapacity"]
                            gsi_minwc = gsi_aswc["minCapacity"]
                            gsi_maxwc = gsi_aswc["maxCapacity"]
                            gsi_targetwp = gsi_aswc["targetUtilizationPercent"]
 
                            dy.auto_scale_global_secondary_index_write_capacity(index_name=gsikey["indexName"],
                                                max_capacity=gsi_maxwc,
                                                min_capacity=gsi_minwc).scale_on_utilization(target_utilization_percent=gsi_targetwp)
                        else:                  
                            dy.auto_scale_global_secondary_index_write_capacity(index_name=gsikey["indexName"],
                                            max_capacity=maxc,
                                            min_capacity=minc).scale_on_utilization(target_utilization_percent=targetp)

                        if not utils.fn_try(gsikey, "autoScaleGsiReadCapacity") == 'E':
                           gsi_asrc = gsikey["autoScaleGsiReadCapacity"]
                           gsi_minrc = gsi_asrc["minCapacity"]
                           gsi_maxrc = gsi_asrc["maxCapacity"]
                           gsi_targetrp = gsi_asrc["targetUtilizationPercent"]
 
                           dy.auto_scale_global_secondary_index_read_capacity(index_name=gsikey["indexName"],
                                               max_capacity=gsi_maxrc,
                                               min_capacity=gsi_minrc).scale_on_utilization(target_utilization_percent=gsi_targetrp)
                else:
                    if nka:
                        dy.add_global_secondary_index( 
                                    partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
                                    non_key_attributes=nka,
                                    index_name=gsikey["indexName"],
                                    projection_type=pti
                                    )
                    else:
                        dy.add_global_secondary_index( 
                                    partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
                                    index_name=gsikey["indexName"],
                                    projection_type=pti
                                    )                        

                    if bm == "PROVISIONED":
                        if not utils.fn_try(gsikey, "autoScaleGsiWriteCapacity") == 'E':
                            gsi_aswc = gsikey["autoScaleGsiWriteCapacity"]
                            gsi_minwc = gsi_aswc["minCapacity"]
                            gsi_maxwc = gsi_aswc["maxCapacity"]
                            gsi_targetwp = gsi_aswc["targetUtilizationPercent"]
 
                            dy.auto_scale_global_secondary_index_write_capacity(index_name=gsikey["indexName"],
                                                max_capacity=gsi_maxwc,
                                                min_capacity=gsi_minwc).scale_on_utilization(target_utilization_percent=gsi_targetwp)
                        else:                    
                            dy.auto_scale_global_secondary_index_write_capacity(index_name=gsikey["indexName"],
                                            max_capacity=maxc,
                                            min_capacity=minc).scale_on_utilization(target_utilization_percent=targetp)

                        if not utils.fn_try(gsikey, "autoScaleGsiReadCapacity") == 'E':
                           gsi_asrc = gsikey["autoScaleGsiReadCapacity"]
                           gsi_minrc = gsi_asrc["minCapacity"]
                           gsi_maxrc = gsi_asrc["maxCapacity"]
                           gsi_targetrp = gsi_asrc["targetUtilizationPercent"]
 
                           dy.auto_scale_global_secondary_index_read_capacity(index_name=gsikey["indexName"],
                                               max_capacity=gsi_maxrc,
                                               min_capacity=gsi_minrc).scale_on_utilization(target_utilization_percent=gsi_targetrp)
        ## End of CDK L2


        ## CDK L1
        # if not utils.fn_try(table, "writeProvisionedThroughputSettings") == 'E':
        #     wth = gutils.fn_fetch_throughput(table["writeProvisionedThroughputSettings"]["writeCapacityAutoScalingSettings"])
        #     wth_inst = gutils.fn_write_throughput(wth)

        # if not utils.fn_try(table, "readProvisionedThroughputSettings") == 'E':
        #     rth = gutils.fn_fetch_throughput(table["readProvisionedThroughputSettings"]["readCapacityAutoScalingSettings"])

        # if not utils.fn_try(table, "replicaRegion") == 'E':
        #     rpl_obj = table["replicaRegion"]

        #     for r in rpl_obj:
        #         repl_inst = gutils.fn_replica(r, rth, repl, table)
        #     #print(replica)

        # if not utils.fn_try(table, "globalSecondaryIndex") == 'E':
        #     gsi_obj = table["globalSecondaryIndex"]
        #     for i in gsi_obj:
        #         gsi_def = gutils.fn_gsi(gsi, i, attr_def, wth)

        # #attr.append(attr_def)
        # cfn_global_table = dynamodb.CfnGlobalTable(self, name,
        #     attribute_definitions=attr_def,
        #     key_schema=key_def,
        #     replicas=repl_inst,

        #     # Global secondary index
        #     billing_mode=mode,
        #     global_secondary_indexes=gsi_def,
        #     table_name=name,
        #     write_provisioned_throughput_settings=wth_inst
        # )
        ## CDK End of L1

        