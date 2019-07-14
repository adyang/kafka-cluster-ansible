import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_kafka_service_is_running_and_enabled(host):
    kafka = host.service('kafka')

    assert kafka.is_running
    assert kafka.is_enabled


def test_kafka_interbroker_communication_is_up(host):
    assert host.socket("tcp://9093").is_listening


def test_kafka_sasl_client_communication_is_up(host):
    assert host.socket("tcp://9094").is_listening


def test_kafka_cluster_is_up(host):
    zookeeper_shell = '${HOME}/confluent-5.2.2/bin/zookeeper-shell localhost:2181 '
    response = host.check_output(zookeeper_shell + r'ls /brokers/ids | grep -oP "\[.*\]"')

    assert response == '[1, 2, 3]'


def test_cluster_replication(host):
    confluent_bin = '${HOME}/confluent-5.2.2/bin/'
    host.run(confluent_bin + 'kafka-topics --zookeeper localhost:2181 '
                             '--create --topic test --partitions 10 --replication-factor 3')
    host.run(confluent_bin + 'kafka-acls --authorizer-properties zookeeper.connect=localhost:2181 '
                             '--add --allow-principal User:client --producer --topic test')
    host.run(confluent_bin + 'kafka-acls --authorizer-properties zookeeper.connect=localhost:2181 '
                             '--add --allow-principal User:client --consumer --topic test --group test')
    host.run('printf "test-message" '
             '| ' + confluent_bin + 'kafka-console-producer --broker-list kafka-1:9094 '
             '--topic test --producer.config ${HOME}/client/client-security.properties')

    response = host.run(confluent_bin + 'kafka-console-consumer --bootstrap-server $(hostname):9094 '
                                        '--consumer.config ${HOME}/client/client-security.properties '
                                        '--topic test --group test '
                                        '--from-beginning --max-messages 1 --timeout-ms 10000')

    assert 'test-message' in response.stdout

    host.run(confluent_bin + 'kafka-topics --zookeeper localhost:2181 '
                             '--delete --topic test')

