from flask import Flask, jsonify, render_template, request
from flask.json.provider import JSONProvider
import pandas as pd
import numpy as np
import json

# Custom JSON provider to handle NumPy types
class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=NumpyEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super(NumpyEncoder, self).default(obj)

app = Flask(__name__)
app.json = CustomJSONProvider(app)

@app.route('/')
def dashboard():
    return render_template('dashboard_template.html')

@app.route('/api/data')
def get_data():
    try:
        # Get filter parameters from the request URL
        unit_filter = request.args.get('unit', 'All ICU Units')
        date_range_filter = request.args.get('date_range', 'Last 30 Days')
        acuity_filter = request.args.get('acuity_level')
        admission_filter = request.args.get('admission_source')

        df_full = pd.read_csv('icu_data.csv')
        df_full['Date'] = pd.to_datetime(df_full['Date'])

        # --- Apply Filters ---
        df_filtered = df_full.copy()
        if not df_full.empty:
            latest_date_in_dataset = df_full['Date'].max()

            if date_range_filter == 'Last 7 Days':
                df_filtered = df_filtered[df_filtered['Date'] >= (latest_date_in_dataset - pd.Timedelta(days=6))]
            elif date_range_filter == 'Last 30 Days':
                df_filtered = df_filtered[df_filtered['Date'] >= (latest_date_in_dataset - pd.Timedelta(days=29))]

            if unit_filter != 'All ICU Units':
                df_filtered = df_filtered[df_filtered['Unit'] == unit_filter]
            
            if acuity_filter:
                df_filtered = df_filtered[df_filtered['AcuityLevel'] == acuity_filter]
            
            if admission_filter:
                df_filtered = df_filtered[df_filtered['AdmissionSource'] == admission_filter]

        # --- Process your DataFrame ---
        if df_filtered.empty:
            return jsonify({
                'kpis': {'bed_occupancy': 0, 'patient_census': 0, 'ventilator_utilization': 0, 'avg_los': 0},
                'charts': {
                    'census_over_time': {'labels': [], 'datasets': []},
                    'acuity_levels': {'labels': [], 'datasets': []},
                    'admission_source': {'labels': [], 'datasets': []}
                },
                'patient_details': []
            })

        latest_data = df_filtered.sort_values(by='Date').iloc[-1]
        bed_occupancy = latest_data['BedOccupancy']
        patient_census = latest_data['PatientCensus']
        ventilator_utilization = latest_data['VentilatorUtilization']
        avg_los = df_filtered['LengthOfStay'].mean()
        if pd.isna(avg_los):
            avg_los = 0

        chart_df = df_filtered.sort_values(by='Date').tail(30)
        
        census_over_time_data = {
            'labels': chart_df['Date'].dt.strftime('%b %d').tolist(),
            'datasets': [
                {
                    'label': 'Patient Census',
                    'data': chart_df['PatientCensus'].tolist(),
                    'borderColor': '#4A90E2',
                    'tension': 0.1
                }, 
                {
                    'label': 'Bed Availability',
                    'data': [50] * len(chart_df),
                    'backgroundColor': 'rgba(74, 144, 226, 0.1)',
                    'fill': True,
                    'borderColor': '#4A90E2',
                    'borderDash': [5, 5],
                }
            ]
        }

        acuity_levels_data = {
            'labels': df_full['AcuityLevel'].unique().tolist(), # Show all possible levels
            'datasets': [{
                'label': 'Patient Count',
                'data': df_filtered['AcuityLevel'].value_counts().reindex(df_full['AcuityLevel'].unique(), fill_value=0).tolist(),
                'backgroundColor': ['#4A90E2', '#F5A623', '#D0021B']
            }]
        }

        admission_source_data = {
            'labels': df_full['AdmissionSource'].unique().tolist(), # Show all possible sources
            'datasets': [{
                'data': df_filtered['AdmissionSource'].value_counts().reindex(df_full['AdmissionSource'].unique(), fill_value=0).tolist(),
                'backgroundColor': ['#4A90E2', '#50E3C2', '#B8E986']
            }]
        }

        patient_details = df_filtered.sort_values(by='Date', ascending=False).head(10).to_dict('records')

        data = {
            'kpis': {
                'bed_occupancy': bed_occupancy,
                'patient_census': patient_census,
                'ventilator_utilization': ventilator_utilization,
                'avg_los': round(avg_los, 1)
            },
            'charts': {
                'census_over_time': census_over_time_data,
                'acuity_levels': acuity_levels_data,
                'admission_source': admission_source_data
            },
            'patient_details': patient_details
        }

        return jsonify(data)

    except FileNotFoundError:
        return jsonify({"error": "icu_data.csv not found."}), 404
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An unexpected error occurred on the server: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
