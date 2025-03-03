"""
Jenna Sprattler | SRE Kentik | 2023-05-30
Script to output table listing AMI's < 90 days since release date
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
import fnmatch

CURRENT_TIME = datetime.datetime.now()
DAYS_THRESHOLD = 90
DATE_THRESHOLD = CURRENT_TIME - datetime.timedelta(days=DAYS_THRESHOLD)

def parse_arguments():
    """ Parse args """
    parser = argparse.ArgumentParser(description='Find AMIs based on region and OS')
    parser.add_argument('region', type=str, help='AWS region')
    parser.add_argument('os_version', type=str, help='OS version')
    args = parser.parse_args()
    return args.region, args.os_version

def validate_inputs(region, os_version):
    """ Validate region and OS version if provided"""
    if region:
        available_regions = get_available_regions()
        if region not in available_regions:
            print(f"Invalid {'region:':<10}  '{region}'")
            print()
            print(f"Available regions:")
            for regions in available_regions:
                print(regions)
            sys.exit()

    valid_os_versions = get_valid_os_versions()
    if not os_version or not any(fnmatch.fnmatch(os_version, version) for version in valid_os_versions):
        print(f"Invalid or missing OS {'version:':<10} '{os_version}'")
        print()
        print("Available OS versions:")
        for version in valid_os_versions:
            print(version)
        print()
        print(f"{'Tip:':<10} Append OS version with more specifics to narrow down results")
        print(f"{'Example:':<10} 'python aws_ami_finder.py us-east-1 debian-12'")
        sys.exit()

def get_available_regions():
    """
    Get a list of available AWS regions
    """
    ec2_client = boto3.client('ec2', region_name='us-west-2')
    response = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in response['Regions']]
    return regions

def get_valid_os_versions():
    """ Return the list of valid OS versions """
    return ['amzn2', 'debian*', 'rhel*', 'suse*', 'ubuntu*', 'Windows*']

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

    # Sort the AMIs by architecture type and name
    sorted_amis = sorted(amis, key=lambda x: (x['Architecture'], x['Name']))
    latest_amis = []
    for ami in sorted_amis:
        creation_date = datetime.datetime.strptime(ami['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        if creation_date >= DATE_THRESHOLD:
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
    if len(sys.argv) < 3:
        print(f"{'Usage:':<10} python aws_ami_finder.py <region> <os_version>")
        print()
        print("Available OS versions:")
        for version in get_valid_os_versions():
            print(version)
        print()
        print(f"{'Tip:':<10} Append OS version with more specifics to narrow down results")
        print(f"{'Example:':<10} 'python aws_ami_finder.py us-east-1 debian-12'")
        sys.exit()

    region, os_version = parse_arguments()
    validate_inputs(region, os_version)
    find_amis(region, os_version)

if __name__ == "__main__":
    main()
