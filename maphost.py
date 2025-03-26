from flask import Flask, render_template, jsonify, request
import os
import xml.etree.ElementTree as ET
import base64
from datetime import datetime
import argparse

app = Flask(__name__)


# Функция для загрузки отчетов из XML-файлов
def load_reports():
    reports = []
    current_dir = os.getcwd()

    for folder_name in os.listdir(current_dir):
        folder_path = os.path.join(current_dir, folder_name)

        if os.path.isdir(folder_path) and folder_name.startswith('report_'):
            xml_file = next((f for f in os.listdir(folder_path) if f.endswith('.xml')), None)

            if xml_file:
                xml_path = os.path.join(folder_path, xml_file)
                try:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()

                    # Читаем дату из XML
                    raw_date = root.findtext(".//Date", "Unknown Date")

                    # Конвертируем дату в формат YYYY-MM-DD
                    try:
                        parsed_date = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
                    except ValueError:
                        parsed_date = "Unknown Date"

                    report_data = {
                        'id': folder_name,
                        'activity_type': root.findtext(".//ActivityType", "Unknown Activity Type"),
                        'work_place': root.findtext(".//WorkPlace", "Unknown Work Place"),
                        'development_stage': root.findtext(".//DevelopmentStage", "Unknown Development Stage"),
                        'farm_name': root.findtext(".//FarmName", "Unknown Farm Name"),
                        'latitude': root.findtext(".//Latitude", "0.0"),
                        'longitude': root.findtext(".//Longitude", "0.0"),
                        'date': parsed_date,  # Фиксируем формат даты
                        'work_type': root.findtext(".//WorkType", "Unknown WorkType"),
                        'executor': root.findtext(".//Executor", "Unknown Executor"),
                        'culture': root.findtext(".//Culture", "Unknown Culture"),
                        'region': root.findtext(".//Region", "Unknown Region"),
                        'district': root.findtext(".//District", "Unknown District"),
                        'area': root.findtext(".//Area", "Unknown Area"),
                        'description': root.findtext(".//Description", "No Description"),
                        'results': root.findtext(".//Results", "No Results"),
                        "dynamic_fields": {},
                        'photos': [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png'))],
                        'folder_path': folder_path
                    }
                    for field in root.findall(".//DynamicFieldsData/Field"):
                        field_name = field.attrib.get('name', 'Unknown Field')
                        field_value = field.text or 'Нет данных'
                        report_data['dynamic_fields'][field_name] = field_value

                    reports.append(report_data)
                except ET.ParseError as e:
                    print(f"Ошибка разбора XML-файла в {folder_name}: {e}")
    return reports


@app.route('/')
def index():
    reports = load_reports()

    # Создание фильтров
    filters = {
        'dates': sorted(set(report['date'] for report in reports if report['date'] != "Unknown Date")),
        'regions': sorted(set(report['region'] for report in reports if report['region'] != "Unknown Region")),
        'activity_types': sorted(
            set(report['activity_type'] for report in reports if report['activity_type'] != "Unknown Activity Type")),
        'work_types': sorted(
            set(report['work_type'] for report in reports if report['work_type'] != "Unknown WorkType")),
    }

    return render_template('index.html', reports=reports, filters=filters)


# API для получения детальной информации об отчете
@app.route('/get_report/<report_id>')
def get_report(report_id):
    report = next((r for r in load_reports() if r['id'] == report_id), None)
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    # Кодирование фото в base64
    photos_encoded = []
    for photo in report['photos']:
        photo_path = os.path.join(report['folder_path'], photo)
        with open(photo_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            photos_encoded.append(f"data:image/jpeg;base64,{encoded_string}")

    report['photos'] = photos_encoded
    return jsonify(report)


# API для получения статистики по отчетам
@app.route('/get_statistics', methods=['POST'])
def get_statistics():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'Нужно указать начальную и конечную дату'}), 400

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400

    reports = load_reports()
    statistics = {}

    for report in reports:
        report_date = report['date']
        if report_date == "Unknown Date":
            continue

        try:
            report_datetime = datetime.strptime(report_date, "%Y-%m-%d")
            if start_date <= report_datetime <= end_date:
                statistics[report_date] = statistics.get(report_date, 0) + 1
        except ValueError:
            continue

    return jsonify(statistics)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="jurnal")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("FLASK_PORT", 5000)),
        help="Порт для запуска сервера",
    )
    args = parser.parse_args()
    app.run(host="0.0.0.0", port=args.port, debug=True)
