import ga_params
import utils
from nodes import Customer as Node
from typing import List

List_Node = List[Node]

""" Les véhicules ne roulent pas en parallèle.
    La simulation est sérieuse / séquentielle : on parcourt la route client par client et on “déploie” un véhicule seulement quand le précédent ne peut plus continuer (par capacité, autonomie ou fenêtre de temps).
 """
class Chromosome:
    route = []                  # liste des clients
    value = None                # float, Score de la solution (fonction objectif)

    vehicles_count = None       # int, Nombre de véhicules utilisés
    vehicles_routes = None      # list, Liste des routes de tous les index des clients des véhicules
    route_rounds = None         # int, Nombre de retours au dépôt
    total_travel_dist = None    # float, la somme de toutes les distances parcourues par tous les véhicules
    total_elapsed_time = None   # type: float
    # deport is 0
    current_load = None         # int
    current_distance = None     # float, Distance parcourue par le véhicule courant (ne doit pas depasser 400km)
    elapsed_time = None         # float, Temps écoulé sur le véhicule courant
    max_elapsed_time = None     # float, Temps max passé par un véhicule
    distance_table = None       # type: list

    higher_value_fitter = False

    #Initialisation de la route (solution candidate)
    def __init__(self, route: iter): # route doit être itérable (objet que l’on peut parcourir avec une boucle comme list, tuple, set ...)
        self.route = list(route) # Convertir la route en liste
        self.value = self.get_cost_score()

    # Initialise les variables avant de simuler la route
    def initial_port(self):
        self.vehicles_count = 1
        self.vehicles_routes = [[0]]
        self.route_rounds = 0
        self.total_travel_dist = 0
        self.total_elapsed_time = 0
        self.current_load = 0
        self.current_distance = 0
        self.elapsed_time = 0
        self.max_elapsed_time = 0

    #Retourne la distance entre 2 noeuds à partir des index
    @staticmethod
    def get_distance(source: int, dest: int) -> float:
        # must be overwritten
        pass

    #Retourne le Customer à partir de son index
    @staticmethod
    def get_node(index: int) -> Node:
        # must be overwritten
        pass

    #Retourne la durée d'un trajet
    @staticmethod
    def get_travel_time(distance: float) -> float:
        return distance / ga_params.vehicle_speed_avg

    # Retoune le cout de deplacement du vehicule (C_distance)
    @staticmethod
    def get_travel_cost(distance: float) -> float:
        return distance * ga_params.vehicle_cost_per_dist
    
    # Calcule le temps d'attente nécessaire avant de pouvoir servir le client.
    def calculate_waiting_time(self, dest: int, arrival_time: float) -> float:
        dest_customer = self.get_node(dest)
        
        if arrival_time < dest_customer.ready_time:
            return dest_customer.ready_time - arrival_time
        else:
            return 0

    # Vérifie si on peut arriver à la destination avant le due time et si c'est le cas si on peut revenir au depôt depuis la destination avant le due time du depôt
    def check_time_and_go(self, source: int, dest: int, distance: float = None) -> bool:
        """
        Vérifie si on peut :
        1. Arriver chez dest avant due_time (en tenant compte de ready_time)
        2. Revenir au dépôt depuis dest avant le due_time du dépôt
        Ne déplace PAS le véhicule — vérifie seulement la faisabilité.
        """
        if distance is None:
            distance = self.get_distance(source, dest)

        dest_customer = self.get_node(dest)

        # Temps d'arrivée prédit chez dest
        arrival_time = self.get_travel_time(distance) + self.elapsed_time

        # Début de service effectif (attendre si arrivée avant ready_time)
        service_start = max(arrival_time, dest_customer.ready_time)

        # Vérifier que le service commence avant due_time
        if service_start > dest_customer.due_time:
            return False

        # Vérifier que le retour au dépôt est possible après le service
        return_time = self.get_travel_time(self.get_distance(dest, 0))
        deport_due_time = self.get_node(0).due_time
        if service_start + dest_customer.service_time + return_time > deport_due_time:
            return False

        return True
    
    #Vérifier si la demande du noeud destination accumulée à la charge courante depasse la capacité du véhicule 
    def check_capacity(self, dest: int) -> bool:
        # Recuperer l'Objet customer de destination
        dest_customer = self.get_node(dest)  # type: Node
        
        return self.current_load + dest_customer.demand <= ga_params.vehicle_capacity
    
    #Vérifie si le véhicule a assez d'autonomie pour aller de source à dest 
    def check_autonomy(self, source: int, dest: int, distance: float = None) -> bool:
        
        if distance is None:
            distance = self.get_distance(source, dest)
            
        # Distance de retour au dépôt depuis la destination et garantit que le véhicule peut rentrer au dépôt à partir de la destination
        return_distance = self.get_distance(dest, 0)
    
        # Vérifier que aller chez dest ET revenir au dépôt est faisable
        return self.current_distance + distance + return_distance <= ga_params.vehicle_autonomy

    # Retourne le coût liée au nombre de véhicule + temps max du depot
    @staticmethod
    def get_vehicle_count_preference_cost(vehicles_count: int, deport_working_hours: int) -> float:
        # less_vehicles_preference * (vehicles_count) + less_deport_working_hours * (deport_working_hours)
        # vehicles_count_over_deport_hours_preference = less_vehicles_preference / less_deport_working_hours
        return ga_params.vehicles_count_over_deport_hours_preference * vehicles_count + deport_working_hours

    # Déplace le véhicule d'un noeud à l'autre (aprés fin de service)
    def move_vehicle(self, source: int, dest: int, distance: float=None):
        if distance is None:
            distance = self.get_distance(source, dest)
        self.total_travel_dist += distance
        self.current_distance += distance
        self.elapsed_time += self.get_travel_time(distance)
        self.max_elapsed_time = max(self.elapsed_time, self.max_elapsed_time)
        self.vehicles_routes[-1].append(dest)
        if dest == 0:
            # Retour au dépôt : réinitialiser charge et distance courante
            self.route_rounds += 1
            self.current_load = 0
            self.current_distance = 0
        else:
            dest_customer = self.get_node(dest)  # type: Node
            self.current_load += dest_customer.demand

    # Envoyer un nouveau vehicule
    def add_vehicle(self):
        """
        Envoie un nouveau véhicule depuis le dépôt.
        Réinitialise le temps, la charge et la distance courante.
        """
        self.vehicles_count += 1
        self.vehicles_routes.append([0])
        self.elapsed_time = 0
        self.current_load = 0
        self.current_distance = 0

    # Calculer la valeur de la fonction objective
    def get_cost_score(self) -> float:
        """
        Calcule la valeur de la fonction objective :
        f = α × distance_totale + β × nb_véhicules + temps_max_dépôt

        Pour chaque client dans la route :
        1. Vérifier capacité + autonomie (look-ahead dépôt) + fenêtre de temps
        2. Si tout OK → déplacer + attendre si nécessaire + service
        3. Sinon → retour dépôt + nouveau véhicule + recommencer depuis dépôt
        """
        self.initial_port()

        for source, dest in utils.pairwise([0] + self.route + [0]):

            # Retour final au dépôt : garanti car check_autonomy inclut dest→dépôt
            if dest == 0:
                self.move_vehicle(source, 0)
                continue

            distance = self.get_distance(source, dest)

            # Vérifier les 3 contraintes
            can_go = (self.check_capacity(dest)
                      and self.check_autonomy(source, dest, distance)
                      and self.check_time_and_go(source, dest, distance))

            if can_go:
                # Déplacer le véhicule vers dest
                self.move_vehicle(source, dest, distance)

                # Ajouter le temps d'attente si arrivée avant ready_time
                waiting_time = self.calculate_waiting_time(dest, self.elapsed_time)
                self.elapsed_time += waiting_time

                # Ajouter le temps de service
                dest_customer = self.get_node(dest)
                self.elapsed_time += dest_customer.service_time
                self.max_elapsed_time = max(self.elapsed_time, self.max_elapsed_time)

            else:
                # Contrainte violée → retour dépôt + nouveau véhicule
                self.move_vehicle(source, 0)
                self.add_vehicle()

                distance_depot = self.get_distance(0, dest)

                # Vérifier depuis le nouveau véhicule au dépôt
                can_go_from_depot = (self.check_capacity(dest)
                                     and self.check_autonomy(0, dest, distance_depot)
                                     and self.check_time_and_go(0, dest, distance_depot))

                if can_go_from_depot:
                    self.move_vehicle(0, dest, distance_depot)

                    # Ajouter le temps d'attente si arrivée avant ready_time
                    waiting_time = self.calculate_waiting_time(dest, self.elapsed_time)
                    self.elapsed_time += waiting_time

                    # Ajouter le temps de service
                    dest_customer = self.get_node(dest)
                    self.elapsed_time += dest_customer.service_time
                    self.max_elapsed_time = max(self.elapsed_time, self.max_elapsed_time)

                else:
                    # Cas extrême : client inatteignable même depuis le dépôt
                    # → forcer le déplacement pour ne pas bloquer la simulation
                    self.move_vehicle(0, dest, distance_depot)

        total_travel_cost = Chromosome.get_travel_cost(self.total_travel_dist)
        total_vehicles_and_deport_working_hours_cost = self.get_vehicle_count_preference_cost(
            vehicles_count=self.vehicles_count,
            deport_working_hours=self.max_elapsed_time)
        return total_travel_cost + total_vehicles_and_deport_working_hours_cost
    
    # Prépare les coordonnées (x, y) de chaque tournée pour l'affichage graphique dans "report.py"
    def plot_get_route_cords(self) -> list:
        ## Stockera les coordonnées des clients de chaque véhicule
        rounds = []
        for vehicle_route in self.vehicles_routes:  # Parcourt chaque tournée
            route_x_holder = [] # Coordonnées X de la tournée courante
            route_y_holder = [] # Coordonnées Y de la tournée courante
            for customer_index in vehicle_route: # Parcourt chaque client dans la tournée
                customer = self.get_node(customer_index)    # type = Node (Récupère l'objet client)
                route_x_holder.append(customer.x)
                route_y_holder.append(customer.y)
            rounds.append((route_x_holder, route_y_holder))  # Stocke (X, Y) pour ce véhicule
        return rounds  
        """ [ 
                ([x1, x2, x3, ...], [y1, y2, y3, ...]),   # véhicule 1 
                ([x1, x2, ...], [y1, y2, ...]),# véhicule 2  
                ...
            ]
        """

    # Permet de parcourir l’objet Chromosome comme une liste le rend iterable
    def __iter__(self):
        """ Retourne un itérateur sur self.route
        
            Exemple : 
            for client in chromosome:
            print(client)
        """
        for r in self.route:
            yield r

    # Comparer 2 chromosomes (on compare les fonctions objectives des chromosomes)
    def __lt__(self, other):
        return self.value < other.value # True si ce chromosome est meilleur (coût plus petit) et False sinon

    # Tester l’égalité entre 2 solutions (l'égalité des fns objectives)
    def __eq__(self, other):
        return self.value == other.value

    # Additionner la fonction objective avec int ou float (Appelée quand l'objet chromosome est à droite de + )
    def __radd__(self, other):
        """ Exemple :
            sum([chromosome1, chromosome2])
            ==> retourne la somme 0 + chromosome1 => other = 0 => (resultat) + chromosome2 
        """
        return self.value + other

    # Additionner la fonction objective avec int ou float (méthode appelée quand l'objet chromosome est à gauche de l’opérateur + )
    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    # Convertir le chromosome en float
    def __float__(self):
        return float(self.value) # convertir la valeur de la fonction objective en float

    def __str__(self):
        return str(self.route) + ", value= " + str(self.value) + ", vehicles_count= " + str(self.vehicles_count) \
               + ", total deport visits=" + str(self.route_rounds) \
               + ", deport working hours=" + str(self.max_elapsed_time) + ", routes= " + str(self.vehicles_routes)

    def __repr__(self):
        return self.__str__()
