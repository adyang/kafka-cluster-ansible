# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end

  (1..3).each do |i|
    config.vm.define "zookeeper-#{i}" do |zookeeper|
      zookeeper.vm.hostname = "zookeeper-#{i}"
      zookeeper.vm.box = "debian/contrib-stretch64"
      zookeeper.ssh.insert_key = false
      zookeeper.vm.network "private_network", ip: "192.168.204.5#{i}"
      zookeeper.vm.provision "shell", inline: <<-SHELL
        sudo apt update
        sudo apt install -y openjdk-8-jre

        for i in {1..3}; do
          entry="192.168.204.5${i} zookeeper-${i}"
          grep -qF -- "${entry}" /etc/hosts || echo "${entry}" | tee -a /etc/hosts
          entry="192.168.204.6${i} kafka-${i}"
          grep -qF -- "${entry}" /etc/hosts || echo "${entry}" | tee -a /etc/hosts
        done
      SHELL
    end
    config.vm.define "kafka-#{i}" do |kafka|
      kafka.vm.hostname = "kafka-#{i}"
      kafka.vm.box = "debian/contrib-stretch64"
      kafka.ssh.insert_key = false
      kafka.vm.network "private_network", ip: "192.168.204.6#{i}"
      kafka.vm.provision "shell", inline: <<-SHELL
        sudo apt update
        sudo apt install -y openjdk-8-jre

        for i in {1..3}; do
          entry="192.168.204.5${i} zookeeper-${i}"
          grep -qF -- "${entry}" /etc/hosts || echo "${entry}" | tee -a /etc/hosts
          entry="192.168.204.6${i} kafka-${i}"
          grep -qF -- "${entry}" /etc/hosts || echo "${entry}" | tee -a /etc/hosts
        done
      SHELL
    end
  end
end
