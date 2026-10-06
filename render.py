import pandas as pd
import argparse
import os
import webbrowser
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Categorical palette slots (validated for colorblind-safe adjacency)
COLOR_EEV = '#2a78d6'         # slot 1 blue
COLOR_ACTUAL_DSH = '#eb6834'  # slot 2 orange
COLOR_TARGET_DSH = '#1baf7a'  # slot 3 aqua
COLOR_SUBCOOL = '#eda100'     # slot 4 yellow
COLOR_COMPRESSOR = '#e87ba4'  # slot 5 magenta
COLOR_FAN = '#008300'         # slot 6 green
COLOR_SUCTION_SH = '#c4314b'  # slot 7 red

SURFACE = '#fcfcfb'
PAGE_PLANE = '#f9f9f7'
INK_PRIMARY = '#0b0b0b'
INK_MUTED = '#898781'
GRIDLINE = '#e1e0d9'


def visualize_over_time(file_list, output_path='visualization.html', open_browser=True):
    """
    Reads CSV files, concatenates them, calculates Actual DSH, Subcool
    and Suction Superheat temperatures, and writes an interactive HTML chart with hover tooltips.
    """
    dataframes = []

    # Required columns
    required_cols = [
        'Time',
        'Actual Superheat Steps',
        'T4 Condenser Out',
        'T8 Compressor Discharge',
        'TP2 High Pressure as Temperature',
        'Target Discharge Superheat',
        'Actual Compressor Speed',
        'Actual Fan Speed',
        'T1 Evap Out',
        'TP1 Low Pressure as Temperature'
    ]

    # 1. Read and validate files
    for file in file_list:
        if not os.path.isfile(file):
            print(f"Error: The file '{file}' was not found.")
            continue

        try:
            df = pd.read_csv(file)
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"Warning: Missing columns {missing_cols} in '{file}'. Skipping.")
                continue

            dataframes.append(df)
        except Exception as e:
            print(f"Error processing '{file}': {e}")

    # 2. Combine, process, and sort data
    if not dataframes:
        print("No valid data found to plot.")
        return

    # Combine all valid dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Convert Time column to datetime objects and sort chronologically
    combined_df['Time'] = pd.to_datetime(combined_df['Time'])
    combined_df.sort_values('Time', inplace=True)

    # Calculate Actual DSH and Subcool temperature (T4 - Thp)
    combined_df['Actual DSH'] = combined_df['T8 Compressor Discharge'] - combined_df['TP2 High Pressure as Temperature']
    combined_df['Subcool'] = combined_df['T4 Condenser Out'] - combined_df['TP2 High Pressure as Temperature']
    combined_df['Suction SH'] = combined_df['T1 Evap Out'] - combined_df['TP1 Low Pressure as Temperature']

    # 3. Plotting - four stacked panels sharing a time axis (no dual y-axes)
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        row_heights=[0.2, 0.4, 0.2, 0.2],
        vertical_spacing=0.05,
        subplot_titles=('EEV (Steps)', 'Temperature (°C)', 'Compressor & Fan Speed', 'Suction Superheat (T1-Tlp)')
    )

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Actual Superheat Steps'],
        name='EEV (Steps)', mode='lines',
        line=dict(color=COLOR_EEV, width=2),
        hovertemplate='%{y:.0f} steps<extra>EEV</extra>'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Actual DSH'],
        name='Actual DSH', mode='lines',
        line=dict(color=COLOR_ACTUAL_DSH, width=2),
        hovertemplate='%{y:.1f} °C<extra>Actual DSH</extra>'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Target Discharge Superheat'],
        name='Target DSH', mode='lines',
        line=dict(color=COLOR_TARGET_DSH, width=2, dash='dash'),
        hovertemplate='%{y:.1f} °C<extra>Target DSH</extra>'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Subcool'],
        name='Subcool (T4-Thp)', mode='lines',
        line=dict(color=COLOR_SUBCOOL, width=2),
        hovertemplate='%{y:.1f} °C<extra>Subcool (T4-Thp)</extra>'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Actual Compressor Speed'],
        name='Compressor Speed', mode='lines',
        line=dict(color=COLOR_COMPRESSOR, width=2),
        hovertemplate='%{y:.0f}<extra>Compressor Speed</extra>'
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Actual Fan Speed'],
        name='Fan Speed', mode='lines',
        line=dict(color=COLOR_FAN, width=2),
        hovertemplate='%{y:.0f}<extra>Fan Speed</extra>'
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=combined_df['Time'], y=combined_df['Suction SH'],
        name='Suction SH (T1-Tlp)', mode='lines',
        line=dict(color=COLOR_SUCTION_SH, width=2),
        hovertemplate='%{y:.1f} °C<extra>Suction SH (T1-Tlp)</extra>'
    ), row=4, col=1)

    fig.update_xaxes(
        showspikes=True, spikemode='across', spikesnap='cursor',
        spikethickness=1, spikedash='dot', spikecolor=INK_MUTED,
        showgrid=True, gridcolor=GRIDLINE, linecolor=GRIDLINE
    )
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False, linecolor=GRIDLINE)

    fig.update_yaxes(title_text='Steps', row=1, col=1)
    fig.update_yaxes(title_text='Temperature (°C)', row=2, col=1)
    fig.update_yaxes(title_text='Speed', row=3, col=1)
    fig.update_yaxes(title_text='Superheat (°C)', row=4, col=1)
    fig.update_xaxes(title_text='Time', row=4, col=1)

    fig.update_layout(
        hovermode='x unified',
        title='EEV, DSH, Subcool, Compressor/Fan Speed and Suction Superheat Over Time',
        plot_bgcolor=SURFACE,
        paper_bgcolor=PAGE_PLANE,
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', color=INK_PRIMARY),
        legend=dict(orientation='h', yanchor='bottom', y=1.06, xanchor='left', x=0),
        height=1300,
        margin=dict(t=110),
    )

    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"Saved interactive visualization to {output_path}")

    if open_browser:
        webbrowser.open('file://' + os.path.abspath(output_path))


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Visualize EEV, DSH, and Subcool over time from multiple CSV files.")
    parser.add_argument(
        "files",
        metavar="FILE",
        type=str,
        nargs="+",
        help="One or more CSV files to process"
    )
    parser.add_argument(
        "-o", "--output",
        default="visualization.html",
        help="Path to write the interactive HTML chart (default: visualization.html)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't automatically open the chart in a browser"
    )

    # Parse arguments from the command line
    args = parser.parse_args()

    # Run the visualization
    visualize_over_time(args.files, output_path=args.output, open_browser=not args.no_open)
