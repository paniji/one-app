from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk.aws_dynamodb import Attribute, AttributeType, ProjectionType
from one_app.sls.utils import utils
from one_app.sls.dydb.gldydb import gldyndb
import os

class dyndb:
    def __init__(self, dydb):
        print(dydb)

    def fn_table(self, dydb):
        aws_region=os.environ["CDK_DEFAULT_REGION"]

        if not utils.fn_try(dydb, "config") == 'E':
            glconfig = utils.fn_try(dydb, "config")

        for key in dydb["tables"]:
            table = dydb["tables"][key]
            name = table["tableName"]
            

            # if not utils.fn_try(table, "replicaRegion") == 'E':
            print("Table: ", name)
            gldyndb.fn_table(self, table, glconfig)
            # else:
            #     print("Table: ", name)
            #     # Partition Key
            #     pk = table["partitionKey"]

            #     # Read Write Capacity
            #     if not utils.fn_try(table, "writeCapacity") == 'E':
            #         wcu = utils.fn_try(table, "writeCapacity")
            #     else:
            #         wcu = 5

            #     if not utils.fn_try(table, "readCapacity") == 'E':
            #         rcu = utils.fn_try(table, "readCapacity")
            #     else:
            #         rcu = 5


            #     if not utils.fn_try(table, "sortKey") == 'E':
            #         sk = table["sortKey"]
            #         dy = dynamodb.Table(self, aws_region + '-' + name,
            #                 table_name=name,
            #                 replication_regions=["us-west-2"],
            #                 read_capacity=rcu,
            #                 write_capacity=wcu,
            #                 partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
            #                 sort_key=utils.fn_table_attr(sk["name"], sk["type"]))
            #     else:
            #         dy = dynamodb.Table(self, aws_region + '-' + name,
            #                 table_name=name,
            #                 replication_regions=["us-west-2"],
            #                 read_capacity=rcu,
            #                 write_capacity=wcu,
            #                 partition_key=utils.fn_table_attr(pk["name"], pk["type"])
            #                 )   

            #     try:
            #         gsi = table["globalSecondaryIndex"]
            #     except:
            #         print("No globalSecondaryIndex")

            #     if gsi:
            #         for gsikey in gsi:
            #             # print(gsikey)
            #             pk = gsikey["partitionKey"]

            #             # Read Write Capacity
            #             if not utils.fn_try(gsikey, "writeCapacity") == 'E':
            #                 wcu = utils.fn_try(gsikey, "writeCapacity")
            #             else:
            #                 wcu = 5

            #             if not utils.fn_try(gsikey, "readCapacity") == 'E':
            #                 rcu = utils.fn_try(gsikey, "readCapacity")
            #             else:
            #                 rcu = 5

            #             # if not utils.fn_try(gsikey, "nonKeyAttributes") == 'E':
            #             #     nka = utils.fn_try(gsikey, "nonKeyAttributes")
            #             #     nk = []
            #             #     for nkey in nka:
            #             #         nk.append(nkey)
            #             #     print(nk)

            #             if not utils.fn_try(gsikey, "sortKey") == 'E':
            #                 sk = gsikey["sortKey"]
            #                 #print(sk)
            #                 dy.add_global_secondary_index( 
            #                             partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
            #                             sort_key=utils.fn_table_attr(sk["name"], sk["type"]),
            #                             index_name=gsikey["indexName"],
            #                             # read_capacity=rcu,
            #                             # write_capacity=wcu,
            #                             # non_key_attributes=["hello"]
            #                             )
            #             else:
            #                 dy.add_global_secondary_index( 
            #                             partition_key=utils.fn_table_attr(pk["name"], pk["type"]),
            #                             index_name=gsikey["indexName"],
            #                             read_capacity=rcu,
            #                             # write_capacity=wcu,
            #                             # non_key_attributes=nk
            #                             )

                    