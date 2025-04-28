import xml.etree.ElementTree as ET
import sys

if len(sys.argv) != 2:
    print("Usage: python3 parse_xml.py <file.xml>")

file = sys.argv[1]

name = file.split('.')[0] + '.txt'

# Parse the XML
tree = ET.parse(file)  # Replace with your XML file path
root = tree.getroot()

# Find nodes and edges
nodes = root.findall(".//node")
edges = root.findall(".//edge")

# Open output file
with open(name, 'w', encoding='utf-8') as f:
    f.write(f"# Vertices {len(nodes)} Edges {len(edges)}\n")
    f.write("# FromNodeId ToNodeId Weight\n")
    for edge in edges:
        source = edge.attrib['source']
        target = edge.attrib['target']
        weight = edge.attrib['weight']
        f.write(f"{source} {target} {weight}\n")
