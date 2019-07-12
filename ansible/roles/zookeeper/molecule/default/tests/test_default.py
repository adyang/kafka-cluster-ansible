import os

import testinfra.utils.ansible_runner

ansible = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE'])
testinfra_hosts = ansible.get_hosts('all')


def test_zookeeper_service_is_running_and_enabled(host):
    zookeeper = host.service('zookeeper')

    assert zookeeper.is_running
    assert zookeeper.is_enabled


def test_zookeeper_is_up(host):
    response = host.check_output('printf "ruok" | nc localhost 2181')

    assert response == 'imok'


def test_zookeeper_cluster_is_up(host):
    response = host.check_output('printf "stat"'
                                 '| nc localhost 2181'
                                 '| grep Mode'
                                 '| cut -d " " -f 2')

    assert response in ('follower', 'leader')


def test_cluster_replication(host):
    zookeeper_shell = '${HOME}/confluent-5.2.2/bin/zookeeper-shell localhost:2181 '
    single = ansible.get_host('zookeeper-1')
    create_response = single.run(zookeeper_shell + 'create /testnode testvalue')
    assert 'Created' in create_response.stderr

    get_response = host.check_output(zookeeper_shell + 'get /testnode')

    assert 'testvalue' in get_response
    single.run(zookeeper_shell + 'delete /testnode')

