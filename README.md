# Project Timeline Visualizer

Thank you for providing the GitHub repository link. Here's professional documentation for your Project Timeline Visualizer repository:

## Project Timeline Visualizer

A professional web application for creating, visualizing, and managing project timelines with support for tasks, dependencies, holidays, and resource allocation.

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue.svg)](https://github.com/SakibAhmedShuva/Project-Timeline-Visualizer)

## Overview

Project Timeline Visualizer is a powerful web application that enables project managers, teams, and stakeholders to create detailed visual timelines for projects of any size. The application offers an intuitive interface for defining tasks, setting dependencies, marking holidays, and visualizing the complete project schedule with professional-grade Gantt charts.


![image](https://github.com/user-attachments/assets/271aaf6d-774d-487f-8b24-cb916c2d27f7)


![image](https://github.com/user-attachments/assets/b89b340e-7cf0-4e4c-874d-fb67713b9e99)


## Key Features

- **Interactive Task Management**: Add, edit, reorder, and delete tasks with drag-and-drop functionality
- **Dependency Handling**: Define sequential task groups and task dependencies
- **Holiday Integration**: Mark holidays and non-working periods with custom colors
- **Dynamic Timeline Generation**: Real-time timeline visualization with task durations
- **Professional Exports**: Download high-resolution timeline images for reports and presentations
- **Responsive Design**: Works seamlessly across desktop and mobile devices

## Technical Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Backend**: Python with Flask framework
- **Data Visualization**: Matplotlib for timeline generation
- **Interactivity**: SortableJS for drag-and-drop functionality

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

1. **Configure Project Details**: 
   - Set your project name
   - Select a start date for your project

2. **Add Tasks**: 
   - Enter task names and their durations in days
   - Use drag-and-drop to reorder tasks
   - Edit or delete tasks as needed

3. **Define Holidays**: 
   - Mark non-working periods with custom names
   - Set start and end dates for holidays
   - Assign custom colors to distinguish different holiday types

4. **Generate Timeline**: 
   - Click "Generate Timeline" to create your visualization
   - View task dependencies and critical path

5. **Export or Share**: 
   - Download the timeline as a high-resolution image
   - Share directly from the application

## API Documentation

### POST `/generate-timeline`

Generates a timeline visualization based on provided project data.

**Request Body:**
```json
{
  "project_name": "Fire Protection System Installation",
  "start_date": "2025-03-25",
  "tasks": [
    {"name": "Riser Works", "duration": 8},
    {"name": "Riser Pressure Test", "duration": 2},
    {"name": "Sprinkler Works", "duration": 10}
  ],
  "holidays": [
    {
      "name": "Eid Holiday",
      "start_date": "2025-04-01",
      "end_date": "2025-04-07",
      "color": "#ff9999"
    }
  ],
  "dependencies": {
    "sequential_groups": [
      {"start_idx": 0, "end_idx": 2}
    ],
    "dependent_tasks": [
      {"idx": 2, "depends_on_idx": 1}
    ]
  }
}
```

**Response:**
```json
{
  "project_name": "Fire Protection System Installation",
  "start_date": "2025-03-25",
  "end_date": "2025-05-15",
  "total_days": 52,
  "working_days": 45,
  "image": "base64_encoded_image_data"
}
```

### POST `/download-timeline`

Downloads the generated timeline as a PNG image file.

## Future Enhancements

- Resource allocation and management
- Multiple timeline views (Gantt, calendar, list)
- Collaborative editing and sharing
- Timeline templates for common project types
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

## Contact

Sakib Ahmed Shuva - [GitHub Profile](https://github.com/SakibAhmedShuva)

Project Link: [https://github.com/SakibAhmedShuva/Project-Timeline-Visualizer](https://github.com/SakibAhmedShuva/Project-Timeline-Visualizer)

---

*Project Timeline Visualizer - Transform your project planning with professional timeline visualization*
