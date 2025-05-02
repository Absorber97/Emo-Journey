"""
Graph Planner module for EmoJourney.
Implements emotion transition graph and Dijkstra's algorithm for path finding.
"""
from typing import Dict, List, Tuple, Set, Optional, Union
import heapq

class EmotionGraph:
    """
    Graph representation of emotions and their transitions.
    Implements Dijkstra's algorithm for finding shortest paths.
    """
    
    def __init__(self):
        """Initialize an empty emotion graph with adjacency list representation."""
        # Adjacency list: {emotion_name: [(neighbor_emotion, distance), ...]}
        self.graph: Dict[str, List[Tuple[str, int]]] = {}
        
        # Initialize with default emotion connections
        self._build_default_graph()
    
    def _build_default_graph(self):
        """
        Build the default emotion transition graph.
        Based on psychological models of emotion transitions.
        """
        # Define emotion transitions with weights
        # Lower weight = easier transition
        transitions = [
            # Joy connections
            ("joy", "trust", 1),
            ("joy", "anticipation", 1),
            ("joy", "surprise", 2),
            
            # Sadness connections
            ("sadness", "fear", 1),
            ("sadness", "disgust", 2),
            ("sadness", "trust", 3),
            
            # Anger connections
            ("anger", "disgust", 1),
            ("anger", "fear", 2),
            ("anger", "anticipation", 3),
            
            # Fear connections
            ("fear", "surprise", 1),
            ("fear", "sadness", 1),
            ("fear", "anger", 2),
            
            # Disgust connections
            ("disgust", "anger", 1),
            ("disgust", "sadness", 2),
            ("disgust", "surprise", 3),
            
            # Surprise connections
            ("surprise", "joy", 2),
            ("surprise", "fear", 1),
            ("surprise", "trust", 2),
            
            # Trust connections
            ("trust", "joy", 1),
            ("trust", "anticipation", 1),
            ("trust", "sadness", 3),
            
            # Anticipation connections
            ("anticipation", "joy", 1),
            ("anticipation", "trust", 1),
            ("anticipation", "anger", 3),
        ]
        
        # Build the graph from transitions
        for source, target, weight in transitions:
            # Add both directions (make it undirected)
            self.add_edge(source, target, weight)
            self.add_edge(target, source, weight)
    
    def add_node(self, emotion: str):
        """
        Add a new emotion node to the graph.
        
        Args:
            emotion: The name of the emotion to add
        """
        if emotion not in self.graph:
            self.graph[emotion] = []
    
    def add_edge(self, source: str, target: str, weight: int = 1):
        """
        Add an edge between two emotions.
        
        Args:
            source: Source emotion
            target: Target emotion
            weight: Weight of the transition (default=1)
        """
        # Create nodes if they don't exist
        self.add_node(source)
        self.add_node(target)
        
        # Add the edge
        self.graph[source].append((target, weight))
    
    def get_neighbors(self, emotion: str) -> List[Tuple[str, int]]:
        """
        Get all neighbors of an emotion with their distances.
        
        Args:
            emotion: The emotion to get neighbors for
            
        Returns:
            List of tuples (neighbor_emotion, distance)
        """
        return self.graph.get(emotion, [])
    
    def dijkstra(self, start: str, end: str) -> Tuple[Union[int, float], List[str]]:
        """
        Find the shortest path between two emotions using Dijkstra's algorithm.
        
        Args:
            start: Starting emotion
            end: Target emotion
            
        Returns:
            Tuple containing (total_distance, path)
            Distance can be int or float('inf') if no path exists
        """
        if start not in self.graph or end not in self.graph:
            return float('inf'), []
        
        # Track distances from start to each node
        distances = {node: float('inf') for node in self.graph}
        distances[start] = 0
        
        # Track paths
        previous = {node: None for node in self.graph}
        
        # Priority queue for efficient node selection
        priority_queue = [(0, start)]
        
        # Track visited nodes
        visited: Set[str] = set()
        
        while priority_queue:
            # Get the node with the smallest distance
            current_distance, current = heapq.heappop(priority_queue)
            
            # If we've reached the end, build and return the path
            if current == end:
                path = []
                while current:
                    path.append(current)
                    current = previous[current]
                path.reverse()
                return distances[end], path
            
            # Skip if already visited
            if current in visited:
                continue
            
            # Mark as visited
            visited.add(current)
            
            # Check all neighbors
            for neighbor, weight in self.graph[current]:
                # Calculate distance through current node
                distance = current_distance + weight
                
                # If we found a shorter path, update
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        # No path found
        return float('inf'), []
    
    def get_emotion_steps(self, current: str) -> Dict[str, Tuple[Union[int, float], List[str]]]:
        """
        Calculate steps required to reach each emotion from current emotion.
        
        Args:
            current: Current emotion
            
        Returns:
            Dictionary mapping {target_emotion: (distance, path)}
            Distance can be int or float('inf') if no path exists
        """
        result = {}
        
        for target in self.graph:
            if target == current:
                continue
            
            distance, path = self.dijkstra(current, target)
            result[target] = (distance, path)
        
        return result
    
    def get_closest_emotions(self, current: str, n: int = 2) -> List[Tuple[str, Union[int, float], List[str]]]:
        """
        Get the n closest emotions to reach from current.
        Ensures a minimum of 2 steps for any emotional journey.
        
        Args:
            current: Current emotion
            n: Number of emotions to return
            
        Returns:
            List of tuples (emotion, distance, path)
            Distance can be int or float('inf') if no path exists
        """
        emotion_steps = self.get_emotion_steps(current)
        
        # Enforce minimum of 2 steps for any emotional journey
        for emotion, (distance, path) in emotion_steps.items():
            # If path is too short (1 step), artificially extend it
            if distance == 1 or (path and len(path) <= 2):
                # Set to at least 2 steps
                modified_distance = max(2, distance)
                # Create a modified path if needed
                if path and len(path) <= 2:
                    # If direct path (just start->end), add intermediary
                    # We'll duplicate the end emotion to make a 3-node path
                    if len(path) == 2:
                        modified_path = path[:-1] + [path[-1], path[-1]]
                    else:
                        modified_path = [current, emotion, emotion]  # Safe fallback
                else:
                    modified_path = path if path else [current, emotion, emotion]
                    
                emotion_steps[emotion] = (modified_distance, modified_path)
        
        # Sort by distance (fewer steps first)
        sorted_emotions = sorted(emotion_steps.items(), key=lambda x: x[1][0])
        
        # Return top n emotions with their distances and paths
        return [(emotion, distance, path) 
                for emotion, (distance, path) in sorted_emotions[:n]] 