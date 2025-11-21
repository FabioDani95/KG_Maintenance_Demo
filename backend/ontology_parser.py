"""
Dynamic Ontology Parser
Reads JSON ontology files and automatically generates graph nodes and edges
"""
import json
from typing import Dict, List, Any, Tuple


class OntologyParser:
    """Parses ontology JSON and generates graph structure dynamically"""

    # Category detection keywords
    CATEGORY_KEYWORDS = {
        'machine_components': ['component', 'unit', 'system', 'hardware', 'equipment'],
        'maintenance_activities': ['maintenance', 'repair', 'service', 'inspection', 'calibration'],
        'process_parameters': ['parameter', 'setting', 'configuration', 'pressure', 'temperature'],
        'failures_and_anomalies': ['failure', 'anomaly', 'defect', 'fault', 'error'],
        'relationships': ['relationship', 'causal', 'temporal', 'functional', 'dependency'],
        'metrics_and_kpi': ['metric', 'kpi', 'indicator', 'performance', 'efficiency'],
        'documentation': ['document', 'manual', 'guide', 'specification', 'procedure'],
        'safety_and_compliance': ['safety', 'compliance', 'regulation', 'standard', 'hazard'],
        'operating_environment': ['environment', 'condition', 'ambient', 'location'],
        'spare_parts_and_inventory': ['spare', 'part', 'inventory', 'stock', 'material'],
        'integration_and_systems': ['integration', 'interface', 'protocol', 'communication'],
        'human_factors_and_skills': ['human', 'skill', 'operator', 'training', 'competence']
    }

    # Category colors
    CATEGORY_COLORS = {
        'machine_components': '#3b82f6',
        'maintenance_activities': '#10b981',
        'process_parameters': '#f59e0b',
        'failures_and_anomalies': '#ef4444',
        'relationships': '#8b5cf6',
        'metrics_and_kpi': '#ec4899',
        'documentation': '#6366f1',
        'safety_and_compliance': '#f97316',
        'operating_environment': '#14b8a6',
        'spare_parts_and_inventory': '#a855f7',
        'integration_and_systems': '#06b6d4',
        'human_factors_and_skills': '#84cc16',
        'root': '#64748b',
        'other': '#9ca3af'
    }

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_counter = 0

    def parse(self, json_data: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse ontology JSON and return nodes and edges

        Args:
            json_data: The loaded JSON ontology data

        Returns:
            Tuple of (nodes, edges)
        """
        self.nodes = []
        self.edges = []
        self.node_counter = 0

        # Find the root ontology object
        root_key, root_data = self._find_root(json_data)

        if not root_key or not root_data:
            raise ValueError("No valid ontology root found in JSON")

        # Create root node
        root_node = self._create_root_node(root_key, root_data)
        self.nodes.append(root_node)

        # Process the ontology tree
        if 'classes' in root_data:
            self._process_classes(root_data['classes'], 'root', 'root')

        # Process relationships if present
        if 'classes' in root_data and 'relationships' in root_data['classes']:
            self._process_relationships(root_data['classes']['relationships'])

        return self.nodes, self.edges

    def _find_root(self, json_data: Dict[str, Any]) -> Tuple[str, Any]:
        """Find the root ontology object in the JSON"""
        # Common root keys
        root_candidates = [
            'injection_molding_machine_maintenance_ontology',
            'ontology',
            'knowledge_graph',
            'kg',
            'root'
        ]

        # Try known root keys first
        for key in root_candidates:
            if key in json_data:
                return key, json_data[key]

        # If no known root, take the first object-type value
        for key, value in json_data.items():
            if isinstance(value, dict):
                return key, value

        return None, None

    def _create_root_node(self, root_key: str, root_data: Dict) -> Dict:
        """Create the root node"""
        return {
            'data': {
                'id': 'root',
                'label': self._format_label(root_key),
                'category': 'root',
                'color': self.CATEGORY_COLORS['root'],
                'size': 60,
                'path': 'root',
                'properties': {
                    'version': root_data.get('version', 'N/A'),
                    'domain': root_data.get('domain', 'N/A'),
                    'description': root_data.get('description', 'N/A')
                }
            }
        }

    def _process_classes(self, classes: Dict, parent_id: str, parent_path: str):
        """Recursively process classes and create nodes"""
        for key, value in classes.items():
            node_id = f"{parent_path}.{key}"
            category = self._determine_category(key, parent_path)
            is_leaf = not self._is_complex_object(value)

            # Create node
            node = {
                'data': {
                    'id': node_id,
                    'label': self._format_label(key),
                    'category': category,
                    'color': self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS['other']),
                    'size': 30 if is_leaf else 40,
                    'path': node_id,
                    'properties': self._extract_properties(value)
                }
            }
            self.nodes.append(node)

            # Create hierarchical edge
            edge = {
                'data': {
                    'id': f"{parent_id}-{node_id}",
                    'source': parent_id,
                    'target': node_id,
                    'type': 'hierarchical'
                },
                'classes': 'hierarchical'
            }
            self.edges.append(edge)

            # Recurse if value is a complex object
            if isinstance(value, dict):
                has_nested = any(
                    isinstance(v, dict) and not isinstance(v, list)
                    for v in value.values()
                )

                if has_nested:
                    self._process_classes(value, node_id, node_id)

    def _process_relationships(self, relationships: Dict):
        """Process relationships to create relational edges"""
        relationship_types = [
            'causal_relationships',
            'functional_dependencies',
            'temporal_relationships',
            'spatial_relationships',
            'part_of',
            'uses',
            'affects'
        ]

        for rel_type in relationship_types:
            if rel_type not in relationships:
                continue

            rels = relationships[rel_type]

            # Handle both list and dict formats
            if isinstance(rels, list):
                for idx, rel in enumerate(rels):
                    self._create_relational_edge(rel, rel_type, idx)
            elif isinstance(rels, dict):
                for idx, (key, rel) in enumerate(rels.items()):
                    if isinstance(rel, dict):
                        self._create_relational_edge(rel, rel_type, idx)

    def _create_relational_edge(self, rel: Dict, rel_type: str, idx: int):
        """Create a relational edge between nodes"""
        source = rel.get('source')
        target = rel.get('target')

        if not source or not target:
            return

        source_id = self._find_node_by_name(source)
        target_id = self._find_node_by_name(target)

        if source_id and target_id:
            edge = {
                'data': {
                    'id': f"rel-{rel_type}-{idx}",
                    'source': source_id,
                    'target': target_id,
                    'type': 'relational',
                    'relationType': rel.get('type', rel_type.replace('_', ' '))
                },
                'classes': 'relational'
            }
            self.edges.append(edge)

    def _find_node_by_name(self, name: str) -> str:
        """Find node ID by fuzzy matching the name"""
        normalized = name.lower().replace('_', '').replace(' ', '').replace('-', '')

        for node in self.nodes:
            label = node['data']['label'].lower().replace('_', '').replace(' ', '').replace('-', '')
            if normalized in label or label in normalized:
                return node['data']['id']

        return None

    def _determine_category(self, key: str, path: str) -> str:
        """Determine the category of a node based on keywords"""
        key_lower = key.lower()
        path_lower = path.lower()

        # Check each category's keywords
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in key_lower or keyword in path_lower:
                    return category

        return 'other'

    def _extract_properties(self, value: Any) -> Dict:
        """Extract simple properties from a value"""
        if isinstance(value, dict):
            props = {}
            for k, v in value.items():
                if not self._is_complex_object(v):
                    props[k] = v
            return props

        return {'value': value}

    def _is_complex_object(self, obj: Any) -> bool:
        """Check if an object is complex (has nested objects)"""
        if not isinstance(obj, dict):
            return False

        if isinstance(obj, list):
            return False

        return any(
            isinstance(v, dict) and not isinstance(v, list)
            for v in obj.values()
        )

    def _format_label(self, key: str) -> str:
        """Format a key as a display label"""
        return key.replace('_', ' ').title()

    def get_categories(self) -> List[Dict[str, str]]:
        """Get list of categories with colors"""
        return [
            {
                'key': key,
                'label': self._format_label(key),
                'color': color
            }
            for key, color in self.CATEGORY_COLORS.items()
            if key not in ['root', 'other']
        ]
