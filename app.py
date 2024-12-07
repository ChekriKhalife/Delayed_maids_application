import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import base64
import io

# Constants remain the same
TASK_THRESHOLDS = {
    'Apply for Work Permit - Stage 1': 168,
    'Pay MOHRE Insurance': 24,
    'Pay Work Permit Fees - Stage 2': 24,
    'Check Work Permit Approval - Stage 1': 48,
    'Check Work Permit Approval - Stage 2': 24,
    'Fix Work Permit Issues - Stage -1': 24,
    'Fix work permit issues - stage 2': 24,
    'Apply for entry Visa': 24,
    'Check Entry Visa Immigration Approval': 24,
    'Change of Status': 24,
    'Upload Change of status': 24,
    'Prepare EID application (Receival Automated)': 96,
    'Approve signed Offer Letter': 24,
    'Apply for R-visa': 24,
    'Upload The e-Residency': 24,
    'Check ID application type': 24,
    'Modify eid application': 240,
    'Prepare EID Application for Modification': 48,
    'Prepare medical application': 48,
    'Prepare folder containing E-visa medical application and EID': 72,
    'Receival of EID Card': 168
}

class DelayedMaidsAnalytics:
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.FLATLY,
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
            ],
            title="Delayed Cases Analytics"
        )
        self.df = pd.DataFrame()

    def process_data(self, df):
        """Process the uploaded data with proper handling of all fields."""
        try:
            df = df.copy()
            df.columns = df.columns.str.strip()
            
            required_columns = ['Housemaid ID', 'Current Stage']
            df = df.dropna(subset=required_columns)
            
            # Handle numeric fields
            df['RPA try count'] = pd.to_numeric(df['RPA try count'], errors='coerce').fillna(0).astype(int)
            df['Time in Stage'] = pd.to_numeric(df['Time in Stage'], errors='coerce').fillna(0)
            
            # Handle text fields
            text_fields = {
                'Client Note': 'STANDARD',
                'Error resolver page?': 'No',
                'Latest Note': '',
                'User': '',
                'Note Time': '',
                'Last RPA try time': '',
                'Nationality': 'Unknown',
                'Type': 'Unknown',
                'Portal Passport status': 'Unknown',
                'Photo Status': 'Unknown',
                'Docs status': 'Unknown'
            }
            
            for field, default in text_fields.items():
                if field in df.columns:
                    df[field] = df[field].astype(str).replace('nan', default).fillna(default)
            
            # Calculate delays and severity
            df['Threshold (in hours)'] = df['Current Stage'].map(TASK_THRESHOLDS).fillna(24)
            df['Delay (hours)'] = (df['Time in Stage'] - df['Threshold (in hours)']).fillna(0)
            
            df['Threshold Ratio'] = df['Time in Stage'] / df['Threshold (in hours)']
            df['Severity'] = pd.cut(
                df['Threshold Ratio'],
                bins=[0, 1.5, 2, 3, float('inf')],
                labels=['Low', 'Medium', 'High', 'Critical']
            ).fillna('Low')
            
            df['Priority Score'] = df.apply(self._calculate_priority, axis=1)
            df['Total Delay (hours)'] = df.groupby('Housemaid ID')['Delay (hours)'].transform('sum')
            
            return df
            
        except Exception as e:
            print(f"Error in data processing: {str(e)}")
            raise

    def _calculate_priority(self, row):
        """Calculate priority score with enhanced logic."""
        try:
            base_score = row['Threshold Ratio'] * 100
            
            multiplier = 1.0
            if row['Client Note'] == 'SUPER_ANGRY_CLIENT':
                multiplier = 2.5
            elif row['Client Note'] == 'PRIORITIZE_VISA':
                multiplier = 1.8
            elif row['Client Note'] == 'AMNESTY':
                multiplier = 1.5
            
            if str(row['Error resolver page?']).lower() == 'yes':
                multiplier *= 1.3
            
            if row['RPA try count'] > 3:
                multiplier *= 1.2
                
            return round(base_score * multiplier)
            
        except Exception:
            return 0

    def create_layout(self):
        """Create enhanced layout with improved design and filter controls."""
        self.app.layout = html.Div([
            # Enhanced Header with Gradient Background
            dbc.Navbar(
                dbc.Container([
                    html.Div([
                        html.I(className="fas fa-chart-line me-2"),
                        html.H2("Delayed Cases Analytics", className="text-white mb-0"),
                    ], className="d-flex align-items-center"),
                    html.Div([
                        dcc.Upload(
                            id='upload-data',
                            children=dbc.Button(
                                ["Upload Excel ", html.I(className="fas fa-upload ms-1")],
                                color="light",
                                className="me-2"
                            ),
                            multiple=False
                        ),
                        html.Span(id='last-update', className="text-white ms-2 small")
                    ], className="d-flex align-items-center")
                ]),
                color="primary",
                dark=True,
                className="mb-3 shadow-sm",
                style={'background': 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)'}
            ),

            dbc.Container([
                # Alert area
                html.Div(id='alerts-area', className="mb-3"),

                # Enhanced Filters Card
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5([
                                    html.I(className="fas fa-filter me-2"),
                                    "Filters"
                                ], className="card-title mb-3"),
                            ], width=12),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='stage-filter',
                                    placeholder="Filter by Stage",
                                    multi=True,
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='type-filter',
                                    placeholder="Filter by Type",
                                    multi=True,
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='nationality-filter',
                                    placeholder="Filter by Nationality",
                                    multi=True,
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='client-note-filter',
                                    options=[
                                        {'label': '🔥 Super Angry Clients', 'value': 'SUPER_ANGRY_CLIENT'},
                                        {'label': '⚡ Priority Visa', 'value': 'PRIORITIZE_VISA'},
                                        {'label': '📋 Amnesty', 'value': 'AMNESTY'},
                                        {'label': 'Standard', 'value': 'STANDARD'}
                                    ],
                                    placeholder="Filter by Client Priority",
                                    multi=True,
                                    className="mb-2"
                                )
                            ], md=3)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button(
                                        ["Apply Filters ", html.I(className="fas fa-check ms-1")],
                                        id="apply-filters-btn",
                                        color="primary",
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        ["Reset Filters ", html.I(className="fas fa-undo ms-1")],
                                        id="reset-filters-btn",
                                        color="secondary"
                                    )
                                ], className="mt-2")
                            ], className="d-flex justify-content-end")
                        ])
                    ])
                ], className="mb-4 shadow-sm"),

                # Enhanced Severity Legend with Icons
                dbc.Card([
                    dbc.CardBody([
                        html.H6([
                            html.I(className="fas fa-info-circle me-2"),
                            "Understanding Severity Levels"
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2 rounded", style={'width': '20px', 'height': '20px', 'backgroundColor': '#2196f3'}),
                                    html.Span(["Low: ", html.Small("Up to 50% over threshold", className="text-muted")])
                                ]),
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2 rounded", style={'width': '20px', 'height': '20px', 'backgroundColor': '#fdd835'}),
                                    html.Span(["Medium: ", html.Small("50-100% over threshold", className="text-muted")])
                                ])
                            ], md=6),
                            dbc.Col([
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2 rounded", style={'width': '20px', 'height': '20px', 'backgroundColor': '#f57c00'}),
                                    html.Span(["High: ", html.Small("100-200% over threshold", className="text-muted")])
                                ]),
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2 rounded", style={'width': '20px', 'height': '20px', 'backgroundColor': '#d32f2f'}),
                                    html.Span(["Critical: ", html.Small("Over 200% threshold", className="text-muted")])
                                ])
                            ], md=6)
                        ])
                    ])
                ], className="mb-4 shadow-sm"),

                # KPI Cards Row
                dbc.Row(id='kpi-cards', className="mb-4"),

                # Enhanced Charts Section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-chart-bar me-2"),
                                    "Client Priority Analysis"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='client-priority-chart'),
                                html.Hr(),
                                dcc.Graph(id='priority-stage-chart')
                            ])
                        ], className="shadow-sm")
                    ], width=12)
                ], className="mb-4"),

                # Enhanced Detailed Cases Table
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5([
                                    html.I(className="fas fa-table me-2"),
                                    "Detailed Cases Overview"
                                ])
                            ], md=3),
                            dbc.Col([
                                dbc.Input(
                                    id='table-search',
                                    type='text',
                                    placeholder='🔍 Search cases...',
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='table-sort-field',
                                    options=[
                                        {'label': 'Total Delay', 'value': 'Total Delay (hours)'},
                                        {'label': 'Current Delay', 'value': 'Delay (hours)'},
                                        {'label': 'Priority Score', 'value': 'Priority Score'},
                                        {'label': 'Time in Stage', 'value': 'Time in Stage'}
                                    ],
                                    value='Total Delay (hours)',
                                    placeholder="Sort by...",
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dbc.Select(
                                    id='records-per-page',
                                    options=[
                                        {'label': '10 records', 'value': 10},
                                        {'label': '25 records', 'value': 25},
                                        {'label': '50 records', 'value': 50},
                                        {'label': '100 records', 'value': 100}
                                    ],
                                    value=25,
                                    className="mb-2"
                                )
                            ], md=3)
                        ])
                    ]),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='detailed-table',
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            sort_by=[{'column_id': 'Time in Stage', 'direction': 'desc'}],
                            page_action="native",
                            page_current=0,
                            page_size=25,
                            style_table={'overflowX': 'auto'},
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold',
                                'textAlign': 'center',
                                'padding': '12px',
                                'border': '1px solid #dee2e6'
                            },
                            style_cell={
                                'textAlign': 'left',
                                'padding': '12px',
                                'fontSize': '14px',
                                'fontFamily': '"Segoe UI", system-ui, -apple-system'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'Client Note', 'filter_query': '{Client Note} = "SUPER_ANGRY_CLIENT"'},
                                    'backgroundColor': '#ffebee',
                                    'color': '#c62828',
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id': 'Client Note', 'filter_query': '{Client Note} = "PRIORITIZE_VISA"'},
                                    'backgroundColor': '#fff3e0',
                                    'color': '#ef6c00'
                                },
                                {
                                    'if': {'column_id': 'Client Note', 'filter_query': '{Client Note} = "AMNESTY"'},
                                    'backgroundColor': '#e8f5e9',
                                    'color': '#2e7d32'
                                },
                                {
                                    'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "Critical"'},
                                    'backgroundColor': '#ffebee',
                                    'color': '#c62828'
                                },
                                {
                                    'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "High"'},
                                    'backgroundColor': '#fff3e0',
                                    'color': '#ef6c00'
                                }
                            ],
                            export_format="csv",
                            export_headers="display",
                            merge_duplicate_headers=True
                        )
                    ])
                ], className="shadow-sm"),

                # Enhanced Footer
                html.Footer([
                    html.Hr(className="my-4"),
                    dbc.Row([
                        dbc.Col([
                            html.P([
                                "© 2024 Developed by Chekri Khalife @",
                                html.A("Maids.cc", href="https://maids.cc", className="text-primary"),
                                ". All rights reserved."
                            ], className="text-center text-muted mb-0"),
                            html.P([
                                html.I(className="fas fa-code me-2"),
                                "Built with Dash and ❤️"
                            ], className="text-center text-muted small mt-1")
                        ])
                    ])
                ], className="py-3")
            ])
        ])

    def setup_callbacks(self):
        """Set up enhanced callbacks with new filter functionality."""
        
        @self.app.callback(
            [Output('stage-filter', 'value'),
             Output('type-filter', 'value'),
             Output('nationality-filter', 'value'),
             Output('client-note-filter', 'value')],
            [Input('reset-filters-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def reset_filters(n_clicks):
            """Reset all filters to their default state."""
            return None, None, None, None

        @self.app.callback(
            [Output('kpi-cards', 'children'),
             Output('client-priority-chart', 'figure'),
             Output('priority-stage-chart', 'figure'),
             Output('detailed-table', 'data'),
             Output('detailed-table', 'columns'),
             Output('stage-filter', 'options'),
             Output('type-filter', 'options'),
             Output('nationality-filter', 'options'),
             Output('last-update', 'children'),
             Output('alerts-area', 'children')],
            [Input('upload-data', 'contents'),
             Input('apply-filters-btn', 'n_clicks'),
             State('stage-filter', 'value'),
             State('type-filter', 'value'),
             State('nationality-filter', 'value'),
             State('client-note-filter', 'value'),
             Input('table-search', 'value'),
             Input('table-sort-field', 'value'),
             Input('records-per-page', 'value')],
            [State('upload-data', 'filename')]
        )
        def update_dashboard(contents, n_clicks, stage_filter, type_filter, nationality_filter,
                           client_note_filter, search_value, sort_field,
                           records_per_page, filename):
            """Update dashboard with enhanced filtering and sorting."""
            # Initialize outputs
            empty_returns = [[], {}, {}, [], [], [], [], [], "", None]
            
            if contents is None:
                return empty_returns

            try:
                # Process uploaded file
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                
                if filename.endswith('.xlsx'):
                    self.df = pd.read_excel(io.BytesIO(decoded))
                elif filename.endswith('.csv'):
                    self.df = pd.read_csv(io.BytesIO(decoded))
                else:
                    raise ValueError("Unsupported file format. Please upload an Excel (.xlsx) or CSV file.")
                
                self.df = self.process_data(self.df)
            except Exception as e:
                return empty_returns[:-1] + [
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-circle me-2"),
                        f"Error processing file: {str(e)}"
                    ], color="danger", dismissable=True, className="d-flex align-items-center")
                ]

            # Apply filters
            filtered_df = self.df.copy()
            
            if stage_filter:
                filtered_df = filtered_df[filtered_df['Current Stage'].isin(stage_filter)]
            if type_filter:
                filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
            if nationality_filter:
                filtered_df = filtered_df[filtered_df['Nationality'].isin(nationality_filter)]
            if client_note_filter:
                filtered_df = filtered_df[filtered_df['Client Note'].isin(client_note_filter)]
                
            # Enhanced search functionality
            if search_value:
                search = search_value.lower()
                filtered_df = filtered_df[
                    filtered_df.astype(str).apply(lambda x: x.str.lower()).apply(
                        lambda x: x.str.contains(search, na=False)
                    ).any(axis=1)
                ]

            # Create visualizations
            kpi_cards = self.create_kpi_cards(filtered_df)
            client_priority_fig = self.create_client_priority_chart(filtered_df)
            priority_stage_fig = self.create_priority_stage_chart(filtered_df)

            # Enhanced sorting
            if sort_field:
                filtered_df = filtered_df.sort_values(sort_field, ascending=False)
            
            # Prepare table data with formatted values
            table_data = filtered_df.to_dict('records')
            columns = [{'name': i, 'id': i} for i in filtered_df.columns]

            # Create filter options with counts
            def create_options_with_counts(column):
                value_counts = self.df[column].value_counts()
                return [{'label': f"{x} ({value_counts[x]})", 'value': x} 
                       for x in sorted(self.df[column].unique())]

            stage_options = create_options_with_counts('Current Stage')
            type_options = create_options_with_counts('Type')
            nationality_options = create_options_with_counts('Nationality')

            # Update time with enhanced formatting
            update_time = html.Span([
                html.I(className="fas fa-clock me-1"),
                f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ])

            return (
                kpi_cards, client_priority_fig, priority_stage_fig,
                table_data, columns, stage_options, type_options, nationality_options,
                update_time, None
            )

    def add_custom_css(self):
        """Add enhanced custom CSS styles."""
        custom_css = """
            :root {
                --primary-color: #1976d2;
                --secondary-color: #2196f3;
                --background-color: #f8f9fa;
            }
            
            body {
                background-color: var(--background-color);
            }
            
            .sticky-top {
                top: 20px;
                z-index: 1000;
            }
            
            .card {
                border: none;
                border-radius: 12px;
                box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.1) !important;
                margin-bottom: 1.5rem !important;
                transition: all 0.2s ease-in-out;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 0.15rem 2.5rem 0 rgba(58, 59, 69, 0.15) !important;
            }
            
            .card-header {
                background-color: white;
                border-bottom: 1px solid rgba(0,0,0,.125);
                padding: 1.25rem;
                border-radius: 12px 12px 0 0 !important;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td,
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
                font-size: 14px;
                padding: 12px;
                border: 1px solid #dee2e6;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                font-weight: 600;
                background-color: #f8f9fa;
            }
            
            .dropdown-container .Select-control {
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            
            .dash-table-container {
                border-radius: 12px;
                overflow: hidden;
            }
            
            .dash-filter input {
                border-radius: 8px;
                border: 1px solid #dee2e6;
                padding: 8px 12px;
            }
            
            .btn {
                border-radius: 8px;
                padding: 8px 16px;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                border: none;
            }
            
            .btn-primary:hover {
                background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
            }
            
            .form-control {
                border-radius: 8px;
                padding: 8px 12px;
            }
            
            .navbar {
                border-radius: 0 0 12px 12px;
            }
        """
        self.app.index_string = self.app.index_string.replace(
            '</head>',
            f'<style>{custom_css}</style></head>'
        )

    def run_server(self, debug=True, port=8050, host='0.0.0.0'):
        """Run the Dash server with startup message."""
        self.create_layout()
        self.setup_callbacks()
        self.add_custom_css()
        print("""
        ╔════════════════════════════════════════════╗
        ║     Delayed Cases Analytics Dashboard      ║
        ╠════════════════════════════════════════════╣
        ║ Starting server at http://localhost:8050   ║
        ║ Press Ctrl+C to quit                       ║
        ╚════════════════════════════════════════════╝
        """)
        self.app.run_server(debug=debug, port=port, host=host)


if __name__ == '__main__':
    app = DelayedMaidsAnalytics()
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host='0.0.0.0', port=port)
