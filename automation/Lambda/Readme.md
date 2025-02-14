### The lambda code has to be deployed to the Blossom-S3-Watcher Lambda body

#### The configuration of lambda must have the following triggers on S3 Bucket observed:
#### 1. Event types: s3:ObjectCreated:*
#### 2. s3:ObjectRemoved:Delete 