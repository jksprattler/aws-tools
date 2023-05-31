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

CURRENT_TIME = datetime.datetime.now()
DAYS_THRESHOLD = 30
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
            print(f"Invalid region '{region}'. Available regions:")
            for regions in available_regions:
                print(regions)
            sys.exit()

    if os_version:
        validate_os_version(os_version)

def get_available_regions():
    """
    Get a list of available AWS regions
    """
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in response['Regions']]
    return regions

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
    """
    Parse user arguments, assign region and os values
    Validate the region and os values against conditionals
    Lookup latest available AMI's and output them to color-coded table
    """
    region, os_version = parse_arguments()
    validate_inputs(region, os_version)
    find_amis(region, os_version)

if __name__ == "__main__":
    main()
