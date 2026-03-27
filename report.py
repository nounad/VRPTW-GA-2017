import ga_params
if ga_params.draw_plot:
    import matplotlib.pyplot as plt
if ga_params.export_spreadsheet:
    from openpyxl import Workbook
from datetime import datetime


class Reporter:
    
    #Stocke les génerations et résultats
    plot_x_axis = []
    plot_y_axis = []
    
    # workbook (classeur: fichier) et worksheet(feuille de calcul) Excel
    sheet_wb = None
    sheet_ws = None
    
    #Nom du fichier Excel
    sheet_dest = 'output'
    sheet_dest_ext = '.xlsm'

    def __init__(self, run_name: str):
        """self.fig, self.subplot, self.fig_node_connector, self.subplot2 et self.init_spreadsheet sont dans __init__ (attribut d'instance) parce que :
            * ils dépendent d’un paramètre (draw_plot ou export_spreadsheet)
            * ils sont créés dynamiquement
            * chaque instance doit avoir sa propre figure et son propre spreadsheet"""
        # Initialier le graphique
        if ga_params.draw_plot:
            plt.ion() # Mode interactif de matplotlib(mise à jour en temps réel des graphiques sans bloquer l'exécution de l'algorithme)
            # crée 2 figures
            self.fig, self.subplot = plt.subplots(figsize=(20, 10)) # Figure 1 → convergence + tableau 
            self.fig_node_connector, self.subplot2 = plt.subplots() # Figure 2 → carte des routes
            
        # Initialier le fichier Excel
        if ga_params.export_spreadsheet:
            self.init_spreadsheet(run_name=run_name)

    # fonction qui gènère les 2 figures (plot-output.png et plot2-output.png)
    def plot_draw(self, x_axis: list, y_axis: list, latest_result, total_time=None):
        # Extraire les valeurs float de chaque resultat
        y_values = []
        for y in y_axis:
            try:
                y_values.append(float(y['best'].value)) # Extrait la valeur du meilleur chromosome (best.value : la val min de la fn objective) de la generation et la convertit en float
            except:
                break # Si erreur (ex: valeur manquante), on sort de la boucle
        if not y_values:
            return
        
        # Formater le temps total
        if total_time:
            total_str = str(total_time).split('.')[0]  # enlever les microsecondes (Exemple: "0:15:23.456789" → "0:15:23" )
        else:
            total_str = 'N/A'
        
        # Figure 1 : configuration
        plt.figure(1) # Sélectionne la figure numéro 1 
        plt.clf() # Efface tout le contenu précédent
        plt.suptitle( # Super titre (titre principal de la figure)
            # dernière génération traitée | valeur du meilleur chromosome avec 1 décimale | nombre de véhicules utilisés par la meilleure solution |  temps total d'execution formaté
            f'Gen {x_axis[-1]} | Best: {latest_result.value:.1f} | Vehicles: {latest_result.vehicles_count} | Temps total: {total_str}',
            fontsize=11
        )

        # Courbe de convergence (partie haute de la figure)
        ax1 = plt.subplot(2, 1, 1) # Crée un sous-graphique avec 2 lignes, 1 colonne, et sélectionne le 1er (en haut)
        margin = (max(y_values) - min(y_values)) * 0.1 + 10
        ax1.set_ylim([min(y_values) - margin, max(y_values) + margin])
        ax1.set_xlabel('Generation')
        ax1.set_ylabel('Cost')
        ax1.plot(x_axis, y_values, color='steelblue') # trace la courbe

        # Tableau des trajets (partie basse de la figure)
        ax2 = plt.subplot(2, 1, 2) # Crée le 2ème sous-graphique (en bas)
        ax2.axis('off') # désactive les axes (pas besoin de coordonnées pour un tableau)

        table_data = []
        col_labels = ['Véhicule', 'Trajet', 'Nb clients'] # en-têtes des colonnes
        
        # Parcourt chaque tournée (route) de la meilleure solution
        for i, route in enumerate(latest_result.vehicles_routes):
            trajet = ' → '.join(str(n) for n in route) # Transforme [0, 3, 5, 2, 0] en "0 → 3 → 5 → 2 → 0"
            nb_clients = len(route) - 2 # Enlève le dépôt au début et à la fin
            table_data.append([f'V{i+1}', trajet, str(nb_clients)]) # Ajoute la ligne au tableau

        # Crée le tableau des routes dans ax2
        table = ax2.table(
            cellText=table_data, # Données du tableau
            colLabels=col_labels, # En-têtes des colonnes
            cellLoc='left', # Aligne le contenu à gauche
            loc='center' # Centre le tableau dans le graphique
        )
        table.auto_set_font_size(False) # Désactive le redimensionnement automatique de la police
        table.set_fontsize(8)
        table.auto_set_column_width([0, 1, 2]) # Ajuste automatiquement la largeur des colonnes 0, 1 et 2

        for j in range(3):
            table[0, j].set_facecolor('#4472C4') # Colore l'en-tête (ligne 0) en bleu (#4472C4)
            table[0, j].set_text_props(color='white', fontweight='bold') # Met le texte en blanc et en gras

        for i in range(1, len(table_data) + 1):
            color = '#DCE6F1' if i % 2 == 0 else 'white' # Colore les lignes alternées (zèbre : Lignes paires en bleu clair et Lignes impaires en blanc)
            for j in range(3):
                table[i, j].set_facecolor(color)

        plt.tight_layout() # Ajuste automatiquement les espacements pour éviter les chevauchements

        # Figure 2 : carte des routes
        plt.figure(2)
        plt.clf()
        # Parcourt chaque tournée
        # route_x : Liste des coordonnées X des points de la tournée (clients + depôt)
        # route_y : liste des coordonnées Y des points de la tournée (noeuds)
        for route_x, route_y in latest_result.plot_get_route_cords(): 
            plt.plot(route_x, route_y, marker='o', markersize=3) #  Trace la ligne reliant les points et marker='o' ajoute des cercles aux points
        plt.title(f'Routes | {latest_result.vehicles_count} vehicles') # Ajoute un titre avec le nombre de véhicules

        plt.tight_layout(pad=2.0) # Ajuste la mise en page avec un padding de 2 points
        plt.draw() # Force le rafraîchissement de l'affichage
        self.fig.savefig("plot-output.png")
        self.fig_node_connector.savefig("plot2-output.png")
        plt.pause(0.000001) # Fait une pause très courte (1 microseconde) pour permettre l'affichage (nécessaire en mode interactif)

    # Cree le fichier Excel nommé automatiquement avec la date 
    def init_spreadsheet(self, run_name: str):
        datetime_str = datetime.now().strftime('%b%d-%H:%M')
        self.sheet_dest = self.sheet_dest + '_' + run_name + '_' + datetime_str + self.sheet_dest_ext
        self.sheet_wb = Workbook()
        self.sheet_ws = self.sheet_wb.active
        self.sheet_ws.append(['gen_index', 'best', 'average', 'std', 'worst', 'created_time', 'computation_time',
                              'best_route'])

    # Ecrit et sauvegarde le fichier Excel
    def export_spreadsheet(self, x_axis: list, y_axis: list):
        datetime_str = str(datetime.now())
        for x, y in zip(x_axis, y_axis):
            self.sheet_ws.append([x, # numéro de génération
                                  y['best'].value, # valeur objective du meilleur
                                  y['average'], # moyenne de la population
                                  y['std'], # écart-type (diversité)
                                  y['worst'].value, # valeur objective du pire
                                  datetime_str, # horodatage
                                  str(y['process_time']), # temps de calcul
                                  str(y['best'].route)]) # route du meilleur chromosome
        self.sheet_wb.save(filename=self.sheet_dest)
