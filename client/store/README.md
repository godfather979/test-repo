# Project Overview
================

**Project Title:** Architecture Graph
**Project Description:** A comprehensive architecture graph module to analyze and visualize the structure of software projects.
**Project Version:** 1.0.0

**Table of Contents**
-----------------

1. [Setup](#setup)
2. [Folder Structure](#folder-structure)
3. [API Documentation](#api-documentation)
4. [Function Documentation](#function-documentation)

## Setup
--------

To get started with the Architecture Graph module, follow these steps:

### Prerequisites

* Python 3.8 or higher
* pip package manager

### Installation

1. Clone the repository: `git clone https://github.com/your-username/architecture-graph.git`
2. Navigate to the project directory: `cd architecture-graph`
3. Install dependencies: `pip install -r requirements.txt`

### Running the Module

1. Run the module using Python: `python main.py`
2. The module will analyze the project structure and display the architecture graph.

## Folder Structure
-----------------

The Architecture Graph module follows a standard folder structure:

```markdown
architecture-graph/
|____ main.py
|____ requirements.txt
|____ src/
|     |____ graph.py
|     |____ node.py
|     |____ edge.py
|____ tests/
|     |____ test_graph.py
|____ docs/
|     |____ README.md
|____ .gitignore
```

## API Documentation
-------------------

### Graph Module

* **`create_graph()`**: Creates a new architecture graph.
* **`add_node(node)`**: Adds a node to the graph.
* **`add_edge(node1, node2)`**: Adds an edge between two nodes.
* **`display_graph()`**: Displays the architecture graph.

### Node Module

* **`Node(name, description)`**: Creates a new node with a name and description.
* **`get_name()`**: Returns the node's name.
* **`get_description()`**: Returns the node's description.

### Edge Module

* **`Edge(node1, node2, weight)`**: Creates a new edge between two nodes with a weight.
* **`get_weight()`**: Returns the edge's weight.

## Function Documentation
-------------------------

### Graph Module

#### `create_graph()`

Creates a new architecture graph.

* **Parameters:** None
* **Returns:** A new graph object
* **Example:** `graph = create_graph()`

#### `add_node(node)`

Adds a node to the graph.

* **Parameters:** `node` (a Node object)
* **Returns:** None
* **Example:** `node = Node('Node 1', 'This is node 1')`
`graph.add_node(node)`

#### `add_edge(node1, node2)`

Adds an edge between two nodes.

* **Parameters:** `node1` and `node2` (Node objects)
* **Returns:** None
* **Example:** `node1 = Node('Node 1', 'This is node 1')`
`node2 = Node('Node 2', 'This is node 2')`
`graph.add_edge(node1, node2)`

#### `display_graph()`

Displays the architecture graph.

* **Parameters:** None
* **Returns:** None
* **Example:** `graph.display_graph()`

### Node Module

#### `Node(name, description)`

Creates a new node with a name and description.

* **Parameters:** `name` and `description` (strings)
* **Returns:** A new Node object
* **Example:** `node = Node('Node 1', 'This is node 1')`

#### `get_name()`

Returns the node's name.

* **Parameters:** None
* **Returns:** A string representing the node's name
* **Example:** `print(node.get_name())`

#### `get_description()`

Returns the node's description.

* **Parameters:** None
* **Returns:** A string representing the node's description
* **Example:** `print(node.get_description())`

### Edge Module

#### `Edge(node1, node2, weight)`

Creates a new edge between two nodes with a weight.

* **Parameters:** `node1` and `node2` (Node objects), and `weight` (a number)
* **Returns:** A new Edge object
* **Example:** `edge = Edge(node1, node2, 5)`

#### `get_weight()`

Returns the edge's weight.

* **Parameters:** None
* **Returns:** A number representing the edge's weight
* **Example:** `print(edge.get_weight())`