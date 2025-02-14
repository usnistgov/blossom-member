#!/usr/bin/env python3
# Generate a connection profile

from itertools import chain

import boto3


def gen_channels(channels: 'list', orderer_name: str, peers_dict: 'dict'):
    # flatten dict of lists into list
    peers = list(chain(*(peers_dict.values())))

    return {
        channel: {
            'orderers': [orderer_name],
            'peers': {
                node['Id']: {
                    'chaincodeQuery': True,
                    'ledgerQuery': True,
                    'endorsingPeer': True,
                    'eventSource': True
                }
                for node in peers
            }
        }
        for channel in channels
    }

def gen_orderers(network, tlsCaCertPath: str):
    # looks like orderer.(...).amazon.com:300xx
    endpoint = network['FrameworkAttributes']['Fabric']['OrderingServiceEndpoint']

    return {
        f'orderer-{network["Name"]}': {
            'url': f'grpcs://{endpoint}',
            'grpcsOptions': {
                # strip port
                'ssl-target-name-override': endpoint.split(':')[0],
            },
            'tlsCACerts': {
                'path': tlsCaCertPath
            }
        }
    }

def gen_organizations(members, peers_dict):
    return {
        member['Name']: {
            'mspid': member['Id'],
            'peers': [
                peer['Id']
                for peer in peers_dict[member['Name']]
            ],
            "certificateAuthorities": [f'ca-{member["Name"]}']
        }
        for member in members
    }

def gen_peers(peers_dict, tlsCaCertPath: str):
    return {
        peer['Id']: {
            'url': f'grpcs://{peer["FrameworkAttributes"]["Fabric"]["PeerEndpoint"]}',
            'eventUrl': f'grpcs://{peer["FrameworkAttributes"]["Fabric"]["PeerEventEndpoint"]}',
            'grpcsOptions': {
                'ssl-target-name-override': peer["FrameworkAttributes"]["Fabric"]["PeerEndpoint"].split(':')[0]
            },
            'tlsCACerts': {
                'path': tlsCaCertPath
            }
        }
        for peer in list(chain(*(peers_dict.values())))
    }

def gen_certificate_authorities(members, tlsCaCertPath: str):
    return {
        f'ca-{member["Name"]}': {
            'url': member['FrameworkAttributes']['Fabric']['CaEndpoint'],
            'httpOptions': {
                'verify': False
            },
            'tlsCACerts': {
                'path': tlsCaCertPath
            },
            'caName': member['Id']
        }
        for member in members
    }

def gen_connection_profile(network_id: str, channels: str, tlsCaCertPath: str):
    client = boto3.client('managedblockchain')
    
    network = client.get_network(NetworkId=network_id)['Network']
    # get a list of member summaries, then get the actual member objects
    members = [
        client.get_member(NetworkId=network_id, MemberId='m-DTLKIKVWWZER3DUHQUDH43I7YQ')['Member']
    ]

    # members = [
    #     client.get_member(NetworkId=network_id, MemberId=summary['Id'])['Member']
    #     for summary in client.list_members(NetworkId=network_id)['Members']
    # ]

    # for each member, get a list of node summaries, then get the actual node objects
    nodes = {
        member['Name']: [
            client.get_node(NetworkId=network_id, MemberId=member['Id'], NodeId=summary['Id'])['Node']
            for summary in client.list_nodes(NetworkId=network_id, MemberId=member['Id'])['Nodes']
        ]
        for member in members
    }

    network_name = network['Name']
    orderer_name = f'orderer-{network["Name"]}'

    ### print(f'\n\t🐞🐞🐞 {channels=}\n\t🐞🐞🐞')
    channels_list = [item.strip() for item in channels.split(",")]
    ### print(f'\n\t🐞🐞🐞{channels=}\n\t🐞🐞🐞')

    return {
        'name': network_name,
        'x-type': 'hlfv1',
        'description': f'Generated connection profile',
        'version': '1.0',
        'channels': gen_channels(channels_list, orderer_name, nodes),
        'orderers': gen_orderers(network, tlsCaCertPath),
        'organizations': gen_organizations(members, nodes),
        'peers': gen_peers(nodes, tlsCaCertPath),
        'certificateAuthorities': gen_certificate_authorities(members, tlsCaCertPath),
    }

if __name__ == '__main__':
    import json
    from argparse import ArgumentParser
    from sys import stderr
    
    parser = ArgumentParser('gen-connection-profile.py',
        description='Generate a connection profile')
    parser.add_argument('--network_id', type=str, required=True,
        help="The network id (starts with n-...)")
    parser.add_argument('--channels', default=['authorization', 'business'],
        help='Channels to include in the profile')
    parser.add_argument('--tlsCaCertPath',
        default='/home/ec2-user/managedblockchain-tls-chain.pem',
        help='The location from which TLS cert will be loaded by clients')
    args = parser.parse_args()

    ### print('\n\t🐞🐞🐞')
    ### print(vars(args))
    ### print('\t🐞🐞🐞\n')

    connection_profile = gen_connection_profile(**args.__dict__)
    print(json.dumps(connection_profile, indent=4))

    if len(args.channels) == 0:
        print("WARNING: no channels were specified", file=stderr)
