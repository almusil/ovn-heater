from collections import defaultdict
from fnmatch import fnmatch
from io import StringIO


# The wrapper allows us to execute the command on all
# matching central containers
class CentralNodeWrapper(object):
    def __init__(self, central_node, container):
        self.node = central_node
        self.container = container

    def run(self, cmd='', stdout=None):
        self.node.phys_node.run(
            f'docker exec {self.container} {cmd}', stdout=stdout
        )


class ExtCmdUnit(object):
    def __init__(self, conf, central_node, worker_nodes):
        self.iteration = conf.get('iteration')
        self.cmd = conf.get('cmd')
        self.test = conf.get('test')
        self.pid_name = conf.get('pid_name')
        self.background_opt = conf.get('background_opt')
        self.pid_opt = conf.get('pid_opt', '')

        node = conf.get('node')
        self.nodes = [n for n in worker_nodes if fnmatch(n.container, node)]
        self.nodes.extend(
            [
                CentralNodeWrapper(central_node, c)
                for c in central_node.central_containers()
                if fnmatch(c, node)
            ]
        )

    def is_valid(self):
        return (
            bool(self.iteration)
            and bool(self.cmd)
            and bool(self.test)
            and bool(self.nodes)
        )

    def exec(self):
        return [self._node_exec(node) for node in self.nodes]

    def _node_exec(self, node):
        cmd = self.cmd

        if self.pid_name:
            stdout = StringIO()
            node.run(f'pidof -s {self.pid_name}', stdout=stdout)
            cmd += f' {self.pid_opt} {stdout.getvalue().strip()}'

        if self.background_opt:
            cmd += ' &'

        stdout = StringIO()
        node.run(cmd, stdout=stdout)
        return stdout.getvalue().strip()


class ExtCmd(object):
    def __init__(self, config, central_node, worker_nodes):
        cmd_list = [
            ExtCmdUnit(ext_cmd, central_node, worker_nodes)
            for ext_cmd in config.get('ext_cmd', list())
        ]
        cmd_list.sort(key=lambda x: x.iteration)

        self.cmd_map = defaultdict(list)
        for ext_cmd in cmd_list:
            if ext_cmd.is_valid():
                self.cmd_map[(ext_cmd.iteration, ext_cmd.test)].append(ext_cmd)

    def exec_cmd(self, iteration, test):
        ext_cmds = self.cmd_map.get((iteration, test))
        if not ext_cmds:
            return

        return [ext_cmd.exec() for ext_cmd in ext_cmds]
