// Ждем полной загрузки DOM, прежде чем выполнять скрипт
document.addEventListener('DOMContentLoaded', () => {

    // -----------------------------------------
    // Подключение к MQTT через WebSocket
    // -----------------------------------------
    const client = mqtt.connect('ws://127.0.0.1:15675', {
        protocolVersion: 5, // Используем MQTT 5.0
        path: '/ws',        // Путь для WebSocket
    });

    // Хранилище данных о сенсорах
    const sensors = {};

    // Ссылка на tbody таблицы, куда будем добавлять строки с данными
    const tbody = document.querySelector('table tbody');

    // -----------------------------------------
    // Callback при успешном подключении к MQTT
    // -----------------------------------------
    client.on('connect', () => {
        // Обновляем статус подключения на странице
        document.getElementById('connect').textContent = 'Connected';

        // Подписка на все топики с температурой
        client.subscribe('temperature/#', { qos: 1 }, (err) => {
            if (err) console.error('Subscribe error:', err);
        });
    });

    // -----------------------------------------
    // Callback при получении сообщения MQTT
    // -----------------------------------------
    client.on('message', (topic, message, packet) => {
        let payload;

        // Пытаемся распарсить JSON из сообщения
        try {
            payload = JSON.parse(message.toString());
        } catch (e) {
            console.error('Failed to parse message payload as JSON:', e);
            return;
        }

        // Извлекаем значение температуры
        const temp = payload.value !== undefined ? String(payload.value) : '--';
        const timestamp = payload.timestamp;

        // Определяем имя сенсора из топика: temperature/<sensor>
        const parts = topic.split('/');
        if (parts.length !== 2) return;
        const sensor = parts[1];

        // Форматируем метку времени в локальное время
        let timeString = '';
        if (timestamp) {
            const tsNum = Number(timestamp);
            if (!isNaN(tsNum)) {
                const dt = new Date(tsNum);
                timeString = dt.toLocaleString();
            }
        }

        // Если сенсор ещё не был добавлен в таблицу, создаем новую строку
        if (!sensors[sensor]) {
            const row = document.createElement('tr');
            row.id = `row-${sensor}`;

            const nameCell = document.createElement('td');
            nameCell.textContent = sensor;

            const tempCell = document.createElement('td');
            tempCell.id = `temp-${sensor}`;
            tempCell.textContent = '--';

            const alertCell = document.createElement('td');
            alertCell.id = `alert-${sensor}`;
            alertCell.textContent = '';

            const timeCell = document.createElement('td');
            timeCell.id = `time-${sensor}`;
            timeCell.textContent = '';

            // Добавляем все ячейки в строку и строку в таблицу
            row.appendChild(nameCell);
            row.appendChild(tempCell);
            row.appendChild(alertCell);
            row.appendChild(timeCell);
            tbody.appendChild(row);

            // Сохраняем ссылку на элементы DOM для последующих обновлений
            sensors[sensor] = {
                lastUpdate: Date.now(),
                elements: { row, tempCell, alertCell, timeCell }
            };
        }

        // Обновляем значения температуры и времени для существующего сенсора
        const { row, tempCell, alertCell, timeCell } = sensors[sensor].elements;
        tempCell.textContent = temp;      // температура
        alertCell.textContent = '';       // очищаем сообщение об алерте
        row.className = 'ok';             // визуальное обозначение "всё ок"
        sensors[sensor].lastUpdate = Date.now();
        timeCell.textContent = timeString; // обновляем время последнего значения
    });

    // -----------------------------------------
    // Периодическая проверка, не устарели ли данные
    // -----------------------------------------
    setInterval(() => {
        const now = Date.now();

        Object.keys(sensors).forEach(sensor => {
            const sensorData = sensors[sensor];
            const diff = now - sensorData.lastUpdate;

            if (diff > 2 * 60 * 1000) {
                // Если данных нет более 2 минут — показываем предупреждение
                sensorData.elements.alertCell.textContent = '⚠️ No data for 2+ minutes!';
                sensorData.elements.row.className = 'alert';
            } else {
                // Данные свежие — всё ок
                sensorData.elements.alertCell.textContent = '✓ OK';
                sensorData.elements.row.className = 'ok';
            }
        });
    }, 10000); // проверяем каждые 10 секунд
});
