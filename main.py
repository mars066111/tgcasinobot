<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Telegram Casino</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--tg-theme-bg-color, #121316);
            color: var(--tg-theme-text-color, #ffffff);
            margin: 0;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .header {
            background: var(--tg-theme-secondary-bg-color, #1e2026);
            border-radius: 14px;
            padding: 15px;
            width: 100%;
            max-width: 380px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            margin-bottom: 15px;
        }
        h1 { margin: 0 0 10px 0; font-size: 20px; color: #f39c12; }
        .balance { font-size: 24px; font-weight: bold; color: #2ecc71; margin-bottom: 10px; }
        .bonus-timer { font-size: 13px; color: #e74c3c; margin-bottom: 8px; }
        .games-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            width: 100%;
            max-width: 380px;
        }
        .game-card {
            background: var(--tg-theme-secondary-bg-color, #1e2026);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .game-card h3 { margin: 0 0 8px 0; font-size: 15px; }
        .btn {
            background-color: var(--tg-theme-button-color, #3498db);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-top: 5px;
        }
        .btn:active { opacity: 0.8; }
        .bonus-btn { background-color: #27ae60; margin-top: 5px; }
    </style>
</head>
<body>

    <div class="header">
        <h1>🎰 Ultimate Casino</h1>
        <div class="balance" id="balance">🪙 1000 монет</div>
        <div class="bonus-timer" id="timerText">Бонус доступен!</div>
        <button class="btn bonus-btn" id="bonusBtn" onclick="claimBonus()">🎁 Забрать бонус (+200)</button>
    </div>

    <div class="games-grid">
        <!-- Кости -->
        <div class="game-card">
            <h3>🎲 Кости</h3>
            <p style="font-size:12px; color:#aaa;">Угадай ≥ 4</p>
            <button class="btn" onclick="playDice()">Играть (50)</button>
        </div>
        <!-- Красное / Черное -->
        <div class="game-card">
            <h3>🔴 Черное / Красное</h3>
            <p style="font-size:12px; color:#aaa;">Шанс 50/50</p>
            <button class="btn" style="background-color: #e74c3c;" onclick="playRedBlack()">Играть (100)</button>
        </div>
        <!-- Больше / Меньше -->
        <div class="game-card">
            <h3>📊 Больше / Меньше</h3>
            <p style="font-size:12px; color:#aaa;">Число от 1 до 100</p>
            <button class="btn" style="background-color: #9b59b6;" onclick="playHighLow()">Играть (75)</button>
        </div>
        <!-- Слоты -->
        <div class="game-card">
            <h3>🎰 Слот-машина</h3>
            <p style="font-size:12px; color:#aaa;">Джекпот x5</p>
            <button class="btn" style="background-color: #f1c40f; color:#000;" onclick="playSlots()">Играть (100)</button>
        </div>
        <!-- Рулетка -->
        <div class="game-card">
            <h3>🎡 Мини-рулетка</h3>
            <p style="font-size:12px; color:#aaa;">Угадай сектор (0-3)</p>
            <button class="btn" style="background-color: #e67e22;" onclick="playRoulette()">Играть (100)</button>
        </div>
        <!-- Монетка -->
        <div class="game-card">
            <h3>🪙 Орёл и Решка</h3>
            <p style="font-size:12px; color:#aaa;">Классика x2</p>
            <button class="btn" style="background-color: #1abc9c;" onclick="playCoinFlip()">Играть (50)</button>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        let balance = 1000;
        let nextBonusTime = Date.now();

        // Таймер бонуса (каждые 10 минут / 600000 мс)
        setInterval(() => {
            let now = Date.now();
            let diff = nextBonusTime - now;
            let btn = document.getElementById('bonusBtn');
            let timerTxt = document.getElementById('timerText');

            if (diff <= 0) {
                timerTxt.innerText = "Бонус доступен!";
                btn.style.display = "block";
            } else {
                let minutes = Math.floor(diff / 60000);
                let seconds = Math.floor((diff % 60000) / 1000);
                timerTxt.innerText = `Следующий бонус через: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                btn.style.display = "none";
            }
        }, 1000);

        function claimBonus() {
            balance += 200;
            nextBonusTime = Date.now() + 10 * 60 * 1000; // 10 минут
            updateDisplay();
            alert('🎁 Вы получили бесплатный бонус 200 монет!');
            tg.HapticFeedback.notificationOccurred('success');
        }

        function updateDisplay() {
            document.getElementById('balance').innerText = `🪙 ${balance} монет`;
        }

        function checkBalance(cost) {
            if (balance < cost) {
                alert('❌ Недостаточно средств! Дождитесь бонуса каждые 10 минут.');
                return false;
            }
            balance -= cost;
            return true;
        }

        // 1. Кости
        function playDice() {
            if (!checkBalance(50)) return;
            let roll = Math.floor(Math.random() * 6) + 1;
            if (roll >= 4) {
                balance += 100;
                alert(`🎉 Выпало ${roll}! Вы выиграли 100 монет!`);
            } else {
                alert(`😢 Выпало ${roll}. Вы проиграли.`);
            }
            updateDisplay();
            tg.HapticFeedback.impactOccurred('medium');
        }

        // 2. Красное / Черное
        function playRedBlack() {
            if (!checkBalance(100)) return;
            let isRed = Math.random() < 0.5;
            if (isRed) {
                balance += 200;
                alert('🔴 Выпало КРАСНОЕ! Вы выиграли 200 монет!');
            } else {
                alert('⚫ Выпало ЧЁРНОЕ. Вы проиграли.');
            }
            updateDisplay();
            tg.HapticFeedback.impactOccurred('medium');
        }

        // 3. Больше / Меньше
        function playHighLow() {
            if (!checkBalance(75)) return;
            let secret = Math.floor(Math.random() * 100) + 1;
            let userChoice = prompt('Угадайте: число больше 50 или нет? Введите "б" (больше) или "м" (меньше):', 'б');
            if (!userChoice) { balance += 75; return; }
            
            let isHigh = secret > 50;
            let userGuessedRight = (userChoice.toLowerCase() === 'б' && isHigh) || (userChoice.toLowerCase() === 'м' && !isHigh);
            
            if (userGuessedRight) {
                balance += 150;
                alert(`🎉 Загаданное число было ${secret}. Вы угадали и выиграли 150 монет!`);
            } else {
                alert(`😢 Загаданное число было ${secret}. Вы проиграли.`);
            }
            updateDisplay();
        }

        // 4. Слоты
        function playSlots() {
            if (!checkBalance(100)) return;
            let win = Math.random() < 0.25;
            if (win) {
                balance += 500;
                alert('🔥 ДЖЕКПОТ! Собралась линия! Вы выиграли 500 монет!');
            } else {
                alert('🎰 Мимо! Барабаны не сошлись.');
            }
            updateDisplay();
            tg.HapticFeedback.notificationOccurred(win ? 'success' : 'error');
        }

        // 5. Рулетка
        function playRoulette() {
            if (!checkBalance(100)) return;
            let sector = Math.floor(Math.random() * 4); // от 0 до 3
            let winSector = Math.floor(Math.random() * 4);
            if (sector === winSector) {
                balance += 400;
                alert(`🎡 Сектор ${sector}! Поздравляем, вы угадали и выиграли 400 монет!`);
            } else {
                alert(`🎡 Выпал сектор ${sector}, а выигрышный был ${winSector}. Вы проиграли.`);
            }
            updateDisplay();
        }

        // 6. Орёл и Решка
        function playCoinFlip() {
            if (!checkBalance(50)) return;
            let win = Math.random() < 0.5;
            if (win) {
                balance += 100;
                alert('🪙 Выпал ОРЁЛ! Вы удвоили ставку и выиграли 100 монет!');
            } else {
                alert('🪙 Выпала РЕШКА. Вы проиграли.');
            }
            updateDisplay();
        }
    </script>
</body>
</html>
