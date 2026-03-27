from random import shuffle


def selection_tournament_deterministic(population: list, selection_size: int, k: int=2, repeat: bool=False, 
                                       reverse: bool=False) -> list:
    pop_copy = list(population)
    selected = []
    for selection_index in range(selection_size): # Selection_size est le nombre d’individus à sélectionner
        shuffle(pop_copy)
        tournament = pop_copy[:k] # Taille du tournoi (combien de candidats sont comparés à chaque tour)
        if reverse: # True si on cherche à minimiser la fitness, False pour maximiser
            selected_in_tournament = min(tournament)
        else:
            selected_in_tournament = max(tournament)
        if not repeat: # Autoriser ou non la répétition des individus sélectionnés
            pop_copy.remove(selected_in_tournament)
        selected.append(selected_in_tournament)

    return selected
