import heapq

class Pathfinder:
    @staticmethod
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def astar_search(start, goal, maze_size, is_valid_move_func):
        start = tuple(start)
        goal = tuple(goal)
        if start == goal: return []

        frontier = []
        heapq.heappush(frontier, (0, start))
        
        came_from = {start: None}
        cost_so_far = {start: 0}

        found = False
        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                found = True
                break

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_node = (current[0] + dx, current[1] + dy)
                
                if not (0 <= next_node[0] < maze_size and 0 <= next_node[1] < maze_size):
                    continue
                
                if not is_valid_move_func(current, next_node):
                    continue

                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + Pathfinder.heuristic(next_node, goal)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        if not found: return []

        path = []
        curr = goal
        while curr != start:
            path.append(list(curr))
            curr = came_from[curr]
        path.reverse()
        return path