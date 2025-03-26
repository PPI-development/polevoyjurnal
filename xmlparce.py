from flask import Flask, request
import os
import logging

# Настройка приложения Flask
app = Flask(__name__)
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))

# Логирование
logging.basicConfig(level=logging.INFO)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'xml_file' not in request.files:
        return "XML-файл не найден в запросе", 400

    xml_file = request.files['xml_file']
    xml_file_name = os.path.splitext(xml_file.filename)[0]
    report_folder = os.path.join(UPLOAD_FOLDER, xml_file_name)

    # Создаём папку для отчёта
    os.makedirs(report_folder, exist_ok=True)

    # Сохраняем XML-файл
    xml_file_path = os.path.join(report_folder, xml_file.filename)
    xml_file.save(xml_file_path)
    logging.info(f"XML-файл сохранён: {xml_file_path}")

    # Сохраняем фотографии
    if 'photos' in request.files:
        for photo in request.files.getlist('photos'):
            photo_path = os.path.join(report_folder, photo.filename)
            photo.save(photo_path)
            logging.info(f"Фото сохранено: {photo_path}")

    return f"Все файлы для отчёта '{xml_file_name}' успешно сохранены!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
