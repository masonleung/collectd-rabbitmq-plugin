# collectd rabbitmq plugin

Get the following rabbitmq stats

1. memory size
1. queue size
1. incoming messages per second
1. delivered messages per second
1. acked messages per seconds

Put the config in /etc/collectd/conf.d

    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      ModulePath "/usr/local/bin/collectd/plugins"
      Import "rabbitmq_stats"

      <Module rabbitmq_stats>
        Port 55672
        Username guest
        Password guest
      </Module>
    </Plugin>
