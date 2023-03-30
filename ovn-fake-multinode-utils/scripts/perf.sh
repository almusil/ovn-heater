#!/bin/bash -xe

host=$1
node_name=$2

function collect_perf_data() {
    c=$1
    mkdir ${host}-perf/$c
    pid=$(docker exec $c /bin/sh -c "pidof -s perf")
    docker exec $c /bin/sh -c "kill $pid && tail --pid=$pid -f /dev/null"
    docker exec $c /bin/sh -c "perf script report flamegraph -o /tmp/ovn-perf.html"
    docker cp $c:/tmp/ovn-perf.html ${host}-perf/$c/
}

mkdir /tmp/${host}-perf

pushd /tmp
for c in $(docker ps --format "{{.Names}}" --filter "name=${node_name}"); do
    collect_perf_data $c
done

for c in $(docker ps --format "{{.Names}}" --filter "name=ovn-central"); do
    collect_perf_data $c
done

tar cvfz ${host}-perf.tgz ${host}-perf
rm -rf ${host}-perf
popd
