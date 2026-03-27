import numpy as np

# Complète les cases vides d’un chromosome avec les noeuds manquants tout en évitant les doublons
def fill_remaining(chromosome: list, filling: list) -> list:
    fill_index = 0
    for ch_index, ch_bit in enumerate(chromosome):
        if ch_bit is None:
            while filling[fill_index] in chromosome:
                fill_index += 1
            chromosome[ch_index] = filling[fill_index]

    return chromosome


def crossover_uox(parent1: list, parent2: list) -> (list, list):
    """
    Exemple :
    Nb clients : 6
    
    Parent1:     1   2   3   4   5   6
    Parent2:     6   5   4   3   2   1
    
    Mask:        0   1   1   0   1   0 
    ==> Si Mask[i] = 0 alors Child1_tmp[i] = None
        Si Mask[i] = 1 alors Child1_tmp[i] = Parant1[i]
        
    Child1_tmp:  _   2   3   _   5   _
    Child2_tmp:  _   5   4   _   2   _
    
    ==> Si Child1_tmp[i] = None alors Child1_tmp[i] = val manquante à partir du Parent2 dans l'ordre.

    Child1:      6   2   3   1   5   4
    Child2:      1   5   4   6   2   3
    """
    if len(parent1) != len(parent2):
        raise Exception("Crossover error: Parents length are not equal")
    chrome_len = len(parent1)
    mask_binary = np.random.randint(2, size=chrome_len)
    # mask_binary = [0, 1, 1, 0, 1, 1]
    child1 = []
    child2 = []

    for index, mask in enumerate(mask_binary):
        if mask:
            child1.append(parent1[index])
            child2.append(parent2[index])
        else:
            child1.append(None)
            child2.append(None)

    child1 = fill_remaining(child1, parent2)
    child2 = fill_remaining(child2, parent1)

    return child1, child2


def crossover_cx(parent1: list, parent2: list) -> (list, list):
    """
    Exemple :
    Nb clients : 10

    Parent1:     8   4   7   3   6   2   5   1   9   0
    Parent2:     0   1   2   3   4   5   6   7   8   9

    Étape 1 : Identification des cycles

    Cycle 1: i=0 → P1[0]=8 , P2[0]=0  => Chercher 8 dans P2 → i=8
             i=8 → P1[8]=9 , P2[8]=8  => Chercher 9 dans P2 → i=9
             i=9 → P1[9]=0 , P2[9]=9  => Chercher 0 dans P2 → i=0 (retour au début => cycle)
             0 → 8 → 9 → 0
    Cycle 2: 1 → 4 → 6 → 5 → 2 → 7 → 1
    Cycle 3: 3 → 3 (point fixe)

    Étape 2 : Construction des enfants (alternance des cycles)

    Cycle 1 (run=0) → nb pair → Child1 prend de Parent1 dans les index du cycle 1
    Cycle 2 (run=1) → nb impair → Child1 prend de Parent2 dans les index du cycle 2 
    Cycle 3 (run=2) → nb pair → Child1 prend de Parent1 dans les index du cycle 3

    Enfants finaux:

    Child1:      8   1   2   3   4   5   6   7   9   0
    Child2:      0   4   7   3   6   2   5   1   8   9
    """
    length = len(parent1)
    if length != len(parent2):
        raise Exception("Crossover error: Parents length are not equal")

    p1 = {}
    p2 = {}
    p1_inv = {}
    p2_inv = {}
    for i in range(length):
        p1[i] = parent1[i]
        p1_inv[p1[i]] = i
        p2[i] = parent2[i]
        p2_inv[p2[i]] = i

    cycles_indices = []
    while p1 != {}:
        i = min(list(p1.keys()))
        cycle = [i]
        start = p1[i]
        check = p2[i]
        del p1[i] # On supprime p1[i]
        del p2[i]

        while check != start:
            i = p1_inv[check]
            cycle.append(i)
            check = p2[i]
            del p1[i]
            del p2[i]

        cycles_indices.append(cycle)

    child = ({}, {})

    for run, indices in enumerate(cycles_indices):
        first = run % 2
        second = (first + 1) % 2

        for i in indices:
            child[first][i] = parent1[i]
            child[second][i] = parent2[i]

    child1 = []
    child2 = []
    for i in range(length):
        child1.append(child[0][i])
        child2.append(child[1][i])

    return child1, child2

    # child1, child2 = crossover_cx([8, 4, 7, 3, 6, 2, 5, 1, 9, 0], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    # print(child1)   # 8 1 2 3 4 5 6 7 9 0
    # print(child2)   # 0 4 7 3 6 2 5 1 8 9


def crossover_pmx(parent1: list, parent2: list) -> (list, list):
    """Exemple
        Nb clients : 10

        Parent1 :   8   4   7   3   6   2   5   1   9   0
        Parent2 :   0   1   2   3   4   5   6   7   8   9

        cut1 = 3
        cut2 = 7
        => positions 3 à 6.
        
        Étape 1 : Copier le segment
        Child1 :    _   _   _   3   4   5   6   _   _   _
        Child2 :    _   _   _   3   6   2   5   _   _   _

        Étape 2 : Construction du mapping bidiretionnel (On crée la correspondance entre les segments) :
            Parent1	  Parent2
                3   ↔    3
                6	↔    4
                2	↔    5
                5	↔    6

        Étape 3 : Remplissage avec résolution des conflits
        i=0
        Parent1[0] = 8  =>  Child1 :   8   _   _   3   4   5   6   _   _   _
        Parent2[0] = 0  =>  Child2 :   0   _   _   3   6   2   5   _   _   _

        i=1
        Parent1[1] = 4 => 4 est déjà dans le segment 
        Donc conflit → on applique le mapping.
        4 correspond à quoi ?
        Dans mapping : 6 ↔ 4 => On remplace 4 par 6 mais 6 est déjà dans Child1 
        On recommence :6 ↔ 5 => 5 est aussi dans Child1 
        On recommence :5 ↔ 2 => 2 n’est PAS dans Child1 
        Child1 : 8   2   _   3   4   5   6   _   _   _

        i=2
        Parent1[2] = 7  =>  Child1 : 8   2   7   3   4   5   6   _   _   _
    
        ...
        Child1 :  8   2   7   3   4   5   6   1   9   0

    """
    
    if len(parent1) != len(parent2):
        raise Exception("Crossover error: Parents length are not equal")

    size = len(parent1)

    # Choix des points
    cx_point1 = np.random.randint(0, size)
    cx_point2 = np.random.randint(0, size)

    if cx_point1 > cx_point2:
        cx_point1, cx_point2 = cx_point2, cx_point1

    # Initialisation enfants avec None
    child1 = [None] * size
    child2 = [None] * size

    # Copier le segment
    child1[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]
    child2[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]

    # Construire le mapping
    mapping1 = {}
    mapping2 = {}

    for i in range(cx_point1, cx_point2):
        mapping1[parent2[i]] = parent1[i]
        mapping2[parent1[i]] = parent2[i]

    # Remplissage avec résolution de conflits
    for i in range(size):

        if i >= cx_point1 and i < cx_point2:
            continue

        # --- Child1 ---
        value = parent1[i]
        while value in mapping1:
            value = mapping1[value]
        child1[i] = value

        # --- Child2 ---
        value = parent2[i]
        while value in mapping2:
            value = mapping2[value]
        child2[i] = value

    return child1, child2

    # p1, p2 = list(range(1, 101)), list(range(1, 101))
    #
    # # child1, child2 = crossover_pmx([8, 4, 7, 3, 6, 2, 5, 1, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9])
    # child1, child2 = crossover_pmx(p1, p2)
    # print(child1)
    # print(child2)
