"""
Jenna Sprattler | SRE Kentik | 2023-05-30
Script to output table listing AMI's < 30 days since release date
Output based on region and OS version inputs from user at runtime
Table columns: AMI ID, Name, Architecture and VirtualizationType
Sorted by Architecture type (x86_64, arm64, etc), then sorted by AMI names
"""

import argparse
import sys
import datetime
from tabulate import tabulate
from colorama import Fore, Style
import boto3

current_time = datetime.datetime.now()
DAYS_THRESHOLD = 30
date_threshold = current_time - datetime.timedelta(days=DAYS_THRESHOLD)

def get_available_regions():
    """
    Get a list of available AWS regions
    """
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in response['Regions']]
    return regions

def parse_arguments():
    """ Parse args """
    parser = argparse.ArgumentParser(description='Find AMIs based on region and OS')
    parser.add_argument('region', type=str, help='AWS region')
    parser.add_argument('os_version', type=str, help='OS version')
    return parser.parse_args()

def validate_os_version(os_version):
    """ Check if the provided OS version and AWS region are valid """
    valid_os_versions = ['amzn2', 'debian-11', 'ubuntu-jammy', 'Windows_Server-2019-English']
    for version in valid_os_versions:
        if os_version.startswith(version):
            return
    print(f"Invalid OS version '{os_version}'. Available OS versions:")
    for version in valid_os_versions:
        print(version)
    sys.exit()

args = parse_arguments()

if args.region:
    specified_region = args.region
    available_regions = get_available_regions()
    if specified_region not in available_regions:
        print(f"Invalid region '{specified_region}'. Available regions:")
        for region in available_regions:
            print(region)
        sys.exit()

if args.os_version:
    specified_os_version = args.os_version
    validate_os_version(specified_os_version)

def find_amis(region, os_version):
    """
    Output a list of the latest Amazon owned AMI's for the specified
    region and OS version in color-coded Table format
    """

    ec2_client = boto3.client('ec2', region_name=region)

    response = ec2_client.describe_images(
        Filters=[
            {'Name': 'name', 'Values': ['*'+os_version+'*']},
            {'Name': 'owner-alias', 'Values': ['amazon']}
        ]
    )

    amis = response['Images']

    # Sort the AMIs by architecture type
    sorted_amis = sorted(amis, key=lambda x: (x['Architecture'], x['Name']))
    latest_amis = []
    for ami in sorted_amis:
        creation_date = datetime.datetime.strptime(ami['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        if creation_date >= date_threshold:
            latest_amis.append(ami)

    table = []
    table_headers = ["AMI ID", "Name", "Architecture", "VirtualizationType"]
    for ami in latest_amis:
        table.append([
            f"{Fore.CYAN}{ami['ImageId']}{Style.RESET_ALL}",
            ami['Name'],
            f"{Fore.GREEN}{ami['Architecture']}{Style.RESET_ALL}",
            ami['VirtualizationType']
        ])
    print(tabulate(table, headers=table_headers, tablefmt="grid"))

def main():
    """
    Parse user arguments, assign region and os values
    Lookup latest available AMI's and output them to color-coded table
    """
    args = parse_arguments()
    region = args.region
    os_version = args.os_version
    find_amis(region, os_version)

if __name__ == "__main__":
    main()
