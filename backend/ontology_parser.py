"""
Dynamic Ontology Parser
Reads JSON ontology files and automatically generates graph nodes and edges
"""
import json
from typing import Dict, List, Any, Tuple, Optional


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

        if not root_key or not isinstance(root_data, dict):
            root_key = root_key or 'ontology'
            root_data = json_data if isinstance(json_data, dict) else {}

        classes_data = self._get_section(root_data, json_data, 'classes')
        instances_data = self._get_section(root_data, json_data, 'instances')
        instance_metadata = json_data.get('machine_instance') if isinstance(
            json_data.get('machine_instance'), dict
        ) else None

        content_types = []
        if classes_data:
            content_types.append('TBox definitions')
        if instances_data or instance_metadata:
            content_types.append('ABox instances')

        # Create root node ONLY if we have TBox (classes) but no ABox instances
        # For ABox-only files, we don't need a root node
        if classes_data and not (instances_data or instance_metadata):
            root_node = self._create_root_node(root_key, root_data, content_types)
            self.nodes.append(root_node)
        elif not instances_data and not instance_metadata:
            # Fallback: create root if we have nothing else
            root_node = self._create_root_node(root_key, root_data, content_types)
            self.nodes.append(root_node)

        # Process optional machine instance metadata (ABox)
        if instance_metadata:
            self._process_classes(
                {'machine_instance': instance_metadata},
                'root',
                'root',
                node_type='instance'
            )

        # Process TBox classes if available
        if classes_data:
            self._process_classes(classes_data, 'root', 'root', node_type='definition')

            # Process relationships if present
            relationships_data = classes_data.get('relationships')
            if isinstance(relationships_data, dict):
                self._process_relationships(relationships_data)

        # Process ABox instances if available
        if instances_data:
            self._process_instances(instances_data)

        # Process explicit edges if available
        # Check for edges in root_data first, then fallback to json_data
        edges_data = None
        for source in (root_data, json_data):
            if isinstance(source, dict) and 'edges' in source and isinstance(source['edges'], list):
                edges_data = source['edges']
                break

        if edges_data:
            self._process_explicit_edges(edges_data)

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

    def _get_section(
        self,
        primary: Optional[Dict[str, Any]],
        fallback: Optional[Dict[str, Any]],
        key: str
    ) -> Optional[Dict[str, Any]]:
        """Return a named section searching root data first, then full JSON"""
        for source in (primary, fallback):
            if isinstance(source, dict) and key in source and isinstance(source[key], dict):
                return source[key]
        return None

    def _create_root_node(
        self,
        root_key: str,
        root_data: Dict,
        content_types: Optional[List[str]] = None
    ) -> Dict:
        """Create the root node"""
        properties = {
            'data': {
                'id': 'root',
                'label': self._format_label(root_key),
                'category': 'root',
                'color': self.CATEGORY_COLORS['root'],
                'size': 60,
                'path': 'root',
                'node_type': 'root'
            }
        }

        root_properties = {
            'version': root_data.get('version', 'N/A'),
            'domain': root_data.get('domain', 'N/A'),
            'description': root_data.get('description', 'N/A')
        }

        # Merge additional simple metadata from the root object
        extracted_props = self._extract_properties(root_data)
        for key, value in extracted_props.items():
            if key in root_properties and root_properties[key] != 'N/A':
                continue
            root_properties[key] = value

        if content_types:
            root_properties['contains'] = content_types

        properties['data']['properties'] = root_properties
        return properties

    def _process_classes(self, classes: Dict, parent_id: str, parent_path: str, node_type: str):
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
                    'properties': self._extract_properties(value),
                    'node_type': node_type
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
                    self._process_classes(value, node_id, node_id, node_type)

    def _process_instances(self, instances: Dict):
        """Process instances and create flat nodes (not recursive)"""
        for instance_id, instance_data in instances.items():
            if not isinstance(instance_data, dict):
                continue

            # Use the instance ID directly as the node ID
            node_id = f"root.instances.{instance_id}"

            # Get the instance type
            instance_type = instance_data.get('type', 'Instance')

            # Determine category based on type
            category = self._categorize_instance_type(instance_type)

            # Extract all properties (including 'type')
            properties = {}
            for key, value in instance_data.items():
                # Store all properties as-is, without recursion
                properties[key] = value

            # Determine human-readable label
            label = self._get_instance_label(instance_id, instance_data)

            # Create node
            node = {
                'data': {
                    'id': node_id,
                    'label': label,
                    'category': category,
                    'color': self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS['other']),
                    'size': 40,
                    'path': node_id,
                    'properties': properties,
                    'node_type': 'instance'
                }
            }
            self.nodes.append(node)

            # NO hierarchical edge from root - instances are standalone

    def _categorize_instance_type(self, instance_type: str) -> str:
        """Map instance type to category"""
        type_lower = instance_type.lower()

        # Machine components mapping
        component_types = [
            'machine', 'screwbarrelassembly', 'heatingsystem', 'injectiondrive',
            'fixedplaten', 'movingplaten', 'tiebars', 'guidebushings',
            'clampingmechanism', 'ejectorsystem', 'pump', 'valveset',
            'actuator', 'hydraulicoil', 'heatexchanger', 'filter',
            'controller', 'hmi', 'sensorset', 'sensor', 'temperaturesensor',
            'mold'
        ]

        for comp_type in component_types:
            if comp_type in type_lower.replace('_', ''):
                return 'machine_components'

        # Maintenance tasks and events
        if 'maintenancetask' in type_lower.replace('_', '') or 'maintenanceevent' in type_lower.replace('_', ''):
            return 'maintenance_activities'

        # Materials and spare parts
        if 'material' in type_lower.replace('_', ''):
            return 'spare_parts_and_inventory'

        # Default to other
        return 'other'

    def _get_instance_label(self, instance_id: str, instance_data: dict) -> str:
        """Generate human-readable label for an instance"""
        instance_type = instance_data.get('type', '')

        # For MaintenanceTask, use description
        if 'MaintenanceTask' in instance_type or 'MaintenanceEvent' in instance_type:
            description = instance_data.get('description', '')
            if description:
                return description

        # For Machine, use model or manufacturer + model
        if 'Machine' in instance_type:
            model = instance_data.get('model', '')
            manufacturer = instance_data.get('manufacturer', '')
            if model and manufacturer:
                return f"{manufacturer} {model}"
            elif model:
                return model

        # For Material, use material_name
        if 'Material' in instance_type:
            material_name = instance_data.get('material_name', '')
            if material_name:
                return material_name

        # For Mold, use mold_id
        if 'Mold' in instance_type:
            mold_id = instance_data.get('mold_id', '')
            if mold_id:
                return mold_id

        # For TemperatureSensor, use zone
        if 'TemperatureSensor' in instance_type:
            zone = instance_data.get('zone', '')
            if zone:
                return f"Temperature Sensor {zone.replace('_', ' ').title()}"

        # For components with specific names, try to use descriptive properties
        # Otherwise use the instance_id
        return instance_id

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

    def _process_explicit_edges(self, edges_list: List[Dict]):
        """Process explicit edges from the JSON edges section"""
        for edge_def in edges_list:
            if not isinstance(edge_def, dict):
                continue

            source = edge_def.get('source')
            target = edge_def.get('target')
            edge_type = edge_def.get('type', 'related')
            edge_id = edge_def.get('id', f"edge-{len(self.edges)}")
            label = edge_def.get('label', '')

            if not source or not target:
                continue

            # Try to find node IDs by matching the instance IDs
            source_node_id = self._find_instance_node(source)
            target_node_id = self._find_instance_node(target)

            if source_node_id and target_node_id:
                # Determine edge class based on type
                edge_class = 'causal' if edge_type == 'causal' else 'relational'

                edge = {
                    'data': {
                        'id': edge_id,
                        'source': source_node_id,
                        'target': target_node_id,
                        'type': edge_type,
                        'label': label
                    },
                    'classes': edge_class
                }

                # Add any additional properties from the edge definition
                for key, value in edge_def.items():
                    if key not in ['source', 'target', 'type', 'id', 'label']:
                        edge['data'][key] = value

                self.edges.append(edge)

    def _find_instance_node(self, instance_id: str) -> Optional[str]:
        """Find the full node ID for an instance ID"""
        # First try exact match with root.instances prefix
        candidate = f"root.instances.{instance_id}"
        if any(node['data']['id'] == candidate for node in self.nodes):
            return candidate

        # Try finding by partial match
        for node in self.nodes:
            node_id = node['data']['id']
            if node_id.endswith(f".{instance_id}"):
                return node_id

        # If no match found, return None
        return None

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
