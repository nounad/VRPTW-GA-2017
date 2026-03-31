from random import randint, shuffle

def mutation_slice_points(chromosome_len: int) -> (int, int):
    slice_point_1 = randint(0, chromosome_len - 3)
    slice_point_2 = randint(slice_point_1 + 2, chromosome_len - 1)
    return slice_point_1, slice_point_2


def mutation_inversion(chromosome: list) -> list:
    """Exemple :
       
       Chromosome initiale : [1, 2, 3, 4, 5, 6, 7, 8]
       
       cut_1 = 2
       cut_2 = 6
       Segment concerné : [3, 4, 5, 6]
       
       Après inversion: [6, 5, 4, 3] (l'ordre est inversé)
       
       Nouveau chromosome : [1, 2, 6, 5, 4, 3, 7, 8]
       
    """
    slice_point_1, slice_point_2 = mutation_slice_points(len(chromosome))

    return chromosome[:slice_point_1] + list(reversed(chromosome[slice_point_1:slice_point_2])) + chromosome[slice_point_2:]


def mutation_scramble(chromosome: list) -> list:
    """Exemple :
       
       Chromosome initiale : [1, 2, 3, 4, 5, 6, 7, 8]
       
       cut_1 = 2
       cut_2 = 6
       Segment concerné : [3, 4, 5, 6]
       
       Après inversion: [5, 3, 6, 4] (mélange aléatoire)
       
       Nouveau chromosome : [1, 2, 5, 3, 6, 4, 7, 8]
       
    """
    slice_point_1, slice_point_2 = mutation_slice_points(len(chromosome))
    scrambled = chromosome[slice_point_1:slice_point_2]
    shuffle(scrambled)

    return chromosome[:slice_point_1] + scrambled + chromosome[slice_point_2:]


def mutation_insertion(chromosome: list) -> list:
    """
    Déplace un client vers une autre position
    Chromosome initiale : [1, 2, 3, 4, 5]
    
    i = 2 (client 3)
    j = 4 (position du client 5)
    
    Enlever le client 3 : [1, 2, 4, 5]
    Insérer le client 3 à la position 4 : [1, 2, 4, 5, 3]
    """
    size = len(chromosome)

    i = randint(0, size - 1)
    j = randint(0, size - 1)

    while j == i:
        j = randint(0, size - 1)

    ch = chromosome.copy()
    node = ch.pop(i)
    ch.insert(j, node)

    return ch


