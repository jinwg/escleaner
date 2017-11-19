## ES-Cleaner

This is a simple AWS Lambda function that once per day deletes old log indices from ElasticSearch.  To deploy, you need to install [serverless](https://serverless.com) and the (python dependencies plugin)[https://www.npmjs.com/package/serverless-python-requirements].  Provide the region and domain name as deploy options:

```
sls deploy --region us-east-1 --name central-logging
```

The ElasticSearch domain must be in that region.  You can also define an index pattern using a Python regular expression, the default being one compatible with either logstash or the cloudwatch log naming convention:

```
INDEX_REGEX: "(logstash|cwl)-(?P<y>\\d+)\\.(?P<m>\\d+)\\.(?P<d>\\d+)"
```

If you provide your own regex, you must use the group labels y, m, and d.  

The Lambda will run once per day and by default delete indices older than 14 days, although this is configurable via an environment variable in the serverless configuration file.  Note that another fine option for ES 5+ is [Curator](https://github.com/elastic/curator), although this does not support ES versions prior to 5.
