import sys
import os
import json
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, DataTable, TableColumn, NumberFormatter
from bokeh.layouts import column
from bokeh.palettes import Category10
from bokeh.io import output_file

def load_data(directories):
    data = {}
    for directory in directories:
        json_file = os.path.join(directory, 'response_length_vs_loop_density.json')
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data[os.path.basename(directory)] = json.load(f)
        else:
            data[os.path.basename(directory)] = []  # Empty list if JSON file doesn't exist
    return data

def create_scatter_plot(data):
    p = figure(title="Average Response Length vs Loop Density", x_axis_label='Average Response Length', y_axis_label='Loop Density',
               x_range=(0, 2000), y_range=(0, 1), width=1000, height=600)

    colors = Category10[10][:len(data)]
    
    for (folder, points), color in zip(data.items(), colors):
        source = ColumnDataSource(data=dict(
            x=[point[0] for point in points],
            y=[point[1] for point in points],
            folder=[folder] * len(points)
        ))
        
        p.circle('x', 'y', size=8, color=color, alpha=0.6, legend_label=folder, source=source)

    p.legend.click_policy = "hide"
    p.add_tools(HoverTool(tooltips=[
        ("Folder", "@folder"),
        ("Avg Response Length", "@x{0.2f}"),
        ("Loop Density", "@y{0.4f}")
    ]))

    return p

def create_summary_table(data):
    summary_data = []
    for folder, points in data.items():
        if points:  # Check if there are any points for this folder
            avg_response_length = sum(point[0] for point in points) / len(points)
            avg_loop_density = sum(point[1] for point in points) / len(points)
        else:
            avg_response_length = 0
            avg_loop_density = 0
        summary_data.append({'Result Set': folder, 'Avg Response Length': avg_response_length, 'Avg Loop Density': avg_loop_density})

    df = pd.DataFrame(summary_data)
    print("DataFrame contents:")
    print(df)  # Debugging print

    source = ColumnDataSource(df)

    columns = [
        TableColumn(field="Result Set", title="Result Set"),
        TableColumn(field="Avg Response Length", title="Avg Response Length", formatter=NumberFormatter(format="0.00")),
        TableColumn(field="Avg Loop Density", title="Avg Loop Density", formatter=NumberFormatter(format="0.0000"))
    ]

    data_table = DataTable(source=source, columns=columns, width=1000, height=280)
    return data_table

def main(directories):
    data = load_data(directories)
    print("Loaded data:")
    for folder, points in data.items():
        print(f"{folder}: {len(points)} points")
    
    scatter_plot = create_scatter_plot(data)
    summary_table = create_summary_table(data)

    output_file("results.html")
    show(column(scatter_plot, summary_table))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view.py <directory1> <directory2> ...")
        sys.exit(1)
    
    directories = [directory.rstrip('/') for directory in sys.argv[1:]]
    main(directories)
