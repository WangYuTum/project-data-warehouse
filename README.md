# Data Engineer Nanodegree Subproject
The repository contains the project information of the **Data Warehouse with AWS Redshift** from Udacity Nanodegree 
**[Data Engineer](https://www.udacity.com/course/data-engineer-nanodegree--nd027)**. Please refer to the 
course [website](https://www.udacity.com/course/data-engineer-nanodegree--nd027) for more details.<br/>

Project scenario: A startup called Sparkify has grown their user base and song database and want to move their data process onto 
the cloud. Their data resides in AWS S3 including user activity logs and song metadata in *JSON* format.<br/>

## Business Process / Data Requirements
- Analytics team wants to understand **what songs** their **users** are listening to by analyzing a set of dimensional tables.
- Analytics team wants a **Data warehouse on the cloud** with tables designed to **optimize queries** and gain insights on song plays.

## Engineering Task
- Create and launch a Redshift cluster on AWS 
  - Create a Redshift cluster and IAM role to grant access to S3
- Create a star schema and ETL pipeline to prepare the data for analytics team
  - Explore & load raw data (*JSON*) in S3 to Redshift staging tables
  - Define fact & dimension tables for a star schema for this particular analytic purpose
  - Write an ETL pipeline to load data from staging tables to analytics tables on Redshift
- Connect to the Redshift cluster and run some test queries

## Tools Used
- Python 3
- [AWS](https://aws.amazon.com/)
- [Redshift SQL](https://docs.aws.amazon.com/redshift/latest/dg/welcome.html)
- [Python configparser](https://docs.python.org/3/library/configparser.html)
- [Psycopg2](https://pypi.org/project/psycopg2/)
- [LucidChart](https://www.lucidchart.com/)

## Original Data Sources
**Note** that the actual data (in *JSON*) used in this project is a subset of original dataset preprocessed by the course. The provided data 
resides in AWS S3 (publically available).
1. Song data from [Million Song Dataset](http://millionsongdataset.com/)
2. User activity data from [Event Simulator](https://github.com/Interana/eventsim) based on [Million Song Dataset](http://millionsongdataset.com/)

## Database Schema (Data Warehousing) Design
**User Story**: A **user** plays a **song** whose artist is **artist_name** at time **start_time** using **agent**.<br/>
From the above story, we can extract the necessary information/dimensions:

- **Who**: **users** dimension
- **What**: **songs** and **artists** dimension
- **When**: **time** dimension
- **How (many)**: **songplays** fact
- (More possible dimensions but not used in this project):
    - **Where**: **locations** dimension
    - **How**: **agents** dimension

Since the core business process/metric is an user playing a song, the fact table should store the song play records with 
user/song identifier together with related information about the how and where the song is played. Based on the data and tables 
given in the project, the star schema looks like this (generated using [LucidChart](https://www.lucidchart.com/)):
![erd](assets/images/ERD.png)

## ETL Process

## Usage and Sample Results
### Setup & Configuration
1. Setup your IAM user (with programmatic) Access Key and Secret Key with the following commands:
- ``export AWS_ACCESS_KEY_ID=your_access_key_id`` 
- ``export AWS_SECRET_ACCESS_KEY=your_secret_access_key``<br/><br/>
**Note:** You can also setup your Access Key and Secret Key by storing them in config or credential files. 
However we **strongly recommend** the above approach because you won't need to change the codes.<br/>
2. Create your Redshift cluster using the following scripts:
- ``cluster_start_shutdown/cluster.cfg``: Defines Redshift cluster Hardware/Database setup and region/role names. You can change them however you want.
- ``cluster_start_shutdown/start_cluster.py``: All-in-One script to launch the Redshift cluster and handles IAM Role/Policy creation and SecurityGroup configurations.
We **strongly recommend** you to use this script to create the cluster and auto-configure all related resources/services. You **MUST** have a running cluster 
in order to proceed with ETL and query experiments later.
- ``cluster_start_shutdown/shutdown_cluster.py``: All-in-One script to shutdown the cluster and clean up all related resources for this project. We **strongly recommend** you to run this script after you are done with the experiments/project to prevent any further costs induced by AWS Redshift services.
3. Fill the **HOST** and **ARN** in ``dwh.cfg``. You can get their values by runing ``cluster_start_shutdown/start_cluster.py`` in previous step.
4. Run ``create_tables.py``.
5. Run ``etl.py`` to load data from S3 into staging tables and then transfer into target tables (fact and dimension tables). You may choose a smaller dataset 
"``s3://udacity-dend/song_data``" (4-min runtime) instead of a complete one "``s3://udacity-dend/song-data``" (2 hours runtime) for demonstration purpose.
<br    > **Note** that you can use **NOLOAD** option in **COPY** command to verify JSON data correctness/integrity without loading the actual data into tables. 
You can then check errors or violation of data format by running the query "``select * from pg_catalog.stl_load_errors;``" on Redshift cluster.

### Sample Queries
**Note** that you must finish the ETL process before running the sample queries.
1. Top-10 most played songs.
- Query:
```
  SELECT sp.song_id, s.title, count(*) AS cnt 
    FROM songplays sp
    JOIN songs s
      ON sp.song_id = s.song_id
GROUP BY 1, 2
ORDER BY 3 DESC
   LIMIT 10;
```
- Result:
![query1](assets/images/query1.png)<br/>

2. Top-10 most played artists.
- Query:
```
  SELECT sp.artist_id, a.name AS artist_name, count(*) AS cnt
    FROM songplays sp
    JOIN artists a
      ON sp.artist_id = a.artist_id
GROUP BY 1, 2
ORDER BY 3 DESC
   LIMIT 10;
```
- Result:
![query2](assets/images/query2.png)<br/>

3. Statistics on when songs are played during a day
- Query:
```
  SELECT CASE
           WHEN t.hour BETWEEN 2 AND 8  THEN '2~8'
           WHEN t.hour BETWEEN 9 AND 12 THEN '9~12'
           WHEN t.hour BETWEEN 13 AND 18 THEN '13~18'
           WHEN t.hour BETWEEN 19 AND 22 THEN '19~22'
           ELSE '23~24, 0~2'
         END AS play_time, 
         count(*) AS cnt
    FROM songplays sp
    JOIN time t
      ON sp.start_time = t.start_time
GROUP BY 1
ORDER BY 2 DESC;

```
- Result:
![query3](assets/images/query3.png)
We can tell from the above result that most users play songs in the afternoon between 13:00 and 18:00 and very few users play songs in (late)mid-night.
4. Another interesting query would be aggregating song play history for each user and use it for machine learning/recommendation.

## Implementation Details/Notes
1. Redshift does not enforce ``NOT NULL`` constraint on **PRIMARY KEY**, **FOREIGN KEY** and **REFERENCE _table_name_ (_column_name_)**.
2. Redshift does not enforce uniqueness constraint on **PRIMARY KEY**. However the auto-generated **IDENTITY** column is guaranteed to have unique value across entire table.
3. Redshift does not enforce referential integrity on keyword **REFERENCE _table_name_ (_column_name_)** or **FOREIGN KEY**, they are only used by query planers to 
optimize performance.

## TODOs
1. Analyze table design and performance via trying different distribution styles and sorting keys.

## Resources
1. [Intro to AWS Redshift Cluster Management](https://docs.aws.amazon.com/redshift/latest/mgmt/welcome.html): how to create and manage Redshift clusters on AWS.
2. [Developer guide to AWS Redshift](https://docs.aws.amazon.com/redshift/latest/dg/welcome.html): how to create and develop data warehouses using Redshift.
3. [Python SQL client/driver psycopg2](https://www.psycopg.org/docs/): how to use psycopg2 to connect to SQL PostgreSQL-compatible databases and execute queries.
4. [psycopg2 with Redshift](https://rudderstack.com/blog/access-and-query-your-amazon-redshift-data-using-python-and-r/): how to use psycopg2 to connect to databases on AWS Redshift and execute queries.
5. [Redshift python SDK: boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)