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
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from dataclasses import dataclass
from typing import Dict, Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import traceback
# Constants remain the same
class ThresholdManager:
    def __init__(self):
        self.default_threshold = 24  # Default threshold in hours
        self.thresholds = {
            'Prepare EID application': 24,
            'Waiting for the maid to go to medical test and EID fingerprinting': 24,
            'Check tasheel contract approval': 24,
            'Insert Labour Card Expiry Date': 24,
            'Pending medical certificate approval from DHA': 24,
            'Receive of Health Insurance Card': 24,
            'Receival of EID Card': 24,
            'MissingDocuments': 24,
            'Pause e-visa application': 24,
            'Submit Nawakes in Tasheel': 24,
            'Check Work Permit Ministry Approval': 24,
            'E-visa Issue solved': 24,
            'Fix the problem of entry visa': 24,
            'Awaiting to receive flight ticket schedule': 24,
            'Fix work permit issues': 24,
            'Apply for R-visa': 24,
            'Pay Challenge overstay fines application fees': 24,
            'Modify EID Application': 24,
            'Refund Entry Visa Application': 24,
            'Check Entry Visa Immigration Approval': 24,
            'Waiting for reply of Ansari': 24,
            'Pending to cancel active visa': 24,
            'Pending to fix MOHRE issue': 24,
            'Prepare medical application': 24,
            'Pending maid to go for EID Biometrics': 24,
            'Prepare insurance application': 24,
            'Upload Contract to Tasheel': 24,
            'Pending offer letter to be signed': 24,
            'prepare_eid_application_for_modification': 24,
            'Apply for Ansari': 24,
            'ChangeofStatus': 24,
            'Get Form from GDRFA': 24,
            'Pending to remove absconding': 24,
            'Create Regular Offer Letter': 24,
            'Modify Offer Letter': 24,
            'Prepare folder containing E-visa medical application and EID': 24,
            'Check Labour Card Approval': 24,
            'Repeat Medical': 24,
            'Waiting for the PRO Update': 24,
            'Waiting for Personal Photo': 24,
            'Check ID application type': 24,
            'Getting the Confirmation to Proceed with Change of Status': 24,
            'Apply for entry Visa': 24,
            'Upload Change of status': 24,
            'Approve signed Offer Letter': 24,
            'Upload tasheel contract to ERP': 24
        }
    
    def get_threshold(self, stage):
        """Get threshold for a specific stage"""
        return self.thresholds.get(stage, self.default_threshold)
    
    def set_threshold(self, stage, hours):
        """Set threshold for a specific stage"""
        try:
            hours = float(hours)
            if hours <= 0:
                raise ValueError("Threshold must be positive")
            self.thresholds[stage] = hours
            return True
        except (ValueError, TypeError):
            return False
    
    def get_all_thresholds(self):
        """Get all thresholds as a list of dicts for the data table"""
        return [
            {'stage': stage, 'threshold': threshold}
            for stage, threshold in self.thresholds.items()
        ]
    
    def bulk_update_thresholds(self, new_thresholds):
        """Update multiple thresholds at once"""
        try:
            for stage, threshold in new_thresholds.items():
                if not self.set_threshold(stage, threshold):
                    return False
            return True
        except Exception:
            return False


@dataclass
class User:
    name: str
    google_sheet_id: str
    active: bool = True
    workload: int = 0

@dataclass
class User:
    name: str
    google_sheet_id: str
    active: bool = True
    workload: int = 0  # Track how many tasks assigned

class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {
            "razan.hassan": User(
                name="Razan Hassan",
                google_sheet_id="14dpPJUFwMXTFemq8b2as3Jpwj_Qs-kplradlM63lS_U"
            ),
            "aya.tahawi": User(
                name="Aya Tahawi",
                google_sheet_id="1hkB77aTFTalcZtUG9xfNKH3b7nIgYAZP1-AF6Ob7szE"
            ),
            "maya.dayoub": User(
                name="Maya Dayoub",
                google_sheet_id="1fDaIXfSGEKlUTlVprS7_SjG1wbhaGk1kVLvZXTia6QU"
            ),
            "laila.alhafi": User(
                name="Laila Alhafi",
                google_sheet_id="1nCzh8FMZOGa2x7v_OLIUtVEtAc4hzUG3f-rIgHJgEF8"
            ),
            "ehab.joud": User(
                name="Ehab Joud",
                google_sheet_id="1WccFTrR-Izh4qpRSnDD9A_nq8MWm0l54fqFJu4eJPYY"
            ),
            "hala.khaddour": User(
                name="Hala Khaddour",
                google_sheet_id="1_zM3sANFMHXvjSFvIHCtG2sKiS7GBWk8haUCoYBm1XU"
            ),
            "marah.ghanem": User(
                name="Marah Ghanem",
                google_sheet_id="1z88anA3_FKx6xo3fc4bci22-J8naoiEYdbcK8eiN8CM"
            )
        }
        self.setup_google_sheets()
    
    
    def validate_sheet_access(self, sheet_id):
        """Validate that we can access and modify the sheet"""
        try:
            sheet = self.client.open_by_key(sheet_id).sheet1
            # Try to write something to verify we have write access
            sheet.update_cell(1, 1, "test")
            sheet.clear()  # Clear the test
            return True
        except Exception as e:
            print(f"Sheet validation error: {str(e)}")
            return False

    def extract_sheet_id(self, sheet_url: str) -> str:
        """Extract Google Sheet ID from URL."""
        try:
            if not sheet_url:
                raise ValueError("No URL provided")
                
            # Handle different URL formats
            if '/spreadsheets/d/' in sheet_url:
                sheet_id = sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            elif 'key=' in sheet_url:
                sheet_id = sheet_url.split('key=')[1].split('&')[0]
            elif len(sheet_url.strip()) == 44:  # Direct sheet ID
                sheet_id = sheet_url.strip()
            else:
                raise ValueError("Invalid Google Sheet URL format")
                
            # Validate ID format (basic check)
            if not sheet_id or len(sheet_id) != 44:
                raise ValueError("Invalid sheet ID format")
                
            return sheet_id
        except Exception as e:
            print(f"Error extracting sheet ID: {str(e)}")
            raise ValueError(f"Could not extract sheet ID: {str(e)}")
        
    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # Add your credentials file path
        # Load credentials from environment variable
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            raise ValueError("Environment variable GOOGLE_SERVICE_ACCOUNT_JSON is missing")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(service_account_json), scope
        )
        self.client = gspread.authorize(creds)


    def add_user(self, username: str, name: str, sheet_id: str) -> bool:
        """Add a new user"""
        try:
            # First validate sheet access
            if not self.validate_sheet_access(sheet_id):
                raise Exception("Cannot access or modify sheet. Please check sharing settings.")
                
            self.users[username] = User(name=name, google_sheet_id=sheet_id)
            self._save_user_config()
            return True
        except Exception as e:
            print(f"Error adding user: {str(e)}")
            return False

    def update_user(self, username: str, name: str = None, sheet_id: str = None) -> bool:
        """Update user details"""
        if username not in self.users:
            return False
        
        try:
            if sheet_id:
                self.client.open_by_key(sheet_id)
                self.users[username].google_sheet_id = sheet_id
            if name:
                self.users[username].name = name
            self._save_user_config()
            return True
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return False

    def delete_user(self, username: str) -> bool:
        """Delete a user completely from the system"""
        try:
            if username in self.users:
                del self.users[username]
                self._save_user_config()
                return True
            return False
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return False
    def distribute_data(self, usernames: list, data: pd.DataFrame) -> dict:
        """
        Distribute data evenly among users with enhanced error handling and debugging
        
        Returns:
            dict: Detailed results for each user including success/failure status and debugging info
        """
        results = {}
        debug_info = {}
        
        try:
            # Input validation with detailed error messages
            if not usernames:
                return {
                    "error": "No users selected",
                    "debug": "The usernames list is empty"
                }
            
            if data.empty:
                return {
                    "error": "No data to distribute",
                    "debug": "The input DataFrame is empty"
                }
                
            # Reset workload counters
            for user in self.users.values():
                user.workload = 0

            # Calculate distribution metrics
            total_records = len(data)
            base_records_per_user = total_records // len(usernames)
            extra_records = total_records % len(usernames)
            
            debug_info["distribution_plan"] = {
                "total_records": total_records,
                "base_records_per_user": base_records_per_user,
                "extra_records": extra_records,
                "users_count": len(usernames)
            }

            start_idx = 0
            for username in usernames:
                user_debug = {
                    "username": username,
                    "steps": []
                }
                
                # Validate user existence
                if username not in self.users:
                    results[username] = {
                        "status": "error",
                        "message": "User not found in system",
                        "debug": f"Username '{username}' not found in self.users dictionary"
                    }
                    continue

                # Calculate records for this user
                records_for_user = base_records_per_user
                if extra_records > 0:
                    records_for_user += 1
                    extra_records -= 1

                end_idx = start_idx + records_for_user
                user_data = data.iloc[start_idx:end_idx]
                start_idx = end_idx
                
                user_debug["steps"].append({
                    "step": "data_slice",
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "records_assigned": len(user_data)
                })

                # Update the user's Google Sheet
                try:
                    # Access sheet
                    sheet = self.client.open_by_key(self.users[username].google_sheet_id).sheet1
                    user_debug["steps"].append({
                        "step": "sheet_access",
                        "sheet_id": self.users[username].google_sheet_id,
                        "status": "success"
                    })
                    
                    # Clear sheet
                    sheet.clear()
                    user_debug["steps"].append({
                        "step": "sheet_clear",
                        "status": "success"
                    })
                    
                    if not user_data.empty:
                        # Update headers
                        headers = user_data.columns.tolist()
                        sheet.update('A1', [headers])
                        user_debug["steps"].append({
                            "step": "headers_update",
                            "headers_count": len(headers),
                            "status": "success"
                        })
                        
                        # Update data
                        values = user_data.values.tolist()
                        if values:
                            sheet.update('A2', values)
                            user_debug["steps"].append({
                                "step": "data_update",
                                "rows_updated": len(values),
                                "status": "success"
                            })
                        
                        # Update workload counter
                        self.users[username].workload = len(values)
                        
                        results[username] = {
                            "status": "success",
                            "message": f"Successfully assigned {len(values)} tasks",
                            "debug": user_debug
                        }
                    else:
                        results[username] = {
                            "status": "warning",
                            "message": "No tasks assigned",
                            "debug": user_debug
                        }

                except Exception as e:
                    error_details = str(e)
                    user_debug["steps"].append({
                        "step": "error",
                        "error_message": error_details,
                        "error_type": type(e).__name__
                    })
                    
                    results[username] = {
                        "status": "error",
                        "message": f"Failed to update sheet: {error_details}",
                        "debug": user_debug
                    }

            self._save_user_config()  # Save updated workload info
            debug_info["final_results"] = results
            return results

        except Exception as e:
            return {
                "error": f"Distribution failed: {str(e)}",
                "debug": {
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    def _save_user_config(self):
        """Save user configuration to a JSON file"""
        config = {
            username: {
                "name": user.name,
                "sheet_id": user.google_sheet_id,
                "active": user.active,
                "workload": user.workload
            }
            for username, user in self.users.items()
        }
        with open('user_config.json', 'w') as f:
            json.dump(config, f, indent=2)

    def _load_user_config(self):
        """Load user configuration from JSON file"""
        try:
            with open('user_config.json', 'r') as f:
                config = json.load(f)
                self.users = {
                    username: User(
                        name=data["name"],
                        google_sheet_id=data["sheet_id"],
                        active=data["active"],
                        workload=data.get("workload", 0)
                    )
                    for username, data in config.items()
                }
        except FileNotFoundError:
            # Use default configuration if file doesn't exist
            pass


class DelayedMaidsAnalytics:
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.FLATLY,
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
            ],
            title="Delayed Cases Analytics",
            prevent_initial_callbacks='initial_duplicate'
        )
        self.server = self.app.server 
        self.df = pd.DataFrame()
        self.user_manager = UserManager()
        self.threshold_manager = ThresholdManager()  # Add the threshold manager
        
    def create_threshold_modal(self):
        """Create modal for threshold configuration"""
        return dbc.Modal([
            dbc.ModalHeader([
                html.H5([
                    html.I(className="fas fa-clock me-2"),
                    "Stage Thresholds Configuration"
                ])
            ]),
            dbc.ModalBody([
                html.Div([
                    html.H6("Configure Time Thresholds per Stage", className="mb-3"),
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "Set the maximum allowed time (in hours) for each stage. Cases exceeding these thresholds will be flagged as delayed."
                    ], color="info", className="mb-3"),
                    dash_table.DataTable(
                        id='threshold-table',
                        columns=[
                            {'name': 'Stage', 'id': 'stage', 'type': 'text'},
                            {'name': 'Threshold (hours)', 'id': 'threshold', 'type': 'numeric', 'editable': True}
                        ],
                        data=self.threshold_manager.get_all_thresholds(),
                        editable=True,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="single",
                        page_action="native",
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '12px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                        },
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'threshold', 'filter_query': '{threshold} > 72'},
                                'backgroundColor': '#ffebee',
                                'color': '#c62828'
                            }
                        ]
                    )
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    ["Reset to Default ", html.I(className="fas fa-undo")],
                    id="reset-thresholds-btn",
                    color="secondary",
                    className="me-2"
                ),
                dbc.Button(
                    ["Save Changes ", html.I(className="fas fa-save")],
                    id="save-thresholds-btn",
                    color="primary",
                    className="me-2"
                ),
                dbc.Button(
                    "Close",
                    id="close-threshold-modal-btn",
                    color="light"
                )
            ])
        ], id="threshold-modal", size="lg")

        
    def create_kpi_cards(self, df):
        """Create KPI cards with metrics."""
        total_cases = len(df)
        if total_cases == 0:
            return [
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("0", className="text-primary mb-1"),
                            html.P("Total Delayed Cases", className="mb-1"),
                            html.Div([
                                html.I(className="fas fa-users me-2"),
                                html.Span("No data available")
                            ], className="text-muted small")
                        ])
                    ], className="border-start border-primary border-4 h-100")
                ], width=3) for _ in range(4)
            ]
        
        critical_cases = len(df[df['Severity'] == 'Critical'])
        angry_clients = len(df[df['Client Note'] == 'SUPER_ANGRY_CLIENT'])
        avg_delay = df['Delay (hours)'].mean()
        highest_priority = df['Priority Score'].max()
        
        cards = [
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3([
                            f"{total_cases:,}",
                            html.Span("cases", className="fs-6 ms-2 text-muted")
                        ], className="text-primary mb-1"),
                        html.P("Total Delayed Cases", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-users me-2"),
                            html.Span(f"{(critical_cases/total_cases*100):.1f}% Critical")
                        ], className="text-muted small")
                    ])
                ], className="border-start border-primary border-4 h-100")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3([
                            f"{angry_clients:,}",
                            html.Span("clients", className="fs-6 ms-2 text-muted")
                        ], className="text-danger mb-1"),
                        html.P("Super Angry Clients", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-exclamation-circle me-2"),
                            html.Span(f"{(angry_clients/total_cases*100):.1f}% of Total")
                        ], className="text-danger small")
                    ])
                ], className="border-start border-danger border-4 h-100")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3([
                            f"{avg_delay:.1f}",
                            html.Span("hours", className="fs-6 ms-2 text-muted")
                        ], className="text-warning mb-1"),
                        html.P("Average Delay", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-clock me-2"),
                            html.Span("Per Case")
                        ], className="text-warning small")
                    ])
                ], className="border-start border-warning border-4 h-100")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3([
                            f"{critical_cases:,}",
                            html.Span("cases", className="fs-6 ms-2 text-muted")
                        ], className="text-danger mb-1"),
                        html.P("Critical Cases", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Highest Priority: {int(highest_priority)}")
                        ], className="text-danger small")
                    ])
                ], className="border-start border-danger border-4 h-100")
            ], width=3)
        ]
        
        return cards

    def create_client_priority_chart(self, df):
        """Create enhanced client priority distribution chart."""
        priority_metrics = df.groupby('Client Note').agg({
            'Delay (hours)': ['mean', 'count', 'sum'],
            'Priority Score': 'mean'
        }).reset_index()
        
        priority_metrics.columns = ['Client Note', 'Avg Delay', 'Count', 'Total Delay', 'Avg Priority']
        
        # Define priority order and colors
        priority_order = ['SUPER_ANGRY_CLIENT', 'PRIORITIZE_VISA', 'AMNESTY', 'STANDARD']
        priority_colors = {
            'SUPER_ANGRY_CLIENT': '#d32f2f',
            'PRIORITIZE_VISA': '#f57c00',
            'AMNESTY': '#388e3c',
            'STANDARD': '#1976d2'
        }
        
        priority_metrics['Client Note'] = pd.Categorical(
            priority_metrics['Client Note'],
            categories=priority_order,
            ordered=True
        )
        priority_metrics = priority_metrics.sort_values('Client Note')
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Average Delay',
            x=priority_metrics['Client Note'],
            y=priority_metrics['Avg Delay'],
            text=[f'Cases: {int(x)}' for x in priority_metrics['Count']],
            textposition='auto',
            marker_color=[priority_colors.get(x, '#1976d2') for x in priority_metrics['Client Note']],
            hovertemplate=(
                '<b>%{x}</b><br>' +
                'Average Delay: %{y:.1f} hours<br>' +
                '%{text}<br>' +
                'Total Delay: %{customdata[0]:.0f} hours<br>' +
                'Avg Priority Score: %{customdata[1]:.0f}<br>' +
                '<extra></extra>'
            ),
            customdata=np.column_stack((
                priority_metrics['Total Delay'],
                priority_metrics['Avg Priority']
            ))
        ))
        
        # Fixed layout to avoid duplicate yaxis
        fig.update_layout(
            title=None,
            xaxis_title="Client Priority Level",
            yaxis_title="Average Delay (hours)",
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Update axes separately
        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(size=12)
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridcolor='rgb(204, 204, 204)',
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(size=12)
        )
        
        return fig

    def create_priority_stage_chart(self, df):
        """Create enhanced priority stage distribution chart."""
        if len(df) == 0:
            return go.Figure()
        
        pivot_data = pd.crosstab(
            df['Current Stage'],
            df['Client Note']
        ).fillna(0)
        
        total_cases = pivot_data.sum(axis=1)
        pivot_data = pivot_data.loc[total_cases.sort_values(ascending=True).index]
        pivot_data = pivot_data.tail(10)
        
        colors = {
            'SUPER_ANGRY_CLIENT': '#d32f2f',
            'PRIORITIZE_VISA': '#f57c00',
            'AMNESTY': '#388e3c',
            'STANDARD': '#1976d2'
        }
        
        fig = go.Figure()
        
        for client_type in pivot_data.columns:
            fig.add_trace(go.Bar(
                name=client_type,
                y=pivot_data.index,
                x=pivot_data[client_type],
                orientation='h',
                marker_color=colors.get(client_type, '#1976d2'),
                hovertemplate=(
                    '<b>%{y}</b><br>' +
                    f'{client_type}<br>' +
                    'Number of Cases: %{x}<br>' +
                    '<extra></extra>'
                )
            ))
        
        # Fixed layout to avoid duplicate yaxis
        fig.update_layout(
            title=None,
            barmode='stack',
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            legend_title="Client Priority",
            xaxis_title="Number of Cases",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Update axes separately
        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgb(204, 204, 204)',
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside'
        )
        
        fig.update_yaxes(
            categoryorder='total ascending',
            showgrid=False,
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(size=10),
            tickangle=0
        )
        
        return fig
    
    
    def process_data(self, df):
        """Process the uploaded data with proper handling of all fields."""
        try:
            df = df.copy()
            df.columns = df.columns.str.strip()
            
            required_columns = ['Housemaid ID', 'Current Stage']
            df = df.dropna(subset=required_columns)
            
            # Handle numeric fields
            df['RPA try count'] = pd.to_numeric(df['RPA try count'], errors='coerce').fillna(0).astype(int)
            df['Time In Stage'] = pd.to_numeric(df['Time In Stage'], errors='coerce').fillna(0)
            
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
            
            # Use threshold manager for calculations
            df['Threshold (in hours)'] = df['Current Stage'].apply(self.threshold_manager.get_threshold)
            df['Delay (hours)'] = (df['Time In Stage'] - df['Threshold (in hours)']).fillna(0)
            
            df['Threshold Ratio'] = df['Time In Stage'] / df['Threshold (in hours)']
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
                        # Manage Users button
                        dbc.Button(
                            ["Manage Users ", html.I(className="fas fa-users-cog")],
                            id="open-user-modal",
                            color="light",
                            className="me-2"
                        ),
                        # Configure Thresholds button
                        dbc.Button(
                            ["Configure Thresholds ", html.I(className="fas fa-clock")],
                            id="open-threshold-modal",
                            color="light",
                            className="me-2"
                        ),
                        # Upload button
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
            # Add this to your create_layout method, after the navbar
           dbc.Modal([
            dbc.ModalHeader("User Management"),
            dbc.ModalBody([
                # User List Table
                html.Div([
                    html.H6("Current Users", className="mb-3"),
                    dash_table.DataTable(
                        id='user-management-table',
                        columns=[
                            {'name': 'Username', 'id': 'username', 'type': 'text'},
                            {'name': 'Display Name', 'id': 'name', 'type': 'text'},
                            {'name': 'Sheet ID', 'id': 'sheet_id', 'type': 'text'},
                            {'name': 'Status', 'id': 'status', 'type': 'text'},
                            {'name': 'Tasks', 'id': 'workload', 'type': 'numeric'}
                        ],
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '12px',
                        },
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        row_selectable='single',
                        selected_rows=[],
                    ),
                ], className="mb-4"),
                
                # Add/Edit User Form
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Username"),
                            dbc.Input(id="user-username", type="text", placeholder="e.g., john.doe")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Display Name"),
                            dbc.Input(id="user-displayname", type="text", placeholder="e.g., John Doe")
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Google Sheet URL"),
                            dbc.Input(id="user-sheet-url", type="text", 
                                    placeholder="Paste Google Sheet URL"),
                            dbc.FormText("Paste the full Google Sheet URL or just the ID")
                        ], width=12)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Add New User", id="add-user-btn", 
                                        color="success", className="me-2"),
                                dbc.Button("Update Selected", id="update-user-btn", 
                                        color="primary", className="me-2"),
                                dbc.Button("Delete Selected", id="delete-user-btn", 
                                        color="danger")
                            ])
                        ])
                    ])
                ])
            ])
        ], id="user-management-modal", size="lg"),

        # Add the threshold modal
        self.create_threshold_modal(),

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

                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-share me-2"),
                            "Distribute Tasks"
                        ])
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Select Users to Assign Tasks", className="mb-2"),
                                html.Div([
                                    dcc.Dropdown(
                                        id='users-to-distribute',
                                        options=[
                                            {'label': user.name, 'value': username}
                                            for username, user in self.user_manager.users.items()
                                            if user.active
                                        ],
                                        multi=True,
                                        placeholder="Select users to distribute tasks to...",
                                        className="mb-3"
                                    )
                                ], style={
                                    'position': 'relative',
                                    'zIndex': '1000'  # Higher z-index
                                })
                            ], width=8),
                            dbc.Col([
                                html.Label("\u00A0", className="mb-2"),
                                dbc.Button(
                                    ["Distribute Tasks ", html.I(className="fas fa-paper-plane ms-1")],
                                    id="distribute-btn",
                                    color="primary",
                                    className="w-100"
                                )
                            ], width=4)
                        ])
                    ])
                ], className="mb-4 shadow-sm"),
                # Enhanced Severity Legend with Icons
                dbc.Card([
                    dbc.CardBody([
                        html.H6([
                            html.I(className="fas fa-exclamation-triangle me-2", 
                                style={'color': '#ff9800'}),
                            "Understanding Severity Levels"
                        ], className="text-primary mb-4"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.Div(className="severity-dot low"),
                                        html.Div(className="severity-pulse low")
                                    ], className="severity-indicator-wrapper"),
                                    html.Div([
                                        html.Span("Low Priority", className="severity-title"),
                                        html.Small("Up to 50% over threshold", 
                                                className="severity-description")
                                    ], className="severity-text")
                                ], className="severity-item"),
                                html.Div([
                                    html.Div([
                                        html.Div(className="severity-dot medium"),
                                        html.Div(className="severity-pulse medium")
                                    ], className="severity-indicator-wrapper"),
                                    html.Div([
                                        html.Span("Medium Priority", className="severity-title"),
                                        html.Small("50-100% over threshold", 
                                                className="severity-description")
                                    ], className="severity-text")
                                ], className="severity-item")
                            ], md=6),
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.Div(className="severity-dot high"),
                                        html.Div(className="severity-pulse high")
                                    ], className="severity-indicator-wrapper"),
                                    html.Div([
                                        html.Span("High Priority", className="severity-title"),
                                        html.Small("100-200% over threshold", 
                                                className="severity-description")
                                    ], className="severity-text")
                                ], className="severity-item"),
                                html.Div([
                                    html.Div([
                                        html.Div(className="severity-dot critical"),
                                        html.Div(className="severity-pulse critical")
                                    ], className="severity-indicator-wrapper"),
                                    html.Div([
                                        html.Span("Critical Priority", className="severity-title"),
                                        html.Small("Over 200% threshold", 
                                                className="severity-description")
                                    ], className="severity-text")
                                ], className="severity-item")
                            ], md=6)
                        ])
                    ])
                ], className="mb-4 severity-card"),

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
                                
                            ], className="text-center text-muted small mt-1")
                        ])
                    ])
                ], className="py-3")
            ])
        ])

    def setup_callbacks(self):
        """Set up enhanced callbacks with new filter functionality."""
        @self.app.callback(
            Output("threshold-modal", "is_open"),
            [
                Input("open-threshold-modal", "n_clicks"),
                Input("close-threshold-modal-btn", "n_clicks"),
                Input("save-thresholds-btn", "n_clicks")
            ],
            [State("threshold-modal", "is_open")],
            prevent_initial_call=True
        )
        def toggle_threshold_modal(n1, n2, n3, is_open):
            if n1 or n2 or n3:
                return not is_open
            return is_open
        
        @self.app.callback(
            [Output('threshold-table', 'data'),
            Output('alerts-area', 'children', allow_duplicate=True)],
            [
                Input('reset-thresholds-btn', 'n_clicks'),
                Input('save-thresholds-btn', 'n_clicks')
            ],
            [State('threshold-table', 'data')],
            prevent_initial_call=True
        )
        def manage_thresholds(reset_clicks, save_clicks, current_data):
                ctx = dash.callback_context
                if not ctx.triggered:
                    return dash.no_update, dash.no_update
        
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                try:
                    if trigger_id == 'reset-thresholds-btn':
                        # Reset to default values
                        self.threshold_manager = ThresholdManager()
                        return self.threshold_manager.get_all_thresholds(), dbc.Alert(
                            "All thresholds reset to default (24 hours)",
                            color="success",
                            duration=3000,
                            is_open=True,
                            dismissable=True
                        )
        
                    elif trigger_id == 'save-thresholds-btn':
                        # Update thresholds from table data
                        new_thresholds = {row['stage']: row['threshold'] for row in current_data}
                        if self.threshold_manager.bulk_update_thresholds(new_thresholds):
                            # Reprocess data if we have any loaded
                            if not self.df.empty:
                                self.df = self.process_data(self.df)
                            return current_data, dbc.Alert(
                                "Thresholds updated successfully",
                                color="success",
                                duration=3000,
                                is_open=True,
                                dismissable=True
                            )
                        else:
                            raise ValueError("Invalid threshold values")
        
                except Exception as e:
                    return self.threshold_manager.get_all_thresholds(), dbc.Alert(
                        f"Error updating thresholds: {str(e)}",
                        color="danger",
                        duration=3000,
                        is_open=True,
                        dismissable=True
                    )
                
                return dash.no_update, dash.no_update
        # Callback for opening/closing the modal
        @self.app.callback(
            Output("user-management-modal", "is_open"),
            [Input("open-user-modal", "n_clicks")],
            [State("user-management-modal", "is_open")],
            prevent_initial_call=True  # Add this line
        )
        def toggle_modal(n1, is_open):
            if n1:
                return not is_open
            return is_open

        # Callback for user management and table updates
        @self.app.callback(
            [Output('user-management-table', 'data'),
            Output('alerts-area', 'children')],
            [Input('user-management-modal', 'is_open'),
            Input('add-user-btn', 'n_clicks'),
            Input('update-user-btn', 'n_clicks'),
            Input('delete-user-btn', 'n_clicks')],
            [State('user-username', 'value'),
            State('user-displayname', 'value'),
            State('user-sheet-url', 'value'),
            State('user-management-table', 'selected_rows'),
            State('user-management-table', 'data')],
            prevent_initial_call=True
        )
        def manage_users_and_table(is_open, add_clicks, update_clicks, delete_clicks,
                          username, displayname, sheet_url, selected_rows, table_data):
            ctx = dash.callback_context
            if not ctx.triggered:
                user_data = [
                    {
                        'username': username,
                        'name': user.name,
                        'sheet_id': user.google_sheet_id,
                        'status': 'Active' if user.active else 'Inactive',
                        'workload': user.workload
                    }
                    for username, user in self.user_manager.users.items()
                ]
                return user_data, dash.no_update

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if trigger_id == 'user-management-modal':
                user_data = [
                    {
                        'username': username,
                        'name': user.name,
                        'sheet_id': user.google_sheet_id,
                        'status': 'Active' if user.active else 'Inactive',
                        'workload': user.workload
                    }
                    for username, user in self.user_manager.users.items()
                ]
                return user_data, dash.no_update

            try:
                if trigger_id == 'add-user-btn':
                    if not all([username, displayname, sheet_url]):
                        return dash.no_update, dbc.Alert(
                            "All fields are required",
                            color="warning",
                            dismissable=True
                        )
                    
                    try:
                        sheet_id = self.user_manager.extract_sheet_id(sheet_url)
                        if self.user_manager.add_user(username, displayname, sheet_id):
                            alert = dbc.Alert(
                                f"User {displayname} added successfully",
                                color="success",
                                dismissable=True
                            )
                        else:
                            raise Exception("Failed to add user")
                    except Exception as e:
                        return dash.no_update, dbc.Alert(
                            f"Error adding user: {str(e)}",
                            color="danger",
                            dismissable=True
                        )

                elif trigger_id == 'update-user-btn':
                    if not selected_rows:
                        return dash.no_update, dbc.Alert(
                            "Please select a user to update",
                            color="warning",
                            dismissable=True
                        )
                    
                    try:
                        sheet_id = self.user_manager.extract_sheet_id(sheet_url) if sheet_url else None
                        selected_username = table_data[selected_rows[0]]['username']
                        if self.user_manager.update_user(selected_username, displayname, sheet_id):
                            alert = dbc.Alert(
                                f"User updated successfully",
                                color="success",
                                dismissable=True
                            )
                        else:
                            raise Exception("Failed to update user")
                    except Exception as e:
                        return dash.no_update, dbc.Alert(
                            f"Error updating user: {str(e)}",
                            color="danger",
                            dismissable=True
                        )

                elif trigger_id == 'delete-user-btn':
                    if not selected_rows:
                        return dash.no_update, dbc.Alert(
                            "Please select a user to delete",
                            color="warning",
                            dismissable=True
                        )
                    
                    try:
                        selected_user = table_data[selected_rows[0]]['username']
                        if self.user_manager.delete_user(selected_user):
                            # Get updated user data after deletion
                            user_data = [
                                {
                                    'username': username,
                                    'name': user.name,
                                    'sheet_id': user.google_sheet_id,
                                    'status': 'Active' if user.active else 'Inactive',
                                    'workload': user.workload
                                }
                                for username, user in self.user_manager.users.items()
                            ]
                            alert = dbc.Alert(
                                f"User {selected_user} deleted successfully",
                                color="success",
                                dismissable=True
                            )
                            return user_data, alert
                        else:
                            raise Exception("Failed to delete user")
                    except Exception as e:
                        return dash.no_update, dbc.Alert(
                            f"Error deleting user: {str(e)}",
                            color="danger",
                            dismissable=True
                        )

                # Get updated user data
                user_data = [
                    {
                        'username': username,
                        'name': user.name,
                        'sheet_id': user.google_sheet_id,
                        'status': 'Active' if user.active else 'Inactive',
                        'workload': user.workload
                    }
                    for username, user in self.user_manager.users.items()
                ]
                
                return user_data, alert

            except Exception as e:
                return dash.no_update, dbc.Alert(
                    f"Error: {str(e)}",
                    color="danger",
                    dismissable=True
                )

        # Callback to populate form when selecting a user
        @self.app.callback(
            [Output('user-username', 'value'),
            Output('user-displayname', 'value'),
            Output('user-sheet-url', 'value')],
            [Input('user-management-table', 'selected_rows')],
            [State('user-management-table', 'data')],
            prevent_initial_call=True
        )
        def populate_form(selected_rows, table_data):
            """Populate form when user is selected"""
            if not selected_rows:
                return "", "", ""
            
            selected_user = table_data[selected_rows[0]]
            return (
                selected_user['username'],
                selected_user['name'],
                selected_user['sheet_id']
            )

        # Callback for reset filters
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

        # Your existing update_dashboard callback
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
            Output('alerts-area', 'children', allow_duplicate=True)],
            [Input('upload-data', 'contents'),
            Input('apply-filters-btn', 'n_clicks'),
            Input('distribute-btn', 'n_clicks')],
            [State('upload-data', 'filename'),
            State('stage-filter', 'value'),
            State('type-filter', 'value'),
            State('nationality-filter', 'value'),
            State('client-note-filter', 'value'),
            State('table-search', 'value'),
            State('table-sort-field', 'value'),
            State('records-per-page', 'value'),
            State('users-to-distribute', 'value'),
            State('detailed-table', 'data')],
            prevent_initial_call=True  # Add this line
        )
        def update_dashboard(contents, filter_clicks, distribute_clicks,
                      filename, stage_filter, type_filter,
                      nationality_filter, client_note_filter,
                      search_value, sort_field, records_per_page,
                      selected_users, table_data):
            """Update dashboard with enhanced filtering and sorting."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return [[], {}, {}, [], [], [], [], [], "", None]
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # Handle distribution button click
            if trigger_id == 'distribute-btn':
                if not selected_users or not table_data:
                    return dash.no_update * 9 + (
                        dbc.Alert("Please select users and ensure there is data to distribute",
                                color="warning", dismissable=True),
                    )
                
                try:
                    df = pd.DataFrame(table_data)
                    results = self.user_manager.distribute_data(selected_users, df)
                    
                    # Process detailed results
                    success_count = sum(1 for r in results.values() 
                                      if isinstance(r, dict) and r.get("status") == "success")
                    error_count = sum(1 for r in results.values() 
                                     if isinstance(r, dict) and r.get("status") == "error")
                    warning_count = sum(1 for r in results.values() 
                                      if isinstance(r, dict) and r.get("status") == "warning")
                    
                    alert_content = []
                    
                    # Summary section
                    summary = [
                        html.H5("Distribution Results", className="mb-3"),
                        html.P([
                            f"Successfully distributed to {success_count} users",
                            html.Br(),
                            f"Errors: {error_count}",
                            html.Br(),
                            f"Warnings: {warning_count}"
                        ], className="mb-3")
                    ]
                    alert_content.extend(summary)
                    
                    # Detailed results section
                    if error_count > 0 or warning_count > 0:
                        alert_content.append(html.H6("Detailed Results:", className="mb-2"))
                        for username, result in results.items():
                            if isinstance(result, dict):
                                if result["status"] in ["error", "warning"]:
                                    alert_content.extend([
                                        html.Div([
                                            html.Strong(f"{username}: "),
                                            result["message"],
                                            # Add debugging info if available
                                            html.Details([
                                                html.Summary("Debug Info"),
                                                html.Pre(json.dumps(result["debug"], indent=2))
                                            ]) if "debug" in result else None
                                        ], className="mb-2")
                                    ])
                    
                    # Determine alert color based on results
                    if error_count > 0:
                        alert_color = "danger"
                    elif warning_count > 0:
                        alert_color = "warning"
                    else:
                        alert_color = "success"
                    
                    alert = dbc.Alert(
                        alert_content,
                        color=alert_color,
                        dismissable=True
                    )
                    
                    return dash.no_update * 9 + (alert,)
                                
                except Exception as e:
                    error_alert = dbc.Alert(
                        [
                            html.H5("Distribution Error", className="mb-3"),
                            html.P(str(e)),
                            html.Details([
                                html.Summary("Debug Info"),
                                html.Pre(traceback.format_exc())
                            ])
                        ],
                        color="danger",
                        dismissable=True
                    )
                    return dash.no_update * 9 + (error_alert,)
            # Handle data upload and filtering (existing functionality)
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
                    dbc.Alert(
                        f"Error processing data: {str(e)}", 
                        color="danger", 
                        dismissable=True
                    )
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
        """Add comprehensive custom CSS styles."""
        custom_css = """
            /* Core Variables */
            :root {
                --primary: #1976d2;
                --primary-light: #2196f3;
                --primary-dark: #1565c0;
                --success: #2e7d32;
                --warning: #ed6c02;
                --danger: #d32f2f;
                --neutral-dark: #2c3e50;
                --neutral-light: #f8f9fa;
                --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
                --shadow-md: 0 4px 8px rgba(0,0,0,0.1); 
                --shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
                --border-radius: 12px;
                --transition: all 0.3s ease;
            }

            /* Global Styles */
            body {
                background-color: var(--neutral-light);
                color: var(--neutral-dark);
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
            }

            /* Card Styles */
            .card {
                background: white;
                border: none;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow-md);
                transition: var(--transition);
                overflow: visible;
            }

            .card:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-lg);
            }

            .card-header {
                background: linear-gradient(145deg, white 0%, var(--neutral-light) 100%);
                border-bottom: 1px solid rgba(0,0,0,0.1);
                padding: 1.25rem;
            }

            /* Navbar Styles */
            .navbar {
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                border-radius: 0 0 var(--border-radius) var(--border-radius);
                box-shadow: var(--shadow-md);
            }

            /* Button Styles */
            .btn {
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: var(--transition);
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                border: none;
                box-shadow: 0 4px 6px rgba(33, 150, 243, 0.2);
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(33, 150, 243, 0.3);
            }

            /* Dropdown Styles */
            .dropdown-wrapper {
                position: relative !important;
                z-index: 1500 !important;
            }

            .Select-control {
                border: 2px solid #e0e0e0 !important;
                border-radius: 8px !important;
                transition: var(--transition) !important;
            }

            .Select-control:hover {
                border-color: var(--primary-light) !important;
            }

            .Select-menu-outer {
                border: none !important;
                border-radius: 8px !important;
                box-shadow: var(--shadow-lg) !important;
                z-index: 1600 !important;
                margin-top: 4px !important;
            }

            /* Severity Card Styles */
            .severity-card {
                background: linear-gradient(145deg, white 0%, var(--neutral-light) 100%);
            }

            .severity-item {
                display: flex;
                align-items: center;
                padding: 1rem;
                margin-bottom: 1rem;
                background: white;
                border-radius: 8px;
                transition: var(--transition);
                box-shadow: var(--shadow-sm);
            }

            .severity-item:hover {
                transform: translateX(8px);
                box-shadow: var(--shadow-md);
            }

            .severity-indicator-wrapper {
                position: relative;
                width: 40px;
                height: 40px;
                margin-right: 1rem;
            }

            .severity-dot {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }

            .severity-pulse {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 24px;
                height: 24px;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
                50% { transform: translate(-50%, -50%) scale(1.5); opacity: 0.2; }
                100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
            }

            .severity-dot.low, .severity-pulse.low {
                background-color: #4caf50;
            }

            .severity-dot.medium, .severity-pulse.medium {
                background-color: #ffc107;
            }

            .severity-dot.high, .severity-pulse.high {
                background-color: #ff9800;
            }

            .severity-dot.critical, .severity-pulse.critical {
                background-color: #f44336;
            }

            /* Table Styles */
            .dash-table-container {
                border-radius: var(--border-radius);
                overflow: hidden;
                box-shadow: var(--shadow-md);
            }

            .dash-spreadsheet-container .dash-spreadsheet-inner td,
            .dash-spreadsheet-container .dash-spreadsheet-inner th {
                padding: 1rem;
                border: 1px solid #e0e0e0;
                font-size: 0.9rem;
            }

            .dash-spreadsheet-container .dash-spreadsheet-inner th {
                background: linear-gradient(145deg, var(--neutral-light) 0%, #e9ecef 100%);
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            /* Alert Styles */
            .alert {
                border-radius: var(--border-radius);
                border: none;
                padding: 1rem 1.5rem;
                box-shadow: var(--shadow-sm);
            }

            .alert-success {
                background: linear-gradient(145deg, #e8f5e9 0%, #c8e6c9 100%);
                color: var(--success);
            }

            .alert-warning {
                background: linear-gradient(145deg, #fff3e0 0%, #ffe0b2 100%);
                color: var(--warning);
            }

            .alert-danger {
                background: linear-gradient(145deg, #ffebee 0%, #ffcdd2 100%);
                color: var(--danger);
            }

            /* Form Styles */
            .form-control {
                border-radius: 8px;
                padding: 0.75rem 1rem;
                border: 2px solid #e0e0e0;
                transition: var(--transition);
            }

            .form-control:focus {
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
            }

            /* Modal Styles */
            .modal-content {
                border-radius: var(--border-radius);
                border: none;
                box-shadow: var(--shadow-lg);
            }

            .modal-header {
                background: linear-gradient(145deg, var(--neutral-light) 0%, #e9ecef 100%);
                border-radius: calc(var(--border-radius) - 1px) calc(var(--border-radius) - 1px) 0 0;
                border-bottom: 2px solid #e9ecef;
            }

            /* KPI Card Styles */
            .kpi-card {
                background: linear-gradient(145deg, white 0%, var(--neutral-light) 100%);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                transition: var(--transition);
            }

            .kpi-card:hover {
                transform: translateY(-4px);
            }

            /* Chart Styles */
            .chart-container {
                background: white;
                border-radius: var(--border-radius);
                padding: 1.5rem;
                box-shadow: var(--shadow-md);
                margin-bottom: 1.5rem;
            }

            /* Status Indicators */
            .status-indicator {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 8px;
            }

            .status-active {
                background-color: var(--success);
                box-shadow: 0 0 0 4px rgba(46, 125, 50, 0.2);
            }

            .status-inactive {
                background-color: var(--danger);
                box-shadow: 0 0 0 4px rgba(211, 47, 47, 0.2);
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

if __name__ == "__main__":
    analytics_app = DelayedMaidsAnalytics()
    analytics_app.create_layout()  # Explicitly create layout here
    analytics_app.setup_callbacks()  # Setup callbacks before starting
    server = analytics_app.app.server  # Expose Flask server for Gunicorn
    analytics_app.run_server(debug=True, port=8050, host="0.0.0.0")
else:
    analytics_app = DelayedMaidsAnalytics()
    analytics_app.create_layout()
    analytics_app.setup_callbacks()
    server = analytics_app.app.server
