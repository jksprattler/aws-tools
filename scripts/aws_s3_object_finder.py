"""
Jenna Sprattler | SRE Kentik | 2023-06-09
Search for S3 bucket objects by passing args for AWS profile,
bucket name, object name and optional prefix
Lists all keys matching provided object name
Lists buckets and top-level prefixes in AWS profile to help find objects
"""
import argparse
import boto3

def parse_args():
    """ Define cli args to be parsed into main() """
    parser = argparse.ArgumentParser(description='Search for an object in an S3 bucket.')
    parser.add_argument('-p', '--profile', required=True, help='AWS profile name')
    parser.add_argument('-b', '--bucket', help='S3 bucket name')
    parser.add_argument('-o', '--object', help='Object name to search for')
    parser.add_argument('-x', '--prefix', help='Object prefix for high volume bucket search')
    subparser = parser.add_subparsers(dest='command', help='Additional commands')
    subparser.add_parser('list-buckets',
                         help='List buckets in profile, use after -p')
    subparser.add_parser('list-prefixes', help='List top-level prefixes in bucket,\
                                                use after -p and -b')
    args = parser.parse_args()

    if args.command == 'list-buckets':
        return args

    if args.command == 'list-prefixes' and args.bucket:
        return args

    if not args.bucket or (not args.bucket and not args.command == 'list-prefixes') \
        or not args.object:
        parser.print_usage()
        return None

    return args

def list_buckets(profile_name):
    """ List buckets in specified profile """
    session = boto3.Session(profile_name=profile_name)
    s3_client = session.client('s3')
    buckets = s3_client.list_buckets()['Buckets']

    for bucket in buckets:
        print(bucket['Name'])

def list_prefixes(profile_name, bucket_name):
    """ List top-level prefixes in a specified bucket """
    session = boto3.Session(profile_name=profile_name)
    s3_client = session.client('s3')
    paginator = s3_client.get_paginator('list_objects_v2')
    list_objects_args = {'Bucket': bucket_name, 'Delimiter': '/'}
    page_iterator = paginator.paginate(**list_objects_args)

    prefixes = []
    for page in page_iterator:
        if 'CommonPrefixes' in page:
            # Iterate over the CommonPrefixes list and extract top-level prefixes
            prefixes.extend([prefix['Prefix'] for prefix in page['CommonPrefixes']])

    if prefixes:
        for prefix in prefixes:
            print(prefix)
    else:
        print(f"No top-level prefixes found in bucket '{bucket_name}'")


def search_s3_object(profile_name, bucket_name, object_name, object_prefix):
    """
    Create a session using the specified profile
    Create s3 client using the session
    Perform recursive search using pagination for the S3 bucket object
    Use optional prefix when dealing w/ high volume objects
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

    if args.command == 'list-buckets':
        list_buckets(args.profile)
    elif args.command == 'list-prefixes':
        list_prefixes(args.profile, args.bucket)
    else:
        search_s3_object(args.profile, args.bucket, args.object, args.prefix)

if __name__ == "__main__":
    main()
