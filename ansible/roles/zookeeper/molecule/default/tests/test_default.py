import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_zookeeper_is_up(host):
    response = host.check_output('printf "ruok" | nc localhost 2181')

    assert response == 'imok'

