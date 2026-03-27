from crossovers import crossover_uox, crossover_cx, crossover_pmx
from selections import selection_tournament_deterministic
from mutations import mutation_inversion, mutation_scramble

print_benchmarks = True
draw_plot = True
export_spreadsheet = True

MAX_GEN = 10000

vehicle_cost_per_dist = 1.0
vehicle_speed_avg = 1.0
vehicle_capacity = 200
vehicles_count_over_deport_hours_preference = 1000
vehicule_autonomy = 400

run_file = {
    'name': 'C101_200',
    'header_map': {
        'XCOORD': 'x_coordinates',
        'YCOORD': 'y_coordinates',
        'DEMAND': 'demand',
        'READY_TIME': 'ready_time',
        'DUE_DATE': 'due_time',
        'SERVICE_TIME': 'service_time',
    }
}

population = {
    'pop_size': 100,
    'crossover_method': staticmethod(crossover_pmx), # Pas de crossover_ratio. Tous les parents sélectionnés sont systématiquement croisés.
    'mutation_method': staticmethod(mutation_inversion),
    'removing_method': staticmethod(selection_tournament_deterministic), # Les deux utilisent le même algorithme de tournoi, mais avec des rôles opposés grâce au paramètre reverse
    'selection_method': staticmethod(selection_tournament_deterministic),
    'selection_pressure': 2,  # tournament size (k) : à chaque sélection on tire 2 chromosomes au hasard et le meilleur gagne (plus de diversité/convergence lente)
    'selection_repeat': False,
    'parent_selection_ratio': 0.8,
    'mutation_ratio': 0.1,
    'elitism_count': 5, # Les 5 meilleurs chromosomes de la génération courante sont copiés directement dans la génération suivante (meilleure sol° ne se perd jamais)
    # plot
    'plot_x_div': 100, # Contrôle la fréquence de mise à jour du graphique (Comme report est appelé tous les gen_index_div = 50 générations, la mise à jour réelle se fait tous les 50 × 100 = 5000 générations.)
    'plot_x_window': 100 # Jamais utilisé ( probablement prévu pour limiter la fenêtre d'affichage du graphique à 100 points)
}
