import pulumi
from pulumi_aws import ec2

# Create a VPC
my_vpc = ec2.Vpc(
    "pulumi-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "PulumiVPC"
    }
)

# Create a subnet
my_public_subnet = ec2.Subnet(
    "my-public-subnet",
    vpc_id=my_vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone="us-east-1a",
    tags={
        "Name": "MyPublicSubnet"
    }
)

# Create an Internet Gateway (IgW)
my_igw = ec2.InternetGateway(
    "my-igw",
    vpc_id=my_vpc.id,
    tags={
        "Name": "MyIgW"
    }
)

# Create a route table
my_route_table = ec2.RouteTable(
    "my-route-table",
    vpc_id=my_vpc.id,
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": my_igw.id
        },
    ],
    tags={
        "Name": "MyRouteTable"
    }
)

# Associate RouteTable with Public Subnet
route_table_association = ec2.RouteTableAssociation(
    "my-route-table-association",
    subnet_id=my_public_subnet.id,
    route_table_id=my_route_table.id    
)

# Create a Security Group and SG Rules
sg = ec2.SecurityGroup(
    "my-sg",
    vpc_id=my_vpc.id,
    description="Allow inbound HTTP, SSH, and ICMP",
    ingress=[
        ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow SSH access",
        ),
        ec2.SecurityGroupIngressArgs(
            protocol="icmp",
            from_port=-1,
            to_port=-1,
            cidr_blocks=["0.0.0.0/0"],
            description="Enable Ping",
        ),
        ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTP access",
        ),
    ],
    egress=[
        ec2.SecurityGroupEgressArgs(
            protocol="-1",  # Allow all outbound traffic
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={"Name": "Pulumi-SG"},
)

pulumi.export("SG ID", sg.id)
pulumi.export("VPC ID", my_vpc.id)


# User Data Script to Install Nginx
user_data_script = """#!/bin/bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
echo "<h1>Welcome to Pulumi Nginx Server</h1>" | sudo tee /var/www/html/index.html
"""


# Create EC2 instance with the defined security group
ec2_instance = ec2.Instance(
    "my-ec2-instance",
    ami="ami-0866a3c8686eaeeba",  # Replace with a valid AMI ID
    instance_type="t2.micro",
    subnet_id=my_public_subnet.id,
    security_groups=[sg.id],  # Attach the security group here
    associate_public_ip_address=True,  # Make it publicly accessible
    key_name="demo-ec2",
    user_data=user_data_script,
    tags={"Name": "MyEC2Instance"},
)

pulumi.export("EC2 Public IP", ec2_instance.public_ip)
