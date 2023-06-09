"""
Jenna Sprattler | SRE Kentik | 2023-06-09
Searches for S3 bucket objects by passing args
for AWS profile, bucket name and object name
Lists all keys matching provided object name
Lists buckets in AWS profile to help find bucket objects
"""
import argparse
import boto3

def parse_args():
    """ Define cli args to be parsed into main() """
    parser = argparse.ArgumentParser(description='Search for an object in an S3 bucket.')
    subparser = parser.add_subparsers(dest='command', help='Additional commands')
    parser.add_argument('-p', '--profile', required=True, help='AWS profile name')
    subparser.add_parser('list',
                    help='List buckets in the specified profile, use after specifying --profile')
    parser.add_argument('-b', '--bucket', help='S3 bucket name')
    parser.add_argument('-o', '--object', help='Object name to search for')
    parser.add_argument('-x', '--prefix', help='Object prefix for faster search')
    args = parser.parse_args()

    if args.command == 'list':
        return args

    if not args.profile or not args.bucket or not args.object:
        parser.print_usage()
        return None

    return args

def list_buckets(profile):
    """ List buckets in specified profile """
    session = boto3.Session(profile_name=profile)
    s3_client = session.client('s3')
    response = s3_client.list_buckets()
    buckets = response['Buckets']

    for bucket in buckets:
        print(bucket['Name'])

def search_s3_object(profile_name, bucket_name, object_name, object_prefix):
    """
    Create a session using the specified profile
    Create s3 client using the session
    Perform recursive search using pagination for the S3 bucket object
    Use optional prefix for faster results when dealing w/ high volume objects
    """
    session = boto3.Session(profile_name=profile_name)
    s3_client = session.client('s3')
    paginator = s3_client.get_paginator('list_objects_v2')
    list_objects_args = {'Bucket': bucket_name}

    if object_prefix:
        list_objects_args['Prefix'] = object_prefix

    page_iterator = paginator.paginate(**list_objects_args)

    for page in page_iterator:
        if 'Contents' in page:
            # Check if the object name is in the retrieved keys
            objects = [obj['Key'] for obj in page['Contents'] if object_name in obj['Key']]

            if objects:
                print(f"'{object_name}' found in bucket '{bucket_name}'")
                for obj in objects:
                    print(f"Key(s) matching '{object_name}': {bucket_name}/{obj}")
                return

    print(f"'{object_name}' not found in bucket '{bucket_name}'")

def main():
    """ Parse args and call either S3 bucket list or object search function """
    args = parse_args()

    if not args:
        return

    if args.command == 'list':
        list_buckets(args.profile)
    else:
        if not args.bucket or not args.object:
            return

        search_s3_object(args.profile, args.bucket, args.object, args.prefix)

if __name__ == "__main__":
    main()
