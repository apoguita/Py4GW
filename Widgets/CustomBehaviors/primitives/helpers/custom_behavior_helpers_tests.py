import math
from typing import List, Tuple, Optional

def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcule la distance euclidienne entre deux points"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def count_players_in_radius(center: Tuple[float, float], 
                           other_players: List[Tuple[float, float]], 
                           radius: float) -> int:
    """Compte le nombre de players dans le rayon"""
    count = 0
    for player in other_players:
        if distance(center, player) <= radius:
            count += 1
    return count

def find_optimal_position_weighted(current_pos: Tuple[float, float],
                                 other_players: List[Tuple[float, float]], 
                                 radius: float,
                                 max_move_distance: Optional[float] = None,
                                 distance_weight: float = 0.1) -> Tuple[Tuple[float, float], int, float]:
    """
    Trouve la position optimale en tenant compte de la distance de déplacement
    
    Args:
        current_pos: Position actuelle du player
        other_players: Liste des autres players
        radius: Rayon de détection
        max_move_distance: Distance maximale de déplacement (None = illimité)
        distance_weight: Poids pour pénaliser les déplacements longs
    
    Returns:
        (position_optimale, nombre_players_couverts, distance_deplacement)
    """
    if not other_players:
        return (current_pos, 0, 0.0)
    
    best_position = current_pos
    best_score = count_players_in_radius(current_pos, other_players, radius)
    best_distance = 0.0
    best_count = best_score
    
    # Test de la position actuelle
    current_count = count_players_in_radius(current_pos, other_players, radius)
    
    # Candidats à tester
    candidates = []
    
    # 1. Positions centrées sur chaque player
    for player_pos in other_players:
        candidates.append(player_pos)
    
    # 2. Points sur les cercles autour de chaque player
    for player_pos in other_players:
        # Teste plusieurs points autour de chaque player
        for angle in range(0, 360, 30):  # Tous les 30 degrés
            rad = math.radians(angle)
            test_x = player_pos[0] + radius * math.cos(rad)
            test_y = player_pos[1] + radius * math.sin(rad)
            candidates.append((test_x, test_y))
    
    # 3. Intersections de cercles
    for i in range(len(other_players)):
        for j in range(i + 1, len(other_players)):
            intersections = circle_intersections(other_players[i], other_players[j], radius, radius)
            candidates.extend(intersections)
    
    # 4. Recherche locale autour de la position actuelle
    search_radius = radius * 2
    for angle in range(0, 360, 15):  # Tous les 15 degrés
        for dist in [radius * 0.5, radius, radius * 1.5]:
            rad = math.radians(angle)
            test_x = current_pos[0] + dist * math.cos(rad)
            test_y = current_pos[1] + dist * math.sin(rad)
            candidates.append((test_x, test_y))
    
    # Évaluer tous les candidats
    for candidate in candidates:
        move_distance = distance(current_pos, candidate)
        
        # Ignorer si trop loin
        if max_move_distance and move_distance > max_move_distance:
            continue
        
        # Compter les players couverts
        count = count_players_in_radius(candidate, other_players, radius)
        
        # Score combiné : couverture - pénalité distance
        score = count - distance_weight * move_distance
        
        # Garder le meilleur (priorité à la couverture, puis à la distance)
        is_better = (count > best_count or 
                    (count == best_count and move_distance < best_distance))
        
        if is_better:
            best_position = candidate
            best_count = count
            best_distance = move_distance
            best_score = score
    
    return best_position, best_count, best_distance

def circle_intersections(p1: Tuple[float, float], p2: Tuple[float, float], 
                        r1: float, r2: float) -> List[Tuple[float, float]]:
    """Trouve les points d'intersection de deux cercles"""
    x1, y1 = p1
    x2, y2 = p2
    
    d = distance(p1, p2)
    
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        return []
    
    if d == r1 + r2 or d == abs(r1 - r2):
        x = x1 + (r1 * (x2 - x1)) / d
        y = y1 + (r1 * (y2 - y1)) / d
        return [(x, y)]
    
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(r1**2 - a**2)
    
    px = x1 + a * (x2 - x1) / d
    py = y1 + a * (y2 - y1) / d
    
    x3 = px + h * (y2 - y1) / d
    y3 = py - h * (x2 - x1) / d
    
    x4 = px - h * (y2 - y1) / d
    y4 = py + h * (x2 - x1) / d
    
    return [(x3, y3), (x4, y4)]

def find_best_move_direction(current_pos: Tuple[float, float],
                           other_players: List[Tuple[float, float]], 
                           radius: float,
                           move_distance: float | None = None) -> Tuple[Tuple[float, float], int]:
    """
    Trouve la meilleure direction de déplacement depuis la position actuelle
    
    Args:
        current_pos: Position actuelle
        other_players: Liste des autres players
        radius: Rayon de détection
        move_distance: Distance fixe de déplacement (si None, trouve la distance optimale)
    
    Returns:
        (nouvelle_position, nombre_players_couverts)
    """
    if move_distance is None:
        return find_optimal_position_weighted(current_pos, other_players, radius)[:2]
    
    best_position = current_pos
    best_count = count_players_in_radius(current_pos, other_players, radius)
    
    # Teste toutes les directions
    for angle in range(0, 360, 5):  # Tous les 5 degrés
        rad = math.radians(angle)
        new_x = current_pos[0] + move_distance * math.cos(rad)
        new_y = current_pos[1] + move_distance * math.sin(rad)
        new_pos = (new_x, new_y)
        
        count = count_players_in_radius(new_pos, other_players, radius)
        
        if count > best_count:
            best_count = count
            best_position = new_pos
    
    return best_position, best_count