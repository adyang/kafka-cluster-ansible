# Kafka Cluster Ansible
## Introduction
The playbooks will install a Kafka cluster with interbroker communication using SSL and client-broker communication using SASL PLAIN.

By default, the binaries, logs, configuration and data will be installed into the SSH user's home directory. (See default vars of each role for details.)

This project is created in part to:
1. Try out [Kafka Security Tutorial](https://docs.confluent.io/current/tutorials/security_tutorial.html).
2. Practise extracting Ansible playbooks out into [Roles](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html).
3. And also to try out testing Ansible roles via [Molecule](https://molecule.readthedocs.io/en/stable/).

## Assumptions/ Requirements
Control Machine:
* Ansible 2.8.1 installed

Target Machines:
* OS is Debian Stretch (9)
* Java 8 is installed
* Deploy/ Ansible user has full sudo permissions
  - This is mainly to configure and run Kafka/ Zookeeper as a Systemd service
  - Full sudo permissions is required due to Ansible limitations: [Can’t limit escalation to certain commands](https://docs.ansible.com/ansible/latest/user_guide/become.html#can-t-limit-escalation-to-certain-commands)
  - In environments that practise "Principle of least privilege", you would need to modify the roles to use the Shell/ Command module to configure Systemd

## Running Playbooks via Vagrant
1. Bring up vagrant machines
```console
$ vagrant up
```

2. Generate and copy test certificates to the machines
```console
$ ansible-playbook -i ansible/hosts ansible/generate-test-certs.yml -vv
```
This will create test CA and broker/client keystores signed by the CA. They will be generated locally in the directory `ansible/certificates` and copied to the corresponding machines. The default password for all the stores is `password`.

3. Create credentials file

Create a `credentials.yml` file that contains the password for the key/trust stores and also to initialise the password for the users that are created in Zookeeper/Kafka for SASL PLAIN:
```console
$ cat <<EOF > credentials.yml
---
zookeeper_super_pass: admin-secret
zookeeper_kafka_pass: kafka-secret
kafka_truststore_pass: password
kafka_keystore_pass: password
kafka_key_pass: password
kafka_kafkabroker_pass: kafkabroker-secret
kafka_client_pass: client-secret
kafka_zookeeper_kafka_pass: kafka-secret

EOF
```

4. Install Kafka cluster
```console
$ ansible-playbook -i ansible/hosts ansible/install.yml --extra-vars '@credentials.yml' -vv
```

5. Try Producing and Consuming from Cluster

We will need to provide security properties in order to communicate with the broker via SASL PLAIN. We can use the user `client` and its password that was setup in the `install.yml` playbook.

```console
$ vagrant ssh kafka-1

$ cat <<EOF > client/client-security.properties
security.protocol=SASL_SSL
ssl.truststore.location=/home/vagrant/client/kafka.client.truststore.jks
ssl.truststore.password=password
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required     username=\"client\"     password=\"client-secret\";

EOF

$ ~/confluent-5.2.2/bin/kafka-topics --zookeeper localhost:2181 --create --topic test --partitions 10 --replication-factor 3

$ ~/confluent-5.2.2/bin/kafka-acls --authorizer-properties zookeeper.connect=localhost:2181 --add --allow-principal User:client --producer --topic test

$ ~/confluent-5.2.2/bin/kafka-acls --authorizer-properties zookeeper.connect=localhost:2181 --add --allow-principal User:client --consumer --topic test --group test

$ printf 'test-message' | ~/confluent-5.2.2/bin/kafka-console-producer --broker-list kafka-1:9094 --producer.config client/client-security.properties --topic test

$ ~/confluent-5.2.2/bin/kafka-console-consumer --bootstrap-server kafka-1:9094 --consumer.config client/client-security.properties --topic test --group test --from-beginning --max-messages 1
test-message
Processed a total of 1 messages
```

## Testing Roles via Molecule
1. Install Docker or ensure it is installed
```console
$ docker --version
```

2. Install molecule with docker support
```console
$ pip3 install --user 'molecule[docker]==2.22rc3'
```

3. Install Squid (Optional)

In order to speed up the downloading of binaries (molecule destroys the docker container after each test), we can setup [Squid](http://www.squid-cache.org/) as a local cache.

On macOS, we can install SquidMan to help manage Squid:
```console
$ brew cask install squidman
```

Add the following to the top of the Squid template (it can be found via `Cmd + ,` to Settings > Template) to cache everything:
```
cache allow all
```
Adjust on disk cache size and max object size to allow caching of the Kafka binaries:
```
# disk and memory cache settings
cache_dir ufs %CACHEDIR% 4096 16 256
maximum_object_size 1 GB
cache_mem %MEMCACHESIZE%
maximum_object_size_in_memory %MEMMAXOBJECTSIZE%
```
In particular, replace `%CACHESIZE%` with `4096` and `%MAXOBJECTSIZE%` with `1 GB`.

4. Run molecule tests
```console
$ export http_proxy="$(ipconfig getifaddr en0):8080"

$ (cd ansible/roles/kafka && molecule test)

$ (cd ansible/roles/zookeeper && molecule test)
```
`ipconfig getifaddr en0` only works on macOS. If not developing on macOS, use `ifconfig` to find the local machine's IP address.

The `http_proxy` variable needs to be set to the IP of the local machine in order for the container hosts to reach the Squid proxy cache. It can be omitted if we are not using a local cache.
