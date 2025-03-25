from flask import Flask, request, jsonify, send_file, render_template
import matplotlib
matplotlib.use('Agg')  # Set the backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import io
import base64

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-timeline', methods=['POST'])
def generate_timeline():
    try:
        data = request.json
        
        # Extract parameters with defaults if not provided
        project_name = data.get('project_name', 'Project Timeline')
        
        # Parse tasks from request
        tasks = []
        for task in data.get('tasks', []):
            name = task.get('name', 'Task')
            duration = task.get('duration', 1)
            tasks.append((name, duration))
        
        if not tasks:
            # Default tasks if none provided
            tasks = [
                ("Riser Works", 8),
                ("Riser Pressure Test", 2),
                ("Sprinkler Works", 10),
                ("Sprinkler Pressure Test", 2),
                ("Product Ex Work", 49),
                ("Shipped on Board", 18),
                ("Vessel at Chittagong", 21),
                ("Materials from port to site", 10),
                ("Pump Room", 10),
                ("Testing Commissioning & Balancing", 5),
            ]
        
        # Parse dates
        start_date_str = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        # Parse holidays - no default holidays added here
        holidays = []
        for holiday in data.get('holidays', []):
            holiday_start = datetime.strptime(holiday.get('start_date'), '%Y-%m-%d')
            holiday_end = datetime.strptime(holiday.get('end_date'), '%Y-%m-%d')
            holiday_name = holiday.get('name', 'Holiday')
            holiday_color = holiday.get('color', '#ff9999')
            holidays.append({
                'start': holiday_start,
                'end': holiday_end,
                'name': holiday_name,
                'color': holiday_color
            })
        
        # Task categories and colors
        task_categories = data.get('task_categories', {
            'construction': {
                'indices': list(range(4)),
                'colors': ['#3498db', '#2980b9', '#1abc9c', '#16a085'],
                'label': 'Construction Tasks'
            },
            'procurement': {
                'indices': list(range(4, 8)),
                'colors': ['#e74c3c', '#c0392b', '#d35400', '#e67e22'],
                'label': 'Procurement Tasks'
            },
            'installation': {
                'indices': list(range(8, 10)),
                'colors': ['#9b59b6', '#8e44ad'],
                'label': 'Installation Tasks'
            }
        })
        
        # Function to calculate task end date considering holidays
        def calculate_end_date(start, duration):
            end_date = start
            days_to_add = duration
            
            while days_to_add > 0:
                end_date += timedelta(days=1)
                # Skip if the date is in any holiday period
                if not any(holiday['start'] <= end_date <= holiday['end'] for holiday in holidays):
                    days_to_add -= 1
                    
            return end_date

        # Generate task start and end dates
        task_dates = []
        
        # Process tasks based on dependencies
        dependencies = data.get('dependencies', {
            'sequential_groups': [
                {'start_idx': 0, 'end_idx': 3},  # Construction tasks
                {'start_idx': 4, 'end_idx': 7},  # Procurement tasks
            ],
            'dependent_tasks': [
                {'idx': 8, 'depends_on_idx': 7},  # Task 8 starts after task 7
                {'idx': 9, 'depends_on_idx': 8}   # Task 9 starts after task 8
            ]
        })
        
        # Process sequential groups
        for group in dependencies.get('sequential_groups', []):
            start_idx = group.get('start_idx', 0)
            end_idx = group.get('end_idx', 0)
            
            current_date = start_date
            for i in range(start_idx, end_idx + 1):
                if i < len(tasks):
                    task_start = current_date
                    task_end = calculate_end_date(task_start, tasks[i][1] - 1)  # -1 because start date counts as day 1
                    task_dates.append((task_start, task_end))
                    current_date = task_end + timedelta(days=1)
        
        # Process dependent tasks
        for dep in dependencies.get('dependent_tasks', []):
            idx = dep.get('idx')
            depends_on_idx = dep.get('depends_on_idx')
            
            if idx < len(tasks) and depends_on_idx < len(task_dates):
                task_start = task_dates[depends_on_idx][1] + timedelta(days=1)
                task_end = calculate_end_date(task_start, tasks[idx][1] - 1)
                task_dates.append((task_start, task_end))
        
        # Calculate project end date and total duration
        project_end = max(end for _, end in task_dates)
        total_days = (project_end - start_date).days + 1

        # Calculate actual working days (excluding holidays)
        holiday_days_in_project = 0
        current = start_date
        while current <= project_end:
            if any(holiday['start'] <= current <= holiday['end'] for holiday in holidays):
                holiday_days_in_project += 1
            current += timedelta(days=1)

        working_days = total_days - holiday_days_in_project

        # Plot the timeline
        fig, ax = plt.subplots(figsize=(14, 8))

        # Combine all colors for tasks
        colors = []
        for category in task_categories.values():
            colors.extend(category['colors'])
        
        # Ensure we have enough colors
        while len(colors) < len(tasks):
            colors.append('#333333')  # Default color

        # Plotting each task as a bar
        for i, task in enumerate(tasks):
            if i < len(task_dates):
                start, end = task_dates[i]
                duration = (end - start).days + 1
                ax.barh(task[0], end - start, left=start, height=0.6, align='center', 
                        color=colors[i] if i < len(colors) else '#333333', alpha=0.8, edgecolor='black')
                
                # Add duration text
                text_x = start + (end - start) / 2
                ax.text(text_x, i, f"{duration} days", ha='center', va='center', 
                        bbox=dict(facecolor='white', alpha=0.8, boxstyle="round,pad=0.3"))

        # Add holiday period indications
        if holidays:  # Only add holiday indicators if there are holidays
            holiday_range = np.arange(len(tasks))
            for holiday in holidays:
                ax.barh(holiday_range, holiday['end'] - holiday['start'], left=holiday['start'], height=0.3, 
                        align='center', color=holiday['color'], alpha=0.3, label=holiday['name'])
                ax.axvline(x=holiday['start'], color='#e74c3c', linestyle='--', alpha=0.7)
                ax.axvline(x=holiday['end'], color='#e74c3c', linestyle='--', alpha=0.7)

        # Formatting
        ax.set_xlabel('', fontsize=12, fontweight='bold')
        ax.set_ylabel('Tasks', fontsize=12, fontweight='bold')
        ax.set_title(f'{project_name} - Project Timeline', fontsize=16, fontweight='bold')

        # Format dates on x-axis
        date_format = mdates.DateFormatter('%b %d, %Y')
        ax.xaxis.set_major_formatter(date_format)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

        # Add grid for better readability
        ax.grid(True, axis='x', alpha=0.3)

        # Set y-axis limits to provide some padding
        plt.ylim(-0.5, len(tasks) - 0.5)

        # Set background color for better contrast
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#ffffff')

        # Create a legend for task categories and holidays
        legend_patches = []
        legend_labels = []
        
        for category in task_categories.values():
            if category['indices'] and category['colors']:
                patch = plt.Rectangle((0, 0), 1, 1, fc=category['colors'][0], alpha=0.8)
                legend_patches.append(patch)
                legend_labels.append(category['label'])
        
        for holiday in holidays:
            patch = plt.Rectangle((0, 0), 1, 1, fc=holiday['color'], alpha=0.3)
            legend_patches.append(patch)
            legend_labels.append(holiday['name'])
            
        if legend_patches:  # Only add legend if there are items to show
            ax.legend(legend_patches, legend_labels,
                     loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=len(legend_patches))

        # Add text annotations for key dates and durations - MODIFIED SECTION
        plt.figtext(0.02, 0.02, f"Project Start: {start_date.strftime('%b %d, %Y')}", fontsize=10, fontweight='bold')

        # Adjust positions and width to ensure text fits within margins
        if holidays:
            # Add holiday text
            holiday_text = ""
            for i, holiday in enumerate(holidays):
                if i > 0:
                    holiday_text += ", "
                holiday_text += f"{holiday['name']}: {holiday['start'].strftime('%b %d')} - {holiday['end'].strftime('%b %d, %Y')}"
            
            plt.figtext(0.27, 0.02, holiday_text, fontsize=10, fontweight='bold', color='#c0392b')
            plt.figtext(0.54, 0.02, f"Project End: {project_end.strftime('%b %d, %Y')}", fontsize=10, fontweight='bold')
            # Move duration text slightly to the left to ensure it fits
            plt.figtext(0.75, 0.02, f"Total Duration: {total_days} days ({working_days} working days)", 
                    fontsize=10, fontweight='bold', color='#2c3e50')
        else:
            # Center the project end text when no holidays are present
            plt.figtext(0.35, 0.02, f"Project End: {project_end.strftime('%b %d, %Y')}", fontsize=10, fontweight='bold')
            # Move duration text slightly to the left to ensure it fits
            plt.figtext(0.65, 0.02, f"Total Duration: {total_days} days ({working_days} working days)", 
                    fontsize=10, fontweight='bold', color='#2c3e50')

        # Rotate date labels for better readability
        plt.xticks(rotation=45)

        # Adjust layout
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        buf.seek(0)
        
        # Convert to base64 for easy embedding in HTML or JSON
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        # Return JSON with the image and project data
        return jsonify({
            'project_name': project_name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': project_end.strftime('%Y-%m-%d'),
            'total_days': total_days,
            'working_days': working_days,
            'image': image_base64
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download-timeline', methods=['POST'])
def download_timeline():
    try:
        # Generate the timeline image using the same logic as above
        # but return as a downloadable file instead of JSON
        data = request.json
        
        # [Same timeline generation code as in generate_timeline]
        # ...
        
        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        buf.seek(0)
        plt.close()
        
        return send_file(
            buf,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"{data.get('project_name', 'timeline')}.png"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
