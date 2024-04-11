from typing import Literal
import googleapiclient.discovery

def change_instances(size: Literal[0] | Literal[1]):

    compute = googleapiclient.discovery.build('compute', 'v1')

    project = 'i-hexagon-304409'
    zone = 'europe-west1-b'
    instance_group = 'minecraft-instance-group-1'

    request = compute.instanceGroupManagers().resize(
        project=project,
        zone=zone,
        instanceGroupManager=instance_group,
        size=size,
    ).execute()

    return request


if __name__ == '__main__':
    import sys
    arg = sys.argv[1]
    try:
        size = int(arg)
    except ValueError:
        print('invalid size')
        sys.exit(1)
    
    if size != 0 and size != 1:
        print('invalid size')
        sys.exit(1)

    change_instances(size)
    print('done')