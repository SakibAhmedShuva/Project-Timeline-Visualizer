# Project Timeline Visualizer

A professional web application for creating, visualizing, and managing project timelines with intelligent handling of task dependencies, holidays, and weekly off days.

## Overview

Project Timeline Visualizer is a powerful web application built for project managers, teams, and stakeholders to create detailed visual timelines. The application intelligently calculates project durations by accounting for dependencies between tasks, designated holidays, and weekly off days, producing professional Gantt charts for clear visualization.

![image](https://github.com/user-attachments/assets/271aaf6d-774d-487f-8b24-cb916c2d27f7)


![image](https://github.com/user-attachments/assets/b89b340e-7cf0-4e4c-874d-fb67713b9e99)

## Key Features

- **Smart Task Management**: Define tasks with names and durations
- **Dependency Chains**: Create complex task dependencies where tasks start only after their prerequisites are completed
- **Holiday Integration**: Mark specific holiday periods with custom names and colors
- **Weekly Off Day Support**: Set organization-wide weekly holidays (e.g., Friday, Sunday)
- **Intelligent Timeline Calculation**: Automatically calculates start and end dates, respecting all dependencies and non-working days
- **Professional Visualization**: Generate clear, professional-grade Gantt charts with task durations
- **Export Functionality**: Download high-resolution timeline images for reports and presentations

## Technical Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python with Flask framework
- **Data Visualization**: Matplotlib for professional timeline generation
- **Date Processing**: Custom algorithms for handling working days, holidays, and dependencies

## Installation and Setup

```bash
# Clone the repository
git clone https://github.com/SakibAhmedShuva/Project-Timeline-Visualizer.git
cd Project-Timeline-Visualizer

# Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask matplotlib numpy

# Run the application
python app.py
```

The application will be available at http://localhost:5000

## Usage Guide

1. **Set Project Details**: 
   - Enter your project name
   - Select a start date
   - Choose which day of the week is your organization's weekly holiday

2. **Define Tasks**: 
   - Add tasks with names and durations in working days
   - Establish dependencies by selecting which task each new task depends on

3. **Add Holidays**: 
   - Specify holiday periods with names, start and end dates
   - Assign custom colors to visually distinguish different holiday types

4. **Generate Timeline**: 
   - Click "Generate Timeline" to calculate and visualize your project schedule
   - The system automatically accounts for all dependencies, holidays, and weekly off days

5. **Export**: 
   - Download the generated timeline as a high-resolution PNG image for reporting and presentations

## API Documentation

### POST `/generate-timeline`

Generates a timeline visualization based on provided project data, accounting for dependencies, holidays, and weekly off days.

**Request Body:**
```json
{
  "project_name": "Fire Protection System Installation",
  "start_date": "2025-03-25",
  "weekly_holiday": 4,
  "tasks": [
    {"name": "Riser Works", "duration": 8, "depends_on_index": null},
    {"name": "Riser Pressure Test", "duration": 2, "depends_on_index": 0},
    {"name": "Sprinkler Works", "duration": 10, "depends_on_index": 1}
  ],
  "holidays": [
    {
      "name": "Eid Holiday",
      "start_date": "2025-04-01",
      "end_date": "2025-04-07",
      "color": "#ff9999"
    }
  ]
}
```

**Response:**
```json
{
  "project_name": "Fire Protection System Installation",
  "start_date": "2025-03-25",
  "end_date": "2025-04-25",
  "total_days": 32,
  "working_days": 22,
  "image": "base64_encoded_image_data",
  "weekly_holiday": 4,
  "weekly_holiday_name": "Friday"
}
```

### POST `/download-timeline`

Downloads the generated timeline as a PNG image file with the project name as the filename.

## How the Timeline Logic Works

The application implements sophisticated algorithms to:

1. **Calculate Working Days**: Accounts for weekly holidays and special holiday periods
2. **Handle Dependencies**: Tasks start on the first working day after their dependencies are completed
3. **Skip Non-Working Days**: Automatically shifts task schedules to skip holidays and weekly off days
4. **Detect Circular Dependencies**: Prevents infinite loops by identifying circular task references

## Future Enhancements

- Resource allocation and management
- Multiple timeline views (Gantt, calendar, list)
- Collaborative editing and sharing
- Timeline templates for common project types
- Export to additional formats (PDF, SVG)
- Integration with project management tools

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
