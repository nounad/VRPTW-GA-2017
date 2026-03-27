import chromosome as chrome
from report import Reporter
import ga_params
import utils

from typing import List
from random import shuffle
from datetime import datetime
import numpy as np

"""
Technique d'injection de dépendances:
    * Crée une classe vide qui hérite de chrome.Chromosome
    * Permet de surcharger les méthodes statiques (get_distance, get_node) plus tard dans evolver.py
"""
class Chromosome(chrome.Chromosome):
    pass


List_Chromosome = List[Chromosome]

# Hérite de Reporter
class Population(Reporter):
    generation = [] # type: List_Chromosome
    gen_index = 0   # type: int
    pop_size = None    # type: int
    chromosome_width = None    # type: int
    chromosome_higher_value_fitter = None
    crossover_method = None
    mutation_method = None
    removing_method = None
    selection_method = None
    selection_pressure = None  # tournament size (k)
    selection_repeat = None
    parent_selection_ratio = None
    mutation_ratio = None
    genocide_ratio = 0
    
    # plot
    # Les attributs de Reporter (plot_x_axis et plot_y_axis) sont destinés à stocker les données pour l'export (Excel et graphiques)
    # Les attributs de Population (x_axis et y_axis) sont destinés à stocker temporairement les données avant export 
    x_axis = []
    y_axis = []
    
    gen_index_div = None    # type: int
    plot_x_div = None
    plot_x_window = None
    plot_fig = None
    plot_subplot = None
    chromosome_class = None

    def __init__(self, pop_size: int, chromosome_width: int, run_file_name: str,
                 crossover_method: staticmethod, mutation_method: staticmethod,
                 removing_method: staticmethod, selection_method: staticmethod,
                 selection_pressure: int, selection_repeat: bool,
                 parent_selection_ratio: float, mutation_ratio: float, elitism_count: int=0,
                 gen_index_div: int=50, plot_x_div: int=200, plot_x_window: int=400):
        self.pop_size = int(pop_size)
        self.chromosome_width = int(chromosome_width)
        self.chromosome_higher_value_fitter = Chromosome.higher_value_fitter
        self.crossover_method = crossover_method.__func__ # __func__ extrait la fonction réelle derrière staticmethod donc crossover_method devient la fonction crossover_pmx et non plus un staticmethod
        self.mutation_method = mutation_method.__func__
        self.removing_method = removing_method.__func__
        self.selection_method = selection_method.__func__
        self.selection_pressure = 2 if selection_pressure is None else int(selection_pressure)
        self.selection_repeat = bool(selection_repeat)
        self.parent_selection_ratio = float(parent_selection_ratio)
        self.mutation_ratio = float(mutation_ratio)
        self.elitism_count = elitism_count
        self.plot_x_div = int(plot_x_div)
        self.gen_index_div = int(gen_index_div)
        self.plot_x_window = int(plot_x_window)

        # Stockage des paramètres d'affichage
        self.total_start_time = datetime.now() # Initialiser le tmp d'execution
        self.generation = self.initial_generation() # Crée la population initiale aléatoire
        super(Population, self).__init__(run_name=run_file_name) # Initialise Reporter (graphiques, Excel)

    # Définir la géneration initiale
    def initial_generation(self, init_size: int=None) -> List_Chromosome:
        if not init_size: # init_size : nombre de chromosomes à créer (par défaut = pop_size)
            init_size = self.pop_size 
        generation_holder = []
        random_indices = list(range(1, self.chromosome_width)) # liste [1, 2, 3, ..., n-1] (tous les clients, sans le dépôt 0)
        for i in range(init_size):
            shuffle(random_indices) #  Mélange l'ordre des clients
            init_chromosome = Chromosome(random_indices)
            generation_holder.append(init_chromosome)
        return generation_holder # Retourne la population initiale
        """Exemple : 
            Population Initiale (size = 100)
            ┌─────────────────────────────────────────────────────────────┐
            │ Chromosome 1: [3,1,4,2,5]    value=15234.5  vehicles=3      │
            │ Chromosome 2: [2,5,1,4,3]    value=14892.3  vehicles=2      │
            │ Chromosome 3: [4,3,5,1,2]    value=15678.2  vehicles=3      │
            │ Chromosome 4: [1,3,2,5,4]    value=14923.1  vehicles=2      │
            │ ...                                                         │
            │ Chromosome 100: [5,2,4,1,3]  value=15123.7  vehicles=3      │
            └─────────────────────────────────────────────────────────────┘
        """

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> (Chromosome, Chromosome):
        # noinspection PyCallingNonCallable
        indices1, indices2 = self.crossover_method(list(parent1), list(parent2)) # Convertit les parents en listes d'indices et applique la méthode de croisement (ex: PMX)
        child1 = Chromosome(indices1)
        child2 = Chromosome(indices2)
        return child1, child2

    def mutation(self, chromosome: Chromosome) -> Chromosome:
        # noinspection PyCallingNonCallable
        muted_indices = self.mutation_method(list(chromosome))
        return Chromosome(muted_indices)

    # Retourne la liste de parents à sélectionner pour le croisement
    def parent_selection(self, generation: List_Chromosome) -> list:
        # Calcule le nombre de parents à sélectionner 
        parent_selection_size = int(len(generation) * self.parent_selection_ratio)
        # Retourne la liste des parents
        return self.selection_method(generation, parent_selection_size, k=self.selection_pressure,
                                     repeat=self.selection_repeat, reverse=(not self.chromosome_higher_value_fitter)) # si chromosome_higher_value_fitter=False (minimisation), alors reverse=True pour sélectionner les plus petits

    def mutation_index_selection(self, generation: List_Chromosome) -> list:
        # Calcule le nombre d'individus à muter
        mutation_selection_size = int(len(generation) * self.mutation_ratio) 
        # Crée une liste d'indices mélangés
        indices = list(range(len(generation))) 
        shuffle(indices)
        # Retourne les premiers indices (sélection aléatoire)
        return indices[:mutation_selection_size]

    # Application du croisement sur les parents sélectionnés
    def get_offsprings(self, generation: List_Chromosome) -> List_Chromosome:
        selected_parents = self.parent_selection(generation)
        offsprings_holder = []
        for parent1, parent2 in utils.couples(selected_parents):
            child1, child2 = self.crossover(parent1, parent2)
            offsprings_holder += [child1, child2]
        return offsprings_holder

    # Applique la mutation directement sur la liste "generation"
    def permute_generation(self, generation: List_Chromosome):
        mutation_indices = self.mutation_index_selection(generation)
        for index in mutation_indices:
            generation[index] = self.mutation(generation[index])

    # Supprime les chromosomes les moins performants de la population
    def remove_less_fitters(self, generation: List_Chromosome, removing_size: int):
        # noinspection PyCallingNonCallable
        selected_chromosomes = self.removing_method(generation, removing_size, k=self.selection_pressure,
                                                    repeat=False, # Chaque individu ne peut être sélectionné qu'une fois
                                                    reverse=self.chromosome_higher_value_fitter) # si reverse=True (minimisation) sélectionne les plus grands (pires) 
        for ch in selected_chromosomes:
            generation.remove(ch)

    # Retourne la liste des meilleurs individus (les plus petits)
    def elitism(self, generation: list) -> list:
        elites = []
        gen = list(generation)     # copy to make sure the generation itself doesn't change
        for i in range(self.elitism_count):
            best = min(gen)
            gen.remove(best)
            elites.append(best)
        return elites

    # Produit la génération suivante  
    def next_gen(self) -> List_Chromosome:
        # create new offsprings by crossover
        children = self.get_offsprings(self.generation)
        # new children added to the population
        new_gen = self.generation + children    # type: List_Chromosome
        # permutation (mutation) on the whole population
        self.permute_generation(new_gen)
        # Ajoute les meilleurs individus de la génération précédente
        new_gen += self.elitism(self.generation)
        # defined pop_size - current population size should be removed using reversed tournament selection
        deceasing_size = max(len(new_gen) - self.pop_size, 0)
        # Supprime les moins bons pour revenir à pop_size
        self.remove_less_fitters(new_gen, deceasing_size)
        return new_gen

    # Exécution de l'algorithme génétique
    def evolve(self) -> Chromosome:
        process_timer_start = datetime.now()
        while self.gen_index < ga_params.MAX_GEN:
            # Vérification du moment de générer un rapport
            if self.gen_index % self.gen_index_div == 0: # self.gen_index_div : fréquence des rapports (ex: 50)
                # Calcul du temps écoulé
                process_time = datetime.now() - process_timer_start
                process_timer_start = datetime.now() # Réinitialise le chronomètre pour la prochaine période
                if ga_params.print_benchmarks:
                    # Affiche le temps nécessaire pour générer les gen_index_div générations
                    print('### Process time of ' + str(self.gen_index_div) + ' generation: '
                          + str(process_time))
                self.report(process_time)
                # Vérifie que le génocide est activé et que tous les chromosomes de la population sont identiques 
                if self.genocide_ratio > 0 and min(self.generation).value == max(self.generation).value:
                    self.generation = self.genocide(self.generation) # Remplace un pourcentage de la population par des individus aléatoires pour la rediversifier
            # Création de la génération suivante        
            self.generation = self.next_gen()
            self.gen_index += 1
        # Une fois la boucle terminée, retourne le meilleur chromosome 
        return min(self.generation)

    # Génère un rapport à intervalles réguliers (surcharge la méthode de la classe mère Raporter)
    def report(self, process_time=None):
        # Ajout des données de la génération courante
        self.x_axis.append(self.gen_index) # Liste qui stocke les numéros de génération courante
        # Ajout de dictionnaire contenant les statistiques de la génération
        self.y_axis.append({ 
            'best': min(self.generation),
            'worst': max(self.generation),
            'average': sum(self.generation) / len(self.generation),
            'std': np.std(self.generation), # écart-type (mesure de diversité de la population)
            'process_time': process_time
        })
        # Définir la fréquence d'export
        if self.gen_index % self.plot_x_div == 0:
            total_time = datetime.now() - self.total_start_time #Calculer le temps d'execution totale
            # Affichage des resultats
            if ga_params.draw_plot:
                self.plot_draw(x_axis=self.x_axis, y_axis=self.y_axis, latest_result=min(self.generation), total_time=total_time)
            if ga_params.export_spreadsheet:
                self.export_spreadsheet(x_axis=self.x_axis, y_axis=self.y_axis)
            
            # Vide les listes après l'export
            self.x_axis = []
            self.y_axis = []

    # Intervient quand la population est trop homogène en remplaceant une partie de la population par de nouveaux chromosomes aléatoires
    def genocide(self, generation: List_Chromosome):
        # Calcul du nombre de nouveaux individus à inserer
        new_gen_size = int(len(generation) * self.genocide_ratio)
        # Calcul du nombre de survivants
        surviving_selection_size = len(generation) - new_gen_size
        # Sélection des survivants
        survivors = self.selection_method(generation, surviving_selection_size, k=self.selection_pressure,
                                          repeat=self.selection_repeat, # autoriser ou non la répétition
                                          reverse=(not self.chromosome_higher_value_fitter)) # orientation de la sélection pour selectionner les meilleurs
        # Création de nouveaux individus aléatoires
        new_gen = self.initial_generation(new_gen_size)
        # Mélange de qualité (survivants) et de diversité (nouveaux)
        return survivors + new_gen

    def __str__(self):
        pop_str = "Generation:" + str(self.gen_index) + '\n'
        for i, chromosome in enumerate(self.generation):
            pop_str += str(i + 1) + ': ' + str(chromosome) + '\n'
        return pop_str

    def __repr__(self):
        return self.__str__()