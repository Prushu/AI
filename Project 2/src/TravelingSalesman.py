#!/usr/bin/python
import sys
import os
import time
from copy import deepcopy
from FileHandler import FileHandler
from Graph import Route, Graph, BreadthFirstSearchTree, DepthFirstSearchStack
import numpy as np


class TravelingSalesman():
    @staticmethod
    def breadth_first_search(graph, source_vertex_id=1, target_vertex_id=11):
        bfs_tree = BreadthFirstSearchTree()

        current_vertex = graph.get_vertex_by_id(source_vertex_id)
        route = Route([current_vertex.vertex_id], graph)
        current_layer = 0
        current_node = BreadthFirstSearchTree.Node("source", current_vertex, str(current_layer), route)
        node_index = 1
        bfs_tree.add_node(current_node)

        # Iterate over each layer in the bfs tree and create the next layer
        while str(current_layer) in bfs_tree.nodes.keys():
            # Iterate over all nodes
            for node in bfs_tree.nodes[str(current_layer)]:
                # Loop over its adjacent vertices
                for adjacent_vertex in node.vertex.adjacent_vertices:
                    # Copy the route of the current node
                    current_route = deepcopy(node.minimum_route)

                    # Update the current route with the new vertex goto
                    current_route.goto(adjacent_vertex.vertex_id)

                    # Create a node representation of the vertex/route
                    adjacent_node = BreadthFirstSearchTree.Node(str(node_index), adjacent_vertex, str(current_layer+1), current_route)

                    # Try to add the node
                    if bfs_tree.add_node(adjacent_node) is True:
                        # If added, append the node and increment the node_index
                        node.adjacent_nodes.append(adjacent_node)
                        node_index += 1

                    print("=== DISPLAYING UPDATED TREE === ")
                    bfs_tree.display()

            # Iterate to the next layer to be done
            current_layer += 1

        # Iterate over the final bfs_tree looking for the target_vertex_id
        for current_layer in bfs_tree.nodes.keys():
            for node in bfs_tree.nodes[current_layer]:
                if node.vertex.vertex_id == target_vertex_id:
                    # Adjust indices within minimum_route to match initial representation
                    for vertex_id in node.minimum_route.vertex_order:
                        vertex_id += 1
                    # Return minimum route.
                    return node.minimum_route

    @staticmethod
    def depth_first_search(graph, source_vertex_id=1, target_vertex_id=11):
        dfs_stack = DepthFirstSearchStack()

        def search_deeper(current_vertex, current_route):
            # Get unfinished remaining adjacent vertices
            remaining_adjacent_vertices = dfs_stack.get_unfinished_adjacent_vertices(current_vertex.adjacent_vertices)
            # Update the route with the new vertex
            current_route.goto(current_vertex.vertex_id)
            # Push the current vertex ontop of the dfs stack
            dfs_stack.push(current_vertex, current_route)

            # If there are no remaining adjacent vertices
            if len(remaining_adjacent_vertices) == 0:
                # Pop the finished node off the stack
                finished_node = dfs_stack.pop()
                # walk back from the route since no longer part of it
                current_route.walk_back()
                # Mark the node complete. Update lists.
                dfs_stack.node_complete(finished_node)

                # If there are still items on the stack.
                if len(dfs_stack.node_stack) > 0:
                    # Search deeper using the previous item as guide.
                    search_deeper(dfs_stack.node_stack[-1].vertex, current_route)
            else:
                # Search the first adjacent vertex
                search_deeper(remaining_adjacent_vertices[0], current_route)

        source_vertex = graph.get_vertex_by_id(source_vertex_id)
        route = Route([], graph)
        search_deeper(source_vertex, route)
        return dfs_stack.get_path_to_finished_vertex_id(target_vertex_id)

    @staticmethod
    def brute_force_solution(graph, current_vertex_id=1, reduce_ram_usage=False):
        # Generate route log path
        if reduce_ram_usage:
            route_log_path =os.getcwd() + os.path.sep + ".." + os.path.sep + "logs" + os.path.sep + \
                            "RouteLog_{0}_{1}".format(len(graph.vertices), str(time.time())[:9])

        # Recursive function for trying all adjacent vertices.
        def try_all_open_routes_from_current_route(route, reduce_ram_usage=False):
            # Initialize Routes to keep track of all attempted routes.
            routes = np.array([])
            # Start at the current vertex id location
            current_vertex = route.graph.vertices[current_vertex_id]

            # For each adjacent vertex that has not been visited
            for adjacent_vertex in current_vertex.get_unvisited_adjacent_vertex_ids():
                # copy the route so far
                new_route = deepcopy(route)
                # goto the current adjacent_vertex
                new_route.goto(adjacent_vertex.vertex_id)

                # if all vertices have been visisted
                if new_route.graph.finished():
                    # goto the current vertex id
                    new_route.goto(current_vertex_id)

                    if reduce_ram_usage:
                        # Log finished route to hard disk
                        FileHandler.log_route(new_route, route_log_path)
                        # Delete from RAM
                        del new_route
                    else:
                        # append the route to the list of completed routes
                        routes = np.concatenate((routes, new_route), axis=None)
                else: # if not,
                    if reduce_ram_usage:
                        try_all_open_routes_from_current_route(new_route, reduce_ram_usage)
                    else:
                        # Recall the recursive function using the updated route.
                        routes = np.concatenate((routes, try_all_open_routes_from_current_route(new_route)), axis=None)

            # After all adjacent vertices have been visisted recursively, return the list of routes
            return routes

        # Initialize the route
        route = Route(list([]), graph)
        # goto the current vertex id
        route.goto(current_vertex_id)

        # Initialize a list of routes
        routes = np.array([])

        # Recursively try all open routes from the current route, advancing when possible.
        routes = np.concatenate((routes, try_all_open_routes_from_current_route(route, reduce_ram_usage=reduce_ram_usage)), axis=None)

        if reduce_ram_usage:
            del routes
            # Sift file located at route_log_path for the shortest route
            return FileHandler.find_minimum_route(route_log_path)
        else:
            # Identify the route with minimum distance traveled
            return min(routes)


if __name__ == "__main__":
    # Retrieve command line arguments
    if len(sys.argv) != 4:
        print("Command Line Arguments should follow the format:")
        print("python TrainingSalesman.py [algorithm] [relative path to vertex_graph_file]"
              " [relative path to adjacency_matrix_file]")
        print("\nImplemented algorithms include: brute_force, bfs, dfs")
    else:
        # retrieve solve_method
        algorithm = sys.argv[1]
        # retrieve relative path to vertex_graph_file
        vertex_graph_file_path = sys.argv[2]
        # retrieve relative path to adjacency_matrix_file_path
        adjacency_matrix_file_path = sys.argv[3]

        # Read the adjacency matrix
        adjacency_matrix = FileHandler.read_adjacency_matrix(os.getcwd() + os.path.sep + adjacency_matrix_file_path)

        # Read the vertices from the vertex graph file.
        vertices = FileHandler.read_graph(os.getcwd() + os.path.sep + vertex_graph_file_path, adjacency_matrix)

        if len(vertices) > 9 and algorithm == 'brute_force':
            reduce_ram_usage = True
        else:
            reduce_ram_usage = False

        # Build a graph representing the vertices and edges.
        graph = Graph(vertices)
        # Calculate edges
        graph.build_graph()

        # Display the graph before solving.
        print("\n=== Displaying Graph ===")
        print(graph)
        graph.plot()

        # Solve the graph using the solve_method provided
        print("\n=== Displaying Solution ===")
        if algorithm == 'brute_force':
            start = time.time()

            if reduce_ram_usage:
                FileHandler.enforce_path(os.getcwd() + os.path.sep + ".." + os.path.sep + "logs" + os.path.sep)
                result = TravelingSalesman.brute_force_solution(graph, reduce_ram_usage=reduce_ram_usage)
            else:
                result = TravelingSalesman.brute_force_solution(graph, reduce_ram_usage=reduce_ram_usage)

            end = time.time()

            print("brute_force_solution", str(result))
            print("Time elaspsed: {}".format(end-start))

            if reduce_ram_usage:
                graph.plot_route(result[0])
            else:
                result.plot()
        elif algorithm == "bfs" or algorithm == "BFS":
            start = time.time()

            result = TravelingSalesman.breadth_first_search(graph, 1, 11)

            end = time.time()
            print("breadth_first_search solution", str(result))
            print("Time elaspsed: {}".format(end-start))

            graph.plot_route(result.vertex_order)

        elif algorithm == "dfs" or algorithm == "DFS":
            start = time.time()

            result = TravelingSalesman.depth_first_search(graph, 1, 11)

            end = time.time()
            print("depth_first_search solution", str(result))
            print("Time elaspsed: {}".format(end-start))

            graph.plot_route(result.vertex_order)
        else:
            print("Invalid solve_method.  Current implemented solve methods include: brute_force")
