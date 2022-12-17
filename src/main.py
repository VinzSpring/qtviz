import os
import re
import statistics
import sys
from typing import *

class QConnect:
    def __init__(self, file: str, sender: str, sender_class: str, signal: str, receiver: str, receiver_class: str, slot: str):
        self.file = file
        self.sender = sender
        self.signal = signal
        self.receiver = receiver
        self.slot = slot
        self.sender_class = sender_class
        self.receiver_class = receiver_class

def find_qconnects(file: str) -> List[QConnect]:
    file = file.replace('\\', '/')
    # new connect syntax
    # connect(sender, &Sender::signal, receiver, &Receiver::slot)
    new_syntax = re.compile(r'connect\((?P<sender>\w+),\s*&(?P<sender_class>\w+)::(?P<signal>\w+),\s*(?P<receiver>\w+),\s*&(?P<receiver_class>\w+)::(?P<slot>\w+)\)')
    # old connect syntax
    # connect(sender, SIGNAL(signal()), receiver, SLOT(slot()))
    old_syntax = re.compile(r'connect\((?P<sender>\w+),\s*SIGNAL\((?P<signal>\w+)\(\)\),\s*(?P<receiver>\w+),\s*SLOT\((?P<slot>\w+)\(\)\)\)')
    qconnects = []

    with open(file, 'r', encoding='utf-8') as f:
        src_code = f.read()

    for match in new_syntax.finditer(src_code):
        qconnects.append(QConnect(file, match.group('sender'), match.group('sender_class'), match.group('signal'), match.group('receiver'), match.group('receiver_class'), match.group('slot')))
    for match in old_syntax.finditer(src_code):
        qconnects.append(QConnect(file, match.group('sender'), None, match.group('signal'), match.group('receiver'), None, match.group('slot')))

    return qconnects

def recursive_find_qconnects(path: str) -> List[QConnect]:
    qconnects = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.cpp') or file.endswith('.h'):
                qconnects.extend(find_qconnects(os.path.join(root, file)))
    return qconnects


def visualise_qconnects(qconnects: List[QConnect]) -> str:
    graph = 'digraph G {\n'
    graph += 'rankdir=LR;\n'
    graph += 'node [shape=box];\n'
    graph += 'edge [fontsize=10];\n'

    qconnects_map = {}
    for qconnect in qconnects:
        if qconnect.file not in qconnects_map:
            qconnects_map[qconnect.file] = []
        qconnects_map[qconnect.file].append(qconnect)

    graph += 'subgraph cluster_file_graphs {\n'
    graph += 'label="Files";\n'
    graph += f'color=blue;\n'

    for file, connects in qconnects_map.items():
        graph += f'subgraph cluster_{re.sub(r"[^a-zA-Z0-9]", "_", file)} {{\n'
        graph += f'label="{file}";\n'
        graph += f'color=blue;\n'
        for qconnect in connects:
            graph += f'"{qconnect.file}/{qconnect.sender_class}" [label="class: {qconnect.sender_class if qconnect.sender_class else "old connect-syntax not supported"}\nname: {qconnect.sender}"];\n'
            graph += f'"{qconnect.file}/{qconnect.receiver_class}" [label="class: {qconnect.receiver_class if qconnect.receiver_class else "old syntax not supported"}\nname: {qconnect.receiver}"];\n'
        for qconnect in connects:
            graph += f'"{qconnect.file}/{qconnect.sender_class}" -> "{qconnect.file}/{qconnect.receiver_class}" [label="{qconnect.signal} → {qconnect.slot}"];\n'
        graph += f'}}\n'
    graph += '}\n'

    graph += 'subgraph cluster_class_graphs {\n'
    graph += 'label="Classes";\n'
    graph += f'color=blue;\n'
    nodes = set()
    for qconnect in qconnects:
        if qconnect.sender_class is None or qconnect.receiver_class is None:
            continue
        nodes.add(f'"{qconnect.sender_class}" [label="class: {qconnect.sender_class}"];\n')
        nodes.add(f'"{qconnect.receiver_class}" [label="class: {qconnect.receiver_class}"];\n')
    graph += ''.join(nodes)

    connections = {}
    for qconnect in qconnects:
        if qconnect.sender_class is None or qconnect.receiver_class is None:
            continue
        connection = f'"{qconnect.sender_class}" -> "{qconnect.receiver_class}"'
        if connection not in connections:
            connections[connection] = 0
        connections[connection] += 1

    max_connections = max(connections.values())
    for connection, count in connections.items():
        hex_color = f'{int(255 * (count / max_connections)):02x}{int(255 * (1 - count / max_connections)):02x}00'
        graph += f'{connection} [label="{qconnect.signal} →{count}→ {qconnect.slot}" color="#{hex_color}"];\n'

    graph += '}\n'

    graph += '}'
    return graph

def main():
    args = sys.argv[1:]    
    path = args[0]
    qconnects = []
    qconnects.extend(recursive_find_qconnects(path))
    graph = visualise_qconnects(qconnects)
    print(graph)
    with open('graph.dot', 'w+', encoding='utf-8') as f:
        f.write(graph)

if __name__ == '__main__':
    main()
