import os
import time
import psutil
from Utils.db_connection import ClickHouse
from Utils.logger import get_module_logger

if __name__ == '__main__':
    table = "default.prd_users"
    cpu_limit = int(os.environ['CPU_LIMIT'])
    ram_limit = int(os.environ['RAM_LIMIT'])

    get_module_logger("Management").info(f'Deduplicating table: {table}')

    db = ClickHouse()
    get_module_logger("Management").info(f'Server configurations:\n'
                                         f'cpu cores: {psutil.cpu_count()}, \n'
                                         f'ram: {psutil.virtual_memory().total / 1000000000} GB')
    while True:
        # partitions that have duplicates are collected
        partition_query = "SELECT _partition_id from {TABLE:Identifier} WHERE id IN(" \
                          "SELECT id FROM {TABLE:Identifier} lcd GROUP BY id HAVING count(*) > 1" \
                          ") GROUP BY _partition_id"
        dedup_partitions = db.select(partition_query, params={"table": table})
        get_module_logger("Management").info(f"No. deduplicating partitions in {table}: {len(dedup_partitions)}")

        for partition in dedup_partitions:
            while True:
                # partitions are deduplicated when cpu and ram usage is reasonable
                cpu, ram = psutil.cpu_percent(interval=1), psutil.virtual_memory().percent
                print('CPU:', cpu, 'RAM:', ram)
                if cpu < cpu_limit and ram < ram_limit:
                    dedup_query = "OPTIMIZE TABLE {table:Identifier} PARTITION ID {partition:String} FINAL"
                    db.query(dedup_query, params={"table": table, "partition": partition[0]})
                    break
                else:
                    time.sleep(5)
                    continue

        get_module_logger("Management").info(f"Table {table} was deduplicated")
        time.sleep(10)
