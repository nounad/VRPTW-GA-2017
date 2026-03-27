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
    vehicles_routes = None      # list, Liste des routes de tous les index des véhicules
    route_rounds = None         # int, Nombre de retours au dépôt
    total_travel_dist = None    # float, la somme de toutes les distances parcourues par tous les véhicules
    ##total_elapsed_time = None   # type: float
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
    def check_time_and_go(self, source: int, dest: int, distance: float=None) -> bool:
        
        #Recuperer la distance entre 2 noeuds
        if distance is None:
            distance = self.get_distance(source, dest)
        
        # Recuperer l'Objet customer de destination    
        dest_customer = self.get_node(dest)  # type: Node
        
        # Prédire le temps d'arrivé à la destination
        elapsed_new = self.get_travel_time(distance) + self.elapsed_time
        
        if elapsed_new <= dest_customer.due_time:
            
            #Prédire le temps de retour au depot à partir de la destination
            return_time = self.get_travel_time(self.get_distance(dest, 0))
            
            #Récuperer le due time du depôt
            deport_due_time = self.get_node(0).due_time
            
            #S'asurer qu'on peut revenir au depôt depuis la destination avant le due time
            if elapsed_new + dest_customer.service_time + return_time <= deport_due_time:
                self.move_vehicle(source, dest, distance=distance)
                return True
            else:
                return False
        else:
            return False
    
    #Vérifier si la demande du noeud destination accumulée à la charge courante depasse la capacité du véhicule 
    def check_capacity(self, dest: int) -> bool:
        # Recuperer l'Objet customer de destination
        dest_customer = self.get_node(dest)  # type: Node
        
        return self.current_load + dest_customer.demand <= ga_params.vehicle_capacity
    
    #Vérifie si le véhicule a assez d'autonomie pour aller de source à dest 
    def check_autonomy(self, source: int, dest: int, distance: float = None) -> bool:
        
        if distance is None:
            distance = self.get_distance(source, dest)   
        
        # Vérifie si la distance totale du trajet actuel + la nouvelle distance ne dépasse pas l'autonomie
        return self.current_distance + distance <= ga_params.vehicle_autonomy

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
            self.route_rounds += 1
            self.current_load = 0
            self.current_distance = 0
        else:
            dest_customer = self.get_node(dest)  # type: Node
            self.current_load += dest_customer.demand

    # Envoyer un nouveau vehicule
    def add_vehicle(self):
        self.vehicles_count += 1
        self.vehicles_routes.append([0])
        self.elapsed_time = 0
        self.current_load = 0
        self.current_distance = 0












    # Calculer la valeur de la fonction objective
    def get_cost_score(self) -> float:
        # demand ~ capacity
        # time ~ due_time
        self.initial_port()

        for source, dest in utils.pairwise([0] + self.route + [0]): # [source,dest]
            # Si le passage de la source à la destination ne depasse pas la capacité du véhicule
            if self.check_capacity(dest):
                # current vehicle has the capacity to go from source to dest
                if not self.check_time_and_go(source, dest):
                    # current vehicle hasn't enough time to go to dest -> new vehicle
                    # current vehicle should go back from source to deport
                    self.move_vehicle(source, 0)
                    # current_load = 0
                    # new vehicle starts from deport heading dest
                    self.add_vehicle()
                    self.move_vehicle(0, dest)
            else:
                # current vehicle hasn't the capacity to go to dest
                # current vehicle should go back from source to deport
                self.move_vehicle(source, 0)
                # head from deport to dest
                distance = self.get_distance(0, dest)  # just for speeding up (caching)
                if not self.check_time_and_go(0, dest, distance):
                    # too late to go from deport to dest on current vehicle -> new vehicle
                    self.add_vehicle()
                    self.move_vehicle(0, dest, distance)

        total_travel_cost = Chromosome.get_travel_cost(self.total_travel_dist)
        total_vehicles_and_deport_working_hours_cost = self.get_vehicle_count_preference_cost(
            vehicles_count=self.vehicles_count,
            deport_working_hours=self.max_elapsed_time)
        return total_travel_cost + total_vehicles_and_deport_working_hours_cost

    def plot_get_route_cords(self) -> list:
        rounds = []
        for vehicle_route in self.vehicles_routes:
            route_x_holder = []
            route_y_holder = []
            for customer_index in vehicle_route:
                customer = self.get_node(customer_index)    # type: Node
                route_x_holder.append(customer.x)
                route_y_holder.append(customer.y)
            rounds.append((route_x_holder, route_y_holder))
        return rounds

    def __iter__(self):
        for r in self.route:
            yield r

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value

    def __radd__(self, other):
        return self.value + other

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.route) + ", value= " + str(self.value) + ", vehicles_count= " + str(self.vehicles_count) \
               + ", total deport visits=" + str(self.route_rounds) \
               + ", deport working hours=" + str(self.max_elapsed_time) + ", routes= " + str(self.vehicles_routes)

    def __repr__(self):
        return self.__str__()
