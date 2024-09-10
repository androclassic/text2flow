
import re
import graphviz



def text2graph(flowchart_text):

    nodes = {}
    edges = []
    stack = []
    n_label_2_id = {}
    
    current_indent = -1


    def has_colon_outside_brackets(s):
        # This regex matches colons that are not inside square brackets
        pattern = r':(?![^\[]*\])'
        res = re.search(pattern, s)
        if res:
            return res.start()+1
        else:
            return 0
        
    def translate_reference(label):
        if label[0]=="(":
            if label[1]=="#":
                node_id = label[2:-1]
            else:
                node_id = label[1:-1]
            
            label = nodes[node_id]['label']
        return label

    
    def add_node(label, attributes, tags):
        node_id = attributes.get('id', label)
        
        if node_id in nodes:
            return node_id
        
        nodes[node_id] = {
            'label': label,
            'attributes': attributes,
            'tags': tags
        }
        return node_id

    def add_edge(from_node, to_node, label=None, metadata=dict()):
        metadata = metadata.copy() 
        if len(metadata):
            print(metadata)
        metadata['from'] = from_node
        metadata['to'] = to_node
        metadata['label'] = label
        edges.append(metadata)
        
    def parse_attributes(content):
        attr_match = re.search(r'\[(.*?)\]', content)
        attributes = {}

        if attr_match:
            attr_str = attr_match.group(1)
            for attr in attr_str.split():
                key, value = attr.split('=')
                attributes[key] = value.strip('"')

            content = content[:attr_match.start()].strip()
        return content, attributes

    def parse_id_and_tags(content):
        # Parse , ID, and tags

        parts = content.split()
        label_parts = []
        tags = []
        node_id = None

        k=0
        for idx, part in enumerate(parts):
            if part.startswith('.') or part.startswith('#'):
                break
            k = idx
            label_parts.append(part)
            
        parts = parts[k+1:]
        label = ' '.join(label_parts)
        for part in parts:
            if part.startswith('.'):
                tags.append(part[1:])
            elif part.startswith('#'):
                assert node_id is None, "cannot have more than 1 id per element"
                node_id = part[1:]
            else:
                assert False, f"syntax error {content}"

        return label, node_id, tags


    def parse_line(line):
        content, attr = parse_attributes(line)
        label, node_id, tags = parse_id_and_tags(content)
        return label, node_id, tags, attr
        


    lines = flowchart_text.strip().split('\n')
    for line in lines:
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        attributes = {}

        
        edge_delimiter = has_colon_outside_brackets(line)
        
        if edge_delimiter==0:
            edge_content = None
            node_content = line
        else:
            edge_content = line[:edge_delimiter-1].strip()
            node_content = line[edge_delimiter:]

        label, node_id, tags, attr = parse_line(node_content)
        
        
        label = translate_reference(label)
        if node_id:
            attributes['id'] = node_id
            n_label_2_id[label] = node_id
        elif label in n_label_2_id:
            attributes['id'] =n_label_2_id[label]
                        
        # Add node
        node_id = add_node(label, attributes, tags)

        if edge_content is None:
            e_label = None
            e_attr = dict()
        else:
            # TODO: extend if needed
            e_label, e_id, e_tags, e_attr = parse_line(edge_content)

        # Handle indentation and edges
        if indent > current_indent:
            if stack:
                add_edge(stack[-1], node_id, label=e_label, metadata=e_attr)
            stack.append(node_id)
        elif indent == current_indent:
            stack.pop()
            if stack:
                add_edge(stack[-1], node_id)
            stack.append(node_id)
        else:
            while stack and indent <= current_indent:
                stack.pop()
                current_indent -= 2
            if stack:
                add_edge(stack[-1], node_id)
            stack.append(node_id)

        current_indent = indent

    # Resolve references
    for edge in edges:
        if edge['from'].startswith('(') and edge['from'].endswith(')'):
            u_id = edge['from'][1:-1] if edge['from'][1]!='#' else edge['from'][2:-1]
            edge['from'] = nodes[u_id]['label']
        if edge['to'].startswith('(') and edge['to'].endswith(')'):
            u_id = edge['to'][1:-1] if edge['to'][1]!='#' else edge['to'][2:-1]
            edge['to'] = nodes[u_id]['label']

                    
    

    return nodes, edges



def create_graph(nodes, edges):
    dot = graphviz.Digraph()

    # Define node styles based on tags
    tag_styles = {
        'position': {'shape': 'box', 'color': 'cornflowerblue'},
        'action': {'shape': 'ellipse', 'color': 'chartreuse3'},
        'system': {'shape': 'diamond', 'color': 'lightyellow'},
        'submission': {'shape': 'octagon', 'color': 'firebrick3'},
        'reaction': {'shape': 'hexagon', 'color': 'coral'}
    }

    # Add nodes with styles and URLs
    for node_id, node_info in nodes.items():
        label = node_info['label']
        href = node_info['attributes'].get('href', '')
        tags = node_info['tags']
        
        # Determine node style
        style = {'shape': 'ellipse', 'color': 'white'}  # Default style
        for tag in tags:
            if tag in tag_styles:
                style = tag_styles[tag]
                break
        dot.node(node_id, label=label, shape=style['shape'], style='filled', fillcolor=style['color'], href=href)

    # Add edges with labels if specified
    for edge in edges:
        from_node = edge['from']
        to_node = edge['to']
        label = edge.get('label', '')
        style = edge.get('style', 'solid')
        color = edge.get('color')
        dot.edge(from_node, to_node, label=label, style=style, color=color, penwidth=edge.get("penwidth"), width=edge.get("width") )

    return dot