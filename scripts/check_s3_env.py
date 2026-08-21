import os

def print_env(key):
    print(f"{key}={repr(os.environ.get(key))}")

for k in ('S3_BUCKET','AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_REGION','S3_PREFIX'):
    print_env(k)
