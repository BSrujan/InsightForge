import os
import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector

# Connect to MySQL and load table into DataFrame
def load_data_from_mysql():
    connection = mysql.connector.connect(
        host="localhost",       # change as needed
        user="root",            # your MySQL username
        password="your_mysql_password", # your MySQL password
        database="sru"  # your DB name
    )
    query = "SELECT * FROM prpo_vt"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

file = load_data_from_mysql()
columns = file.columns.tolist()


def plot_graph(x, y, date1, date2, date_field, graph_type ):
    df = load_data_from_mysql()
    column_data = df[date_field].astype(str).values

    date1 = np.where(column_data == date1)[-1]
    if len(date1) > 0:
        first_index = date1[-1]
        date1 = first_index
    else:
        print("Value not found")
    date2 = np.where(column_data == date2)[-1]
    if len(date2) > 0:
        first_index = date2[-1]
        date2 = first_index
    else:
        print("Value not found")
    filtered = df.loc[int(date1): int(date2)]
    plt.figure(figsize=(25, 15))
    plt.title(f'{y} vs {x}', fontsize=20)
    plt.xlabel(x, fontsize=16)
    plt.ylabel(y, fontsize=16)
    plt.xticks([])

    if graph_type == 'bar':
        plt.bar(filtered[x], filtered[y])
    elif graph_type == 'line':
        plt.plot(filtered[x], filtered[y], marker='o')
    elif graph_type == 'scatter':
        plt.scatter(filtered[x], filtered[y])
    else: plt.pie(filtered[y], labels=filtered[x], autopct='%1.1f%%')
    graph_path ="graph.png"
    plt.tight_layout()
    plt.savefig(graph_path)
    plt.close()

    original_path = "original_data.csv"
    df.to_csv(original_path, index=False)

    return f"{graph_type.capitalize()} graph generated successfully!", graph_path, df[[x, y]], original_path

def show_row_details(evt: gr.SelectData):
     
    if evt is None or evt.index is None:
        return "<div style='text-align:center;'>Please select a valid cell.</div>"
    
    row_idx = evt.index[0]
    if row_idx is None or not isinstance(row_idx, int):
        return "<div style='text-align:center;'>Invalid selection.</div>"

    try:
        df = load_data_from_mysql()
        row_data = df.iloc[row_idx]

        fields = [
            f"""
            <p style='margin-bottom: 24px;'>
                <span style='font-weight: bold; text-decoration: underline;'>{col}:</span><br>
                <span style='margin-left: 5px;'>{row_data[col]}</span>
            </p>
            """ 
            for col in df.columns
        ]

        # Split into 3 roughly equal parts
        third = len(fields) // 3
        col1 = fields[:third]
        col2 = fields[third:2*third]
        col3 = fields[2*third:]

        html = f"""
        <h4 style='text-align:center;'>📌 Row {row_idx} Details</h4>
        <div style='width: 100vw; padding: 20px; display: flex; justify-content: space-around; font-size: 18px; box-sizing: border-box;'>
            <div style='width: 32%;'>{''.join(col1)}</div>
            <div style='width: 32%;'>{''.join(col2)}</div>
            <div style='width: 32%;'>{''.join(col3)}</div>
        </div>
        """
        return html

    except Exception as e:
        return f"<div style='text-align:center;'>❌ Error: {e}</div>"

def update_date_dropdown(selected_column):
    df = load_data_from_mysql()
    if selected_column in df.columns:
        values = df[selected_column].dropna().astype(str).unique().tolist()

        values.sort()
        return gr.Dropdown(choices=values, interactive=True), gr.Dropdown(choices=values, interactive=True)
    return gr.Dropdown(choices=[], interactive=True), gr.Dropdown(choices=[], interactive=True)

with gr.Blocks() as demo:
    gr.Markdown("### 📊 Dynamic graph")

    with gr.Tab("📈 Generate Graph"):
        with gr.Row():
            with gr.Column():
                x_input = gr.Dropdown(choices=columns, label="X-axis", value=None)
                y_input = gr.Dropdown(choices=columns, label="Y-axis", value=None)

                date_field = gr.Dropdown(choices=columns, label="Date Field", value=None)
                graph_type_input = gr.Dropdown(choices=["line", "bar", "scatter", "pie"], label="Graph Type")

                date1_input = gr.Dropdown(choices=[], label="Start Date")
                date2_input = gr.Dropdown(choices=[], label="End Date")

                submit_btn = gr.Button("Generate")

            with gr.Column():
                result_text = gr.Textbox(label="Status", interactive=False)
                graph_output = gr.Image(label="Graph")

        with gr.Accordion("🔎 Filtered Table", open=False):
            table_output = gr.Dataframe(label="original Output")
            download_btn = gr.File(label="original CSV")

    with gr.Tab("🧾 Full CSV"):
        full_table = gr.Dataframe(value=file, label="CSV Data", interactive=True)
        row_detail_output = gr.HTML()

        full_table.select(fn=show_row_details, outputs=row_detail_output)

    # Update date1 and date2 dropdowns when a date field is selected
    date_field.change(
    fn=update_date_dropdown,
    inputs=[date_field],
    outputs=[date1_input, date2_input]
)


    # Click event to generate graph
    submit_btn.click(
        fn=plot_graph,
        inputs=[x_input, y_input, date1_input, date2_input, date_field, graph_type_input],
        outputs=[result_text, graph_output, table_output, download_btn]
    )

if __name__ == "__main__":
    demo.launch()
