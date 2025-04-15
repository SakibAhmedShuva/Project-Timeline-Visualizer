from flask import Flask, request, jsonify, send_file, render_template
import matplotlib
matplotlib.use('Agg')  # Set the backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import io
import base64
import logging # Added for better debugging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

# --- Helper Function to Calculate End Date ---
def calculate_end_date(start, duration, holidays, weekly_holiday):
    """
    Calculates the end date for a task, skipping specified holidays and a weekly holiday.
    Args:
        start (datetime): The start date of the task.
        duration (int): The duration of the task in working days (must be >= 1).
        holidays (list): A list of holiday dictionaries [{'start': dt, 'end': dt}, ...].
        weekly_holiday (int): The day of the week to skip (0=Monday, 6=Sunday).
    Returns:
        datetime: The calculated end date.
    """
    if duration <= 0: # Duration includes the start day
        # Handle zero or negative duration if needed, or raise error
        # For now, assume duration is at least 1
         return start # Or handle as error

    end_date = start
    days_added = 0 # Start day counts as the first day

    # First, check if the start date itself is a holiday or weekly off day
    is_start_holiday = any(h['start'] <= start <= h['end'] for h in holidays)
    is_start_weekly_off = start.weekday() == weekly_holiday

    # If start day is valid, it counts as day 1
    if not is_start_holiday and not is_start_weekly_off:
        days_added = 1

    # Find the remaining days needed
    while days_added < duration:
        end_date += timedelta(days=1)
        is_holiday = any(h['start'] <= end_date <= h['end'] for h in holidays)
        is_weekly_off = end_date.weekday() == weekly_holiday

        if not is_holiday and not is_weekly_off:
            days_added += 1

    return end_date

# --- Helper Function to find next working day ---
def find_next_working_day(start_date, holidays, weekly_holiday):
    """ Finds the next valid working day starting from start_date (inclusive). """
    current_date = start_date
    while True:
        is_holiday = any(h['start'] <= current_date <= h['end'] for h in holidays)
        is_weekly_off = current_date.weekday() == weekly_holiday
        if not is_holiday and not is_weekly_off:
            return current_date
        current_date += timedelta(days=1)


@app.route('/generate-timeline', methods=['POST'])
def generate_timeline():
    try:
        data = request.json
        logging.info(f"Received data: {data}")

        # --- Extract Parameters ---
        project_name = data.get('project_name', 'Project Timeline')
        start_date_str = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        # Default weekly holiday is Friday (4) if not provided by frontend
        weekly_holiday = int(data.get('weekly_holiday', 4)) # 0=Mon, 1=Tue, ..., 6=Sun

        # --- Correctly determine the weekly holiday name ---
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        try:
            correct_weekly_holiday_name = day_names[weekly_holiday]
        except IndexError:
            correct_weekly_holiday_name = "Invalid Day" # Fallback
        # --- End correct name determination ---

        # --- Parse Holidays ---
        holidays = []
        for holiday in data.get('holidays', []):
            try:
                holiday_start = datetime.strptime(holiday.get('start_date'), '%Y-%m-%d')
                holiday_end = datetime.strptime(holiday.get('end_date'), '%Y-%m-%d')
                # Ensure end date is not before start date
                if holiday_end < holiday_start:
                     holiday_end = holiday_start # Treat as single day if invalid range
                holiday_name = holiday.get('name', 'Holiday')
                holiday_color = holiday.get('color', '#ff9999')
                holidays.append({
                    'start': holiday_start,
                    'end': holiday_end,
                    'name': holiday_name,
                    'color': holiday_color
                })
            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping invalid holiday data: {holiday}. Error: {e}")
                continue # Skip invalid holiday entries

        # --- Parse Tasks and Dependencies ---
        tasks_input = data.get('tasks', [])
        if not tasks_input:
             # Add default tasks if none provided (for easier testing)
            tasks_input = [
                {"name": "Riser Works", "duration": 8, "depends_on_index": None},
                {"name": "Riser Pressure Test", "duration": 2, "depends_on_index": 0},
                {"name": "Sprinkler Works", "duration": 10, "depends_on_index": 1},
                {"name": "Sprinkler Pressure Test", "duration": 2, "depends_on_index": 2},
                {"name": "Product Ex Work", "duration": 49, "depends_on_index": None},
                {"name": "Shipped on Board", "duration": 18, "depends_on_index": 4},
                {"name": "Vessel at Chittagong", "duration": 21, "depends_on_index": 5},
                {"name": "Materials from port to site", "duration": 10, "depends_on_index": 6},
                {"name": "Pump Room", "duration": 10, "depends_on_index": 7},
                {"name": "Testing Commissioning & Balancing", "duration": 5, "depends_on_index": 8},
            ]

        tasks = []
        for i, task_data in enumerate(tasks_input):
            name = task_data.get('name', f'Task {i+1}')
            duration = int(task_data.get('duration', 1))
            depends_on_index = task_data.get('depends_on_index')
            # Validate depends_on_index
            if depends_on_index is not None:
                 try:
                     depends_on_index = int(depends_on_index)
                     if not (0 <= depends_on_index < len(tasks_input)):
                         logging.warning(f"Task '{name}' has invalid dependency index {depends_on_index}. Setting to None.")
                         depends_on_index = None
                 except (ValueError, TypeError):
                      logging.warning(f"Task '{name}' has non-integer dependency index {depends_on_index}. Setting to None.")
                      depends_on_index = None

            tasks.append({
                'id': i, # Use index as ID for simplicity
                'name': name,
                'duration': duration,
                'depends_on_index': depends_on_index,
                'start_date': None, # To be calculated
                'end_date': None    # To be calculated
            })

        # --- Calculate Task Dates based on Dependencies ---
        tasks_processed = 0
        max_iterations = len(tasks) * 2 # Safety break for circular dependencies
        iterations = 0

        # Find the actual project start date (first working day on or after requested start)
        actual_project_start_date = find_next_working_day(start_date, holidays, weekly_holiday)

        while tasks_processed < len(tasks) and iterations < max_iterations:
            iterations += 1
            made_progress = False
            for i in range(len(tasks)):
                task = tasks[i]
                if task['start_date'] is not None: # Already processed
                    continue

                dependency_met = False
                calculated_start = actual_project_start_date # Default start if no dependency

                if task['depends_on_index'] is None:
                    dependency_met = True
                else:
                    dep_index = task['depends_on_index']
                    if 0 <= dep_index < len(tasks) and tasks[dep_index]['end_date'] is not None:
                        # Dependency finished, start the day after
                        potential_start = tasks[dep_index]['end_date'] + timedelta(days=1)
                        # Find the next *working* day
                        calculated_start = find_next_working_day(potential_start, holidays, weekly_holiday)
                        dependency_met = True
                    # else: dependency not yet processed, wait

                if dependency_met:
                    task['start_date'] = calculated_start
                    # Duration includes the start day itself
                    task['end_date'] = calculate_end_date(task['start_date'], task['duration'], holidays, weekly_holiday)
                    tasks_processed += 1
                    made_progress = True
                    logging.info(f"Processed task '{task['name']}': {task['start_date'].strftime('%Y-%m-%d')} -> {task['end_date'].strftime('%Y-%m-%d')}")


            if not made_progress and tasks_processed < len(tasks):
                 # Check for unprocessed tasks without met dependencies (potential issue or cycle)
                 unprocessed = [t['name'] for t in tasks if t['start_date'] is None]
                 logging.warning(f"No progress made in iteration {iterations}. Possible circular dependency or issue. Unprocessed: {unprocessed}")
                 # Optionally, break or try to resolve. For now, we break with the max_iterations check.


        if tasks_processed < len(tasks):
             # Not all tasks could be processed - likely a circular dependency
             unprocessed_tasks = [t['name'] for t in tasks if t['start_date'] is None]
             error_msg = f"Could not process all tasks, possible circular dependency. Unprocessed: {', '.join(unprocessed_tasks)}"
             logging.error(error_msg)
             # Return an error or proceed with processed tasks? Let's return error for clarity.
             return jsonify({'error': error_msg}), 400


        # --- Calculate Project End Date and Durations ---
        if not tasks or not any(t['end_date'] for t in tasks):
             project_end = actual_project_start_date # Handle case with no tasks
        else:
            project_end = max(t['end_date'] for t in tasks if t['end_date'] is not None)

        total_days = (project_end - actual_project_start_date).days + 1 # Calendar days

        # Calculate actual working days (excluding holidays AND weekly holiday)
        working_days = 0
        if total_days > 0: # Avoid unnecessary loops if duration is 0 or less
            current = actual_project_start_date
            while current <= project_end:
                is_holiday = any(h['start'] <= current <= h['end'] for h in holidays)
                is_weekly_off = current.weekday() == weekly_holiday
                if not is_holiday and not is_weekly_off:
                    working_days += 1
                current += timedelta(days=1)

        # --- Plotting ---
        fig, ax = plt.subplots(figsize=(15, max(8, len(tasks) * 0.6))) # Adjust height based on tasks

        # Task categories and colors (Simplified - apply color cyclically or based on some logic if needed)
        # Example: cycle through a predefined list of colors
        plot_colors = ['#3498db', '#e74c3c', '#1abc9c', '#9b59b6', '#f1c40f',
                       '#2ecc71', '#e67e22', '#34495e', '#16a085', '#d35400']
        num_colors = len(plot_colors)

        task_names = [t['name'] for t in tasks]

        # Plotting each task as a bar
        plotted_indices = [] # Keep track of y-positions used
        for i, task in enumerate(tasks):
            if task['start_date'] is None or task['end_date'] is None:
                logging.warning(f"Skipping plotting task '{task['name']}' as dates were not calculated.")
                continue

            start_num = mdates.date2num(task['start_date'])
            end_num = mdates.date2num(task['end_date'])
            # duration_days = (task['end_date'] - task['start_date']).days + 1 # Recalculate for plotting width - Not needed for barh

            # Use barh with numeric dates; width is end_num - start_num + 1 (to include the end day)
            ax.barh(i, end_num - start_num + 1, left=start_num, height=0.6, align='center',
                    color=plot_colors[i % num_colors], alpha=0.85, edgecolor='black', label=task['name'] if i < 5 else "") # Label only first few to avoid clutter

            # Add duration text inside the bar
            text_x_num = start_num + (end_num - start_num + 1) / 2
            ax.text(mdates.num2date(text_x_num), i, f"{task['duration']}d", # Use original task duration
                    ha='center', va='center', color='white', fontweight='bold',
                    fontsize=9, bbox=dict(facecolor=plot_colors[i % num_colors], alpha=0.9, boxstyle="round,pad=0.2",edgecolor='none'))
            plotted_indices.append(i)


        # --- Add Holiday Period Indications ---
        if holidays and plotted_indices:
            min_y_axis, max_y_axis = ax.get_ylim() # Get current y-limits
            min_plotted_y, max_plotted_y = min(plotted_indices), max(plotted_indices)
            # Calculate relative positions for axvspan
            y_min_rel = (min_plotted_y - 0.5 - min_y_axis) / (max_y_axis - min_y_axis)
            y_max_rel = (max_plotted_y + 0.5 - min_y_axis) / (max_y_axis - min_y_axis)

            legend_added = set() # Avoid duplicate holiday legends
            for holiday in holidays:
                h_start_num = mdates.date2num(holiday['start'])
                h_end_num = mdates.date2num(holiday['end'])
                # Draw vertical span covering the plotted task area
                # Add 1 to end_num because axvspan excludes the endpoint date visually
                ax.axvspan(h_start_num, h_end_num + 1, ymin=y_min_rel, ymax=y_max_rel,
                           color=holiday['color'], alpha=0.2, zorder=-1) # Behind tasks

                # Optionally add vertical lines at start/end
                ax.axvline(x=h_start_num, color=holiday['color'], linestyle=':', alpha=0.6, linewidth=1)
                ax.axvline(x=h_end_num+1, color=holiday['color'], linestyle=':', alpha=0.6, linewidth=1)

                # Add to legend only once per name
                if holiday['name'] not in legend_added:
                     # Create dummy patch for legend (can be used if needed)
                     # patch = plt.Rectangle((0, 0), 1, 1, fc=holiday['color'], alpha=0.3)
                     legend_added.add(holiday['name'])

        # --- Formatting ---
        ax.set_yticks(range(len(tasks)))
        ax.set_yticklabels(task_names, fontsize=10)
        ax.invert_yaxis() # Tasks top-to-bottom

        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Tasks', fontsize=12, fontweight='bold')
        ax.set_title(f'{project_name} - Timeline', fontsize=16, fontweight='bold')

        # Format dates on x-axis
        date_format = mdates.DateFormatter('%b %d, %Y')
        ax.xaxis.set_major_formatter(date_format)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1)) # Major ticks weekly
        ax.xaxis.set_minor_locator(mdates.DayLocator()) # Minor ticks daily

        ax.grid(True, axis='x', linestyle='--', alpha=0.6, which='major') # Grid lines for weeks
        ax.grid(True, axis='x', linestyle=':', alpha=0.3, which='minor') # Fainter grid lines for days

        # Set x-axis limits with padding
        if tasks and any(t['start_date'] for t in tasks):
            plot_start_date = min(t['start_date'] for t in tasks if t['start_date'] is not None)
            plot_end_date = project_end
            ax.set_xlim(plot_start_date - timedelta(days=2), plot_end_date + timedelta(days=2))
        else: # Handle empty timeline case
            ax.set_xlim(actual_project_start_date - timedelta(days=2), actual_project_start_date + timedelta(days=10))


        # Set y-axis limits (if tasks exist)
        if plotted_indices:
            ax.set_ylim(max(plotted_indices) + 0.5, min(plotted_indices) - 0.5) # Inverted axis
        else:
             ax.set_ylim(0.5, -0.5) # Handle empty case

        # Set background color
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#ffffff')

        # Add Legend (Consider placing it outside plot area if too cluttered)
        # handles, labels = ax.get_legend_handles_labels() # Get labels from barh plots if used
        # if handles:
        #    ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(5, len(handles)))

        # --- Add text annotations for key info ---
        plt.figtext(0.02, 0.03, f"Start: {actual_project_start_date.strftime('%b %d, %Y')}", fontsize=9, fontweight='bold')
        plt.figtext(0.30, 0.03, f"End: {project_end.strftime('%b %d, %Y')}", fontsize=9, fontweight='bold')
        plt.figtext(0.60, 0.03, f"Duration: {total_days} Cal. Days", fontsize=9, fontweight='bold', color='#2c3e50')
        # CORRECTED: Use the correct holiday name in the plot annotation
        plt.figtext(0.80, 0.03, f"Work Days: {working_days} ({correct_weekly_holiday_name} Off)", fontsize=9, fontweight='bold', color='#2c3e50')


        # Rotate date labels for better readability
        plt.xticks(rotation=30, ha='right')

        # Adjust layout
        plt.tight_layout(rect=[0, 0.06, 1, 0.96]) # Adjust bottom margin for figtext

        # --- Save and Return ---
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200) # Lower DPI slightly if performance is an issue
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig) # Close the figure to free memory

        # CORRECTED: Return the correct holiday name in the JSON response
        return jsonify({
            'project_name': project_name,
            'start_date': actual_project_start_date.strftime('%Y-%m-%d'), # Return actual start
            'end_date': project_end.strftime('%Y-%m-%d'),
            'total_days': total_days,
            'working_days': working_days,
            'image': image_base64,
            'weekly_holiday': weekly_holiday, # Keep the integer value
            'weekly_holiday_name': correct_weekly_holiday_name # Use the correct name
        })

    except ValueError as ve:
         logging.error(f"Value error: {ve}")
         return jsonify({'error': f'Invalid input data: {ve}'}), 400
    except Exception as e:
        logging.exception("An error occurred during timeline generation:") # Log full traceback
        return jsonify({'error': f'An internal error occurred: {e}'}), 500


# --- Download Route (Refactored to reuse generation logic) ---
@app.route('/download-timeline', methods=['POST'])
def download_timeline():
    try:
        # Re-generate the image based on the same POST data to get the buffer.
        # Note: In a production app, caching the result or having JS send
        # the generated image data might be more efficient.

        # Calling generate_timeline() returns a Flask Response object.
        # We need to get the JSON data from it if it's successful.
        response = generate_timeline() # This executes the endpoint logic again

        if response.status_code != 200:
            # If generation failed, return the error response directly
            return response

        # If generation succeeded, get the JSON data from the response
        response_data = response.get_json()
        image_base64 = response_data.get('image')

        if not image_base64:
            logging.error("Image data not found in regeneration response for download.")
            return jsonify({'error': 'Failed to retrieve generated image for download.'}), 500

        # Decode the base64 image
        image_bytes = base64.b64decode(image_base64)
        buf = io.BytesIO(image_bytes)
        buf.seek(0)

        # Use the project name from the original request data for the filename
        project_name = request.json.get('project_name', 'timeline')
        # Sanitize filename
        safe_filename = "".join([c for c in project_name if c.isalnum() or c in (' ', '_', '-')]).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        if not safe_filename: # Handle empty project name case
            safe_filename = 'timeline'

        return send_file(
            buf,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"{safe_filename}.png"
        )

    except Exception as e:
        logging.exception("An error occurred during timeline download:")
        # Try to return a JSON error if possible
        return jsonify({'error': f'An internal error occurred during download: {e}'}), 500

if __name__ == '__main__':
    # Use Gunicorn or Waitress in production instead of Flask's built-in server
    # Example: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=True, host='0.0.0.0', port=5000) # debug=True is NOT for production