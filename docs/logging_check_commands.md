# Commands to check for logging

1. SSH to the aggregator
2. To check that the cluster is up and running: 

        $ curl -X GET "https://admin:admin@localhost:9200/_cat/health?v" --insecure
        epoch      timestamp cluster        status node.total node.data shards pri relo init unassign pending_tasks max_task_wait_time active_shards_percent
        1532709281 16:34:41  docker-cluster yellow          1         1      7   7    0    0        6             0                  -                 53.8%
3. To check if we've received at least some data to date: 
    
        $ curl -X GET "https://admin:admin@localhost:9200/_cat/indices?v" --insecure
        health status index             uuid                   pri rep docs.count docs.deleted store.size pri.store.size
        yellow open   .kibana           6DS8Lc4ZTMKMZHUMX1_QeQ   1   1          2            0      8.6kb          8.6kb
        green  open   searchguard       RI7HZhoGRmWS2gKDj-8yLQ   1   0          0            0       30kb           30kb
        yellow open   syslog-2018.07.27 a75WMUX6TMSn05SKFwDWZw   5   1        671            0    726.1kb        726.1kb
Some of the things in this display will differ depending on your install, but if you see words like "yellow", "green", and an index called `syslog-<TIMESTAMP>` then you're in business.
4. Look for some data from the Virtue logs (note that you'll need to change the `syslog-2018.07.27` in the URL to match an index that the `indices` command above returned; use today's date if you're not sure what to try...):

        $ curl -X GET --insecure "https://admin:admin@localhost:9200/syslog-2018.07.27/_search?q=LogType:Virtue&pretty"
This will produce a large amount of output. Look the "hits" section, and then the "total" key. This will tell you how many log messages you've received to date.