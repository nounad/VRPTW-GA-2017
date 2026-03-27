import csv

# header_map: dictionnaire pour renommer les colonnes
def csv_read(case: str, delimiter=',', data_start_row: int=1, header_map: dict=None) -> list:
    collected_data = []

    with open('data/' + case + '.csv', 'r', newline='') as csv_file:
        
        """Lire tout le fichier dans une liste: 
                                                               [
            x,y,demand,ready_time,due_time,service_time         ['x','y','demand','ready_time','due_time','service_time'],
            0,0,0,0,230,0                                 =>    ['0','0','0','0','230','0'],
            10,15,5,20,100,10                                   ['10','15','5','20','100','10']
                                                               ]
        """
        spam_reader = csv.reader(csv_file, delimiter=delimiter, quotechar='|')
        rows_list = list(spam_reader)
        
        # Si on veut structurer les données
        if data_start_row > 0 and header_map is not None:
            header = rows_list[0] # On récupère la 1ère ligne (les noms de colonnes)
            # header = [header_map[head] if head in header_map else head for i, head in enumerate(header)]
            for head, mapped in header_map.items():  #Exemple :
                i = header.index(head)               # header_map =      
                header[i] = mapped                   #  {"x": "x_coordinates",    =>  "x" devient "x_coordinates"
                                                     #   "y": "y_coordinates" }       "y" devient "y_coordinates"
        else:                                        
            return rows_list
        
        """
        Transformer chaque ligne en dictionnaire
        Chaque ligne devient (Objet Customer):
        { "x_coordinates": "10", "y_coordinates": "15", "demand": "5", ...} """
        for row in rows_list[data_start_row:]:
            collected_data.append({header[i]: value for i, value in enumerate(row)})
    

    return collected_data # [{...,...}, {...,...}, ...]
