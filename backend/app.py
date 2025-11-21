"""
Flask Backend for Dynamic Ontology Visualization
Loads JSON ontologies and serves graph data via REST API
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from ontology_parser import OntologyParser

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global state
current_ontology = None
parser = OntologyParser()

# Configuration
UPLOAD_FOLDER = 'uploads'
FRONTEND_FOLDER = '../frontend'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory(FRONTEND_FOLDER, 'index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static frontend files"""
    return send_from_directory(FRONTEND_FOLDER, path)


@app.route('/api/upload', methods=['POST'])
def upload_ontology():
    """Upload and parse ontology JSON file"""
    global current_ontology

    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.json'):
            return jsonify({'error': 'File must be a JSON file'}), 400

        # Read and parse JSON
        json_data = json.load(file)

        # Parse ontology
        nodes, edges = parser.parse(json_data)

        # Store current ontology
        current_ontology = {
            'nodes': nodes,
            'edges': edges,
            'raw': json_data
        }

        return jsonify({
            'message': 'Ontology loaded successfully',
            'stats': {
                'nodes': len(nodes),
                'edges': len(edges)
            }
        })

    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing ontology: {str(e)}'}), 500


@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get current graph data (nodes and edges)"""
    if current_ontology is None:
        return jsonify({'error': 'No ontology loaded'}), 404

    return jsonify({
        'nodes': current_ontology['nodes'],
        'edges': current_ontology['edges']
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of available categories"""
    categories = parser.get_categories()
    return jsonify({'categories': categories})


@app.route('/api/node/<path:node_id>', methods=['GET'])
def get_node(node_id):
    """Get details for a specific node"""
    if current_ontology is None:
        return jsonify({'error': 'No ontology loaded'}), 404

    # Find node by ID
    node = next(
        (n for n in current_ontology['nodes'] if n['data']['id'] == node_id),
        None
    )

    if node is None:
        return jsonify({'error': 'Node not found'}), 404

    # Get connected edges
    incoming = [e for e in current_ontology['edges'] if e['data']['target'] == node_id]
    outgoing = [e for e in current_ontology['edges'] if e['data']['source'] == node_id]

    return jsonify({
        'node': node,
        'incoming_edges': incoming,
        'outgoing_edges': outgoing
    })


@app.route('/api/search', methods=['GET'])
def search_nodes():
    """Search nodes by query string"""
    if current_ontology is None:
        return jsonify({'error': 'No ontology loaded'}), 404

    query = request.args.get('q', '').lower()

    if not query:
        return jsonify({'results': []})

    # Search in node labels and paths
    results = [
        node for node in current_ontology['nodes']
        if query in node['data']['label'].lower() or
           query in node['data']['path'].lower()
    ]

    return jsonify({'results': results})


@app.route('/api/filter', methods=['POST'])
def filter_nodes():
    """Filter nodes by categories"""
    if current_ontology is None:
        return jsonify({'error': 'No ontology loaded'}), 404

    data = request.get_json()
    enabled_categories = data.get('categories', [])

    if not enabled_categories:
        return jsonify({
            'nodes': current_ontology['nodes'],
            'edges': current_ontology['edges']
        })

    # Filter nodes
    filtered_nodes = [
        node for node in current_ontology['nodes']
        if node['data']['category'] in enabled_categories or
           node['data']['category'] == 'root'
    ]

    # Get IDs of visible nodes
    visible_ids = {node['data']['id'] for node in filtered_nodes}

    # Filter edges (only show if both source and target are visible)
    filtered_edges = [
        edge for edge in current_ontology['edges']
        if edge['data']['source'] in visible_ids and
           edge['data']['target'] in visible_ids
    ]

    return jsonify({
        'nodes': filtered_nodes,
        'edges': filtered_edges
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about current ontology"""
    if current_ontology is None:
        return jsonify({'error': 'No ontology loaded'}), 404

    # Calculate statistics
    categories = {}
    for node in current_ontology['nodes']:
        cat = node['data']['category']
        categories[cat] = categories.get(cat, 0) + 1

    edge_types = {}
    for edge in current_ontology['edges']:
        edge_type = edge['data']['type']
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    return jsonify({
        'total_nodes': len(current_ontology['nodes']),
        'total_edges': len(current_ontology['edges']),
        'categories': categories,
        'edge_types': edge_types
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ontology_loaded': current_ontology is not None
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  KNOWLEDGE GRAPH MAINTENANCE - Backend Server")
    print("=" * 60)
    print()
    print("  Server starting on: http://localhost:8000")
    print()
    print("  API Endpoints:")
    print("    - POST /api/upload        : Upload ontology JSON")
    print("    - GET  /api/graph         : Get graph data")
    print("    - GET  /api/categories    : Get categories")
    print("    - GET  /api/node/<id>     : Get node details")
    print("    - GET  /api/search?q=...  : Search nodes")
    print("    - POST /api/filter        : Filter by categories")
    print("    - GET  /api/stats         : Get statistics")
    print("    - GET  /api/health        : Health check")
    print()
    print("=" * 60)
    print()

    app.run(debug=True, host='0.0.0.0', port=8000)
