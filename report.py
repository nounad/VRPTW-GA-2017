import ga_params
if ga_params.draw_plot:
    import matplotlib.pyplot as plt
if ga_params.export_spreadsheet:
    from openpyxl import Workbook
from datetime import datetime
import re


class Reporter:

    plot_x_axis = []
    plot_y_axis = []
    sheet_wb = None
    sheet_ws = None
    sheet_dest = 'output'
    sheet_dest_ext = '.xlsx'

    def __init__(self, run_name: str):
        if ga_params.draw_plot:
            plt.ion()
            self.fig, self.subplot = plt.subplots(figsize=(20, 10))
            self.fig_node_connector, self.subplot2 = plt.subplots()
        if ga_params.export_spreadsheet:
            self.init_spreadsheet(run_name=run_name)

    def plot_draw(self, x_axis: list, y_axis: list, latest_result, total_time=None):
        # Extraire les valeurs float
        y_values = []
        for y in y_axis:
            try:
                y_values.append(float(y['best'].value))
            except:
                break
        if not y_values:
            return
        
        # Formater le temps total
        if total_time:
            total_str = str(total_time).split('.')[0]  # enlever les microsecondes
        else:
            total_str = 'N/A'

        plt.figure(1)
        plt.clf()
        plt.suptitle(
            f'Gen {x_axis[-1]} | Best: {latest_result.value:.1f} | Vehicles: {latest_result.vehicles_count} | Temps total: {total_str}',
            fontsize=11
        )

        # Courbe de convergence (haut)
        ax1 = plt.subplot(2, 1, 1)
        margin = (max(y_values) - min(y_values)) * 0.1 + 10
        ax1.set_ylim([min(y_values) - margin, max(y_values) + margin])
        ax1.set_xlabel('Generation')
        ax1.set_ylabel('Cost')
        ax1.plot(x_axis, y_values, color='steelblue')

        # Tableau des trajets (bas)
        ax2 = plt.subplot(2, 1, 2)
        ax2.axis('off')

        table_data = []
        col_labels = ['Véhicule', 'Trajet', 'Nb clients']
        for i, route in enumerate(latest_result.vehicles_routes):
            trajet = ' → '.join(str(n) for n in route)
            nb_clients = len(route) - 2
            table_data.append([f'V{i+1}', trajet, str(nb_clients)])

        table = ax2.table(
            cellText=table_data,
            colLabels=col_labels,
            cellLoc='left',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.auto_set_column_width([0, 1, 2])

        for j in range(3):
            table[0, j].set_facecolor('#4472C4')
            table[0, j].set_text_props(color='white', fontweight='bold')

        for i in range(1, len(table_data) + 1):
            color = '#DCE6F1' if i % 2 == 0 else 'white'
            for j in range(3):
                table[i, j].set_facecolor(color)

        plt.tight_layout()

        # Figure 2 : carte des routes
        plt.figure(2)
        plt.clf()
        for route_x, route_y in latest_result.plot_get_route_cords():
            plt.plot(route_x, route_y, marker='o', markersize=3)
        plt.title(f'Routes | {latest_result.vehicles_count} vehicles')

        plt.tight_layout(pad=2.0) 
        plt.draw()
        self.fig.savefig("plot-output.png")
        self.fig_node_connector.savefig("plot2-output.png")
        plt.pause(0.000001)

    def init_spreadsheet(self, run_name: str):
        datetime_str = datetime.now().strftime('%b%d-%H:%M')
        self.sheet_dest = self.sheet_dest + '_' + run_name + '_' + datetime_str + self.sheet_dest_ext
        self.sheet_wb = Workbook()
        self.sheet_ws = self.sheet_wb.active
        self.sheet_ws.append(['gen_index', 'best', 'average', 'std', 'worst', 'created_time', 'computation_time',
                              'best_route'])

    def export_spreadsheet(self, x_axis: list, y_axis: list):
        datetime_str = str(datetime.now())
        for x, y in zip(x_axis, y_axis):
            self.sheet_ws.append([x, y['best'].value, y['average'], y['std'], y['worst'].value, datetime_str,
                                  str(y['process_time']), str(y['best'].route)])
        self.sheet_wb.save(filename=self.sheet_dest)