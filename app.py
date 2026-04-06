from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import random
import requests
import threading
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'rpg-game-secret-key-2024'
CORS(app)

# ============ НАСТРОЙКИ DONATIONALERTS ============
DA_CLIENT_ID = "18475"
DA_CLIENT_SECRET = "C6qEYM6eRHeSGGIjEzXzOzWSZ3ZNWD6tsokDnEMg"
DA_REDIRECT_URI = "https://rpg-backend-uch9.onrender.com/api/donate/callback"

# Хранилище токенов (в реальном проекте - БД)
user_tokens = {}  # session_id -> access_token
donation_alerts_token = None  # глобальный токен приложения

# ============ КЛАСС ПЕРСОНАЖА ============
class RPGCharacter:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.level = 1
        self.exp = 0
        self.max_exp = 100
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.attack = 15
        self.defense = 10
        self.agility = 20
        self.gold = 50
        self.odm_gear = False
        self.gas_level = 100
        self.blades_count = 6
        self.inventory = ["Зелье здоровья", "Простой меч"]
        self.location = "Стена Мария"
        self.quests = {}
        self.titan_kills = {}
        self.last_rest = None
        self.last_training = None
        self.daily_reward = None
        self.mikasa_relationship = 0
        self.mikasa_level = 0
        self.has_companion = False
    
    def to_dict(self):
        return {
            "user_id": self.user_id, "name": self.name, "level": self.level,
            "exp": self.exp, "max_exp": self.max_exp, "health": self.health,
            "max_health": self.max_health, "energy": self.energy, "max_energy": self.max_energy,
            "attack": self.attack, "defense": self.defense, "agility": self.agility,
            "gold": self.gold, "odm_gear": self.odm_gear, "gas_level": self.gas_level,
            "blades_count": self.blades_count, "inventory": self.inventory, "location": self.location,
            "quests": self.quests, "titan_kills": self.titan_kills,
            "mikasa_relationship": self.mikasa_relationship, "mikasa_level": self.mikasa_level,
            "has_companion": self.has_companion
        }
    
    def can_rest(self):
        if not self.last_rest: return True
        return datetime.now() - self.last_rest > timedelta(minutes=5)
    
    def rest(self):
        self.health = self.max_health
        self.energy = self.max_energy
        if self.odm_gear:
            self.gas_level = 100
            self.blades_count = 6
        self.last_rest = datetime.now()
        return True
    
    def can_train(self):
        if not self.last_training: return True
        return datetime.now() - self.last_training > timedelta(seconds=10)
    
    def can_get_daily(self):
        if not self.daily_reward: return True
        return datetime.now() - self.daily_reward > timedelta(hours=24)

# Данные титанов
TITANS = {
    "Обычный титан": {"здоровье": 40, "атака": 8, "защита": 5, "награда": (20, 30), "слабое_место": "Шея", "описание": "15-метровый титан"},
    "Аномальный титан": {"здоровье": 80, "атака": 15, "защита": 8, "награда": (50, 70), "слабое_место": "Глаза", "описание": "Быстрый титан"},
    "Звероподобный титан": {"здоровье": 150, "атака": 25, "защита": 15, "награда": (100, 150), "слабое_место": "Спина", "описание": "Звероподобный титан"},
    "Броня Титана": {"здоровье": 500, "атака": 40, "защита": 50, "награда": (300, 500), "слабое_место": "Суставы", "босс": True, "описание": "БРОНЯ ТИТАНА"},
    "Колоссальный титан": {"здоровье": 800, "атака": 60, "защита": 30, "награда": (500, 800), "слабое_место": "Шея", "босс": True, "описание": "КОЛОССАЛЬНЫЙ ТИТАН"},
    "Дракон": {"здоровье": 1000, "атака": 70, "защита": 40, "награда": (1000, 1500), "слабое_место": "Сердце", "босс": True, "описание": "ДРЕВНИЙ ДРАКОН"}
}

# Локации
LOCATIONS = {
    "Стена Мария": {"description": "🏛️ СТЕНА МАРИЯ"},
    "Стена Роза": {"description": "🏛️ СТЕНА РОЗА"},
    "Стена Сина": {"description": "🏛️ СТЕНА СИНА"},
    "За стеной": {"description": "🌲 ТИТАНИЧЕСКИЙ ЛЕС"},
    "Казармы": {"description": "⚔️ КАЗАРМЫ"},
    "Тренировочная площадка": {"description": "🎯 ТРЕНИРОВОЧНАЯ ПЛОЩАДКА"},
    "Торговый район": {"description": "🛒 ТОРГОВЫЙ РАЙОН"},
    "Магазин оружия": {"description": "⚔️ МАГАЗИН ОРУЖИЯ"},
    "Аптека": {"description": "❤️ АПТЕКА"},
    "Магазин ODM": {"description": "⚡ МАГАЗИН ODM"},
    "Черный рынок": {"description": "🛒 ЧЕРНЫЙ РЫНОК"},
    "Центральная площадь": {"description": "🏙️ ЦЕНТРАЛЬНАЯ ПЛОЩАДЬ"},
    "Таверна": {"description": "🍺 ТАВЕРНА"},
    "Госпиталь": {"description": "🏥 ГОСПИТАЛЬ"},
    "Лаборатория": {"description": "🔬 ЛАБОРАТОРИЯ"},
    "Королевский дворец": {"description": "👑 КОРОЛЕВСКИЙ ДВОРЕЦ"},
    "Рынок Сины": {"description": "💰 РЫНОК СИНЫ"},
    "Храм воинов": {"description": "🛐 ХРАМ ВОИНОВ"},
    "Дом Аккерманов": {"description": "🏠 ДОМ АККЕРМАНОВ"},
    "Боссы": {"description": "⚔️ ВЫБОР БОССА"}
}

players = {}
battles = {}

# ============ ДОНАТ-СИСТЕМА ============

player_diamonds = {}
player_privileges = {}

PRIVILEGES_SHOP = {
    "green_nick": {"name": "💚 Зеленый ник в чате", "price": 50, "duration": 30, "badge": "💚", "color": "#88ff88"},
    "silver_nick": {"name": "⭐ Серебряный ник + бейдж", "price": 150, "duration": 30, "badge": "⭐", "color": "#c0c0c0"},
    "gold_nick": {"name": "👑 Золотой ник + бейдж", "price": 300, "duration": 30, "badge": "👑", "color": "#ffd700"},
    "rainbow_nick": {"name": "🌈 Радужный ник", "price": 500, "duration": 30, "badge": "🌈", "color": "rainbow"}
}

DIAMOND_RATES = {100: 100, 300: 330, 500: 600, 1000: 1300}
pending_donations = {}

# ============ API ДОНАТА ============

@app.route('/api/donate/auth', methods=['GET'])
def donate_auth():
    """Начало OAuth авторизации DonationAlerts"""
    auth_url = f"https://www.donationalerts.com/oauth/authorize?client_id={DA_CLIENT_ID}&redirect_uri={DA_REDIRECT_URI}&response_type=code&scope=oauth-donation-subscribe+oauth-user-show"
    return redirect(auth_url)

@app.route('/api/donate/callback', methods=['GET'])
def donate_callback():
    """Callback после авторизации"""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"})
    
    # Обмен кода на токен
    token_url = "https://www.donationalerts.com/oauth/token"
    data = {
        "client_id": DA_CLIENT_ID,
        "client_secret": DA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": DA_REDIRECT_URI
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        global donation_alerts_token
        donation_alerts_token = access_token
        print(f"✅ Получен токен DonationAlerts: {access_token[:20]}...")
        
        # Запускаем слушатель донатов
        start_donation_listener()
        
        return jsonify({"success": True, "message": "DonationAlerts подключен!"})
    else:
        return jsonify({"error": "Failed to get token"})

@app.route('/api/donate/create', methods=['POST'])
def create_donation():
    data = request.json
    session_id = data.get('session_id')
    amount = data.get('amount')
    
    if not session_id or session_id not in players:
        return jsonify({"error": "Сначала создайте персонажа"})
    
    player = players[session_id]
    diamonds = DIAMOND_RATES.get(amount, amount)
    donation_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
    
    pending_donations[donation_id] = {
        "session_id": session_id,
        "player_name": player.name,
        "amount": amount,
        "diamonds": diamonds,
        "created": datetime.now()
    }
    
    donation_url = f"https://www.donationalerts.com/r/dfg45?amount={amount}&custom={donation_id}"
    
    return jsonify({
        "success": True,
        "donation_url": donation_url,
        "amount": amount,
        "diamonds": diamonds,
        "donation_id": donation_id
    })

def start_donation_listener():
    """Запуск слушателя донатов через WebSocket"""
    if not donation_alerts_token:
        print("⚠️ Нет токена DonationAlerts")
        return
    
    def listen():
        import websocket
        import json
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get('type') == 'donation':
                    don_data = data.get('data', {})
                    custom = don_data.get('custom', '')
                    amount = don_data.get('amount', 0)
                    username = don_data.get('username', '')
                    
                    if custom in pending_donations:
                        donation = pending_donations[custom]
                        session_id = donation["session_id"]
                        diamonds = donation["diamonds"]
                        player_diamonds[session_id] = player_diamonds.get(session_id, 0) + diamonds
                        del pending_donations[custom]
                        print(f"💎 Донат от {username}: {amount}₽ → +{diamonds} алмазов!")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        def on_open(ws):
            # Авторизация на WebSocket
            auth_msg = json.dumps({
                "type": "oauth",
                "token": donation_alerts_token
            })
            ws.send(auth_msg)
            print("🔗 WebSocket DonationAlerts подключен")
        
        websocket_url = "wss://centrifugo.donationalerts.com/connection/websocket"
        ws = websocket.WebSocketApp(websocket_url, on_open=on_open, on_message=on_message)
        
        while True:
            try:
                ws.run_forever()
            except Exception as e:
                print(f"WebSocket ошибка: {e}")
            time.sleep(5)
    
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()

@app.route('/api/donate/test/<donation_id>', methods=['GET'])
def test_donation(donation_id):
    """Тестовый эндпоинт для имитации оплаты (без реальных денег)"""
    if donation_id not in pending_donations:
        return jsonify({"error": "Донат не найден"})
    
    donation = pending_donations[donation_id]
    session_id = donation["session_id"]
    diamonds = donation["diamonds"]
    player_diamonds[session_id] = player_diamonds.get(session_id, 0) + diamonds
    del pending_donations[donation_id]
    
    return jsonify({
        "success": True,
        "message": f"✨ Тестовый донат! Начислено {diamonds} алмазов!",
        "diamonds": diamonds
    })

@app.route('/api/diamonds/get', methods=['POST'])
def get_diamonds():
    data = request.json
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"error": "Сессия не найдена"})
    diamonds = player_diamonds.get(session_id, 0)
    return jsonify({"diamonds": diamonds})

@app.route('/api/privileges/list', methods=['GET'])
def list_privileges():
    return jsonify({"privileges": PRIVILEGES_SHOP})

@app.route('/api/privileges/buy', methods=['POST'])
def buy_privilege():
    data = request.json
    session_id = data.get('session_id')
    privilege_type = data.get('privilege_type')
    
    if not session_id:
        return jsonify({"error": "Сессия не найдена"})
    if privilege_type not in PRIVILEGES_SHOP:
        return jsonify({"error": "Привилегия не найдена"})
    
    privilege = PRIVILEGES_SHOP[privilege_type]
    current_diamonds = player_diamonds.get(session_id, 0)
    
    if current_diamonds < privilege["price"]:
        return jsonify({"error": f"Недостаточно алмазов! Нужно {privilege['price']}"})
    
    player_diamonds[session_id] = current_diamonds - privilege["price"]
    expires = datetime.now() + timedelta(days=privilege["duration"])
    player_privileges[session_id] = {
        "type": privilege_type,
        "expires": expires,
        "badge": privilege["badge"],
        "color": privilege["color"],
        "name": privilege["name"]
    }
    
    return jsonify({
        "success": True,
        "message": f"🎉 Привилегия '{privilege['name']}' активирована!",
        "diamonds": player_diamonds[session_id],
        "privilege": player_privileges[session_id]
    })

@app.route('/api/privileges/status', methods=['POST'])
def get_privilege_status():
    data = request.json
    session_id = data.get('session_id')
    player_name = data.get('player_name')
    
    privilege = None
    for sid, priv in player_privileges.items():
        if sid == session_id:
            if priv["expires"] > datetime.now():
                privilege = priv
            else:
                del player_privileges[sid]
            break
    
    if not privilege and player_name:
        for sid, priv in player_privileges.items():
            if sid in players and players[sid].name == player_name:
                if priv["expires"] > datetime.now():
                    privilege = priv
                break
    
    return jsonify({"privilege": privilege})

# ============ ОСНОВНЫЕ API ============

@app.route('/api/create', methods=['POST'])
def create_character():
    data = request.json
    name = data.get('name', 'Боец')
    session_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
    players[session_id] = RPGCharacter(session_id, name)
    return jsonify({"success": True, "player": players[session_id].to_dict(), "session_id": session_id})

@app.route('/api/action', methods=['POST'])
def game_action():
    data = request.json
    session_id = data.get('session_id')
    action = data.get('action')
    battle_id = data.get('battle_id')
    
    if not session_id or session_id not in players:
        return jsonify({"error": "Сессия не найдена"})
    
    player = players[session_id]
    
    # Навигация
    if action in LOCATIONS:
        player.location = action
        return jsonify({"success": True, "location": action, "description": LOCATIONS[action]["description"], "player": player.to_dict()})
    
    if action == "Назад":
        if player.location == "Боссы":
            player.location = "За стеной"
        elif player.location in ["Магазин оружия", "Аптека", "Магазин ODM", "Черный рынок"]:
            player.location = "Торговый район"
        elif player.location == "Таверна":
            player.location = "Центральная площадь"
        elif player.location in ["Лаборатория", "Королевский дворец", "Рынок Сины", "Храм воинов"]:
            player.location = "Стена Сина"
        elif player.location == "Госпиталь":
            player.location = "Стена Роза"
        else:
            player.location = "Стена Мария"
        return jsonify({"success": True, "location": player.location, "description": LOCATIONS[player.location]["description"], "player": player.to_dict()})
    
    # Характеристики
    if action == "stats":
        return jsonify({"stats": player.to_dict()})
    
    if action == "inventory":
        return jsonify({"inventory": player.inventory, "player": player.to_dict()})
    
    # Отдых и лечение
    if action == "rest" and player.can_rest():
        player.rest()
        return jsonify({"success": True, "message": "Вы отдохнули!", "player": player.to_dict()})
    
    if action == "heal" and player.gold >= 10:
        player.gold -= 10
        player.health = player.max_health
        return jsonify({"success": True, "message": "Вылечены!", "player": player.to_dict()})
    
    if action == "daily" and player.can_get_daily():
        player.daily_reward = datetime.now()
        reward = random.randint(50, 150)
        player.gold += reward
        return jsonify({"success": True, "message": f"Ежедневная награда! +{reward} золота", "player": player.to_dict()})
    
    # Тренировки
    if action == "train_odm" and player.odm_gear and player.gas_level >= 20 and player.blades_count >= 2 and player.can_train():
        player.gas_level -= 20
        player.blades_count -= 2
        exp_gain = random.randint(25, 40)
        player.exp += exp_gain
        player.last_training = datetime.now()
        return jsonify({"success": True, "message": f"Тренировка! +{exp_gain} опыта", "player": player.to_dict()})
    
    if action == "train_normal" and player.can_train():
        exp_gain = random.randint(10, 20)
        player.exp += exp_gain
        player.last_training = datetime.now()
        return jsonify({"success": True, "message": f"Тренировка! +{exp_gain} опыта", "player": player.to_dict()})
    
    # Покупки
    if action == "buy_odm" and player.gold >= 100:
        player.gold -= 100
        player.odm_gear = True
        return jsonify({"success": True, "message": "Куплено ODM!", "player": player.to_dict()})
    
    if action == "buy_gas" and player.gold >= 20:
        player.gold -= 20
        player.gas_level = min(100, player.gas_level + 50)
        return jsonify({"success": True, "message": f"Куплен газ! {player.gas_level}/100", "player": player.to_dict()})
    
    if action == "buy_blades" and player.gold >= 10:
        player.gold -= 10
        player.blades_count = min(6, player.blades_count + 3)
        return jsonify({"success": True, "message": f"Куплены лезвия! {player.blades_count}/6", "player": player.to_dict()})
    
    if action == "buy_sword" and player.gold >= 50:
        player.gold -= 50
        player.attack += 5
        return jsonify({"success": True, "message": "Куплен меч! Атака +5", "player": player.to_dict()})
    
    if action == "buy_potion" and player.gold >= 20:
        player.gold -= 20
        player.inventory.append("Зелье здоровья")
        return jsonify({"success": True, "message": "Куплено зелье!", "player": player.to_dict()})
    
    # Исследование
    if action == "explore":
        events = [{"text": "🌿 Нашли травы!", "item": "Лечебные травы"}, {"text": "💰 Нашли 15 золота!", "gold": 15}]
        event = random.choice(events)
        if event.get("item"): player.inventory.append(event["item"])
        if event.get("gold"): player.gold += event["gold"]
        return jsonify({"success": True, "message": event["text"], "player": player.to_dict()})
    
    # Охота
    if action == "hunt" and player.odm_gear:
        titan_name = random.choice(["Обычный титан", "Аномальный титан", "Звероподобный титан"])
        titan = TITANS[titan_name]
        battle_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
        battles[battle_id] = {"player_id": session_id, "enemy_name": titan_name, "enemy_health": titan["здоровье"], "enemy_max_health": titan["здоровье"], "enemy_attack": titan["атака"], "reward": titan["награда"], "weak_spot": titan["слабое_место"], "description": titan["описание"]}
        return jsonify({"battle_start": True, "battle_id": battle_id, "enemy": titan_name, "enemy_health": titan["здоровье"], "enemy_max_health": titan["здоровье"], "weak_spot": titan["слабое_место"], "description": titan["описание"], "player_health": player.health})
    
    # Боссы
    if action in ["Броня Титана", "Колоссальный титан", "Дракон"] and player.odm_gear:
        titan = TITANS[action]
        battle_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
        battles[battle_id] = {"player_id": session_id, "enemy_name": action, "enemy_health": titan["здоровье"], "enemy_max_health": titan["здоровье"], "enemy_attack": titan["атака"], "reward": titan["награда"], "weak_spot": titan["слабое_место"], "description": titan["описание"], "is_boss": True}
        return jsonify({"battle_start": True, "battle_id": battle_id, "enemy": action, "enemy_health": titan["здоровье"], "enemy_max_health": titan["здоровье"], "weak_spot": titan["слабое_место"], "description": titan["описание"], "is_boss": True, "player_health": player.health})
    
    # Боевые действия
    if action == "battle_attack" and battle_id in battles:
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        damage = random.randint(10, 25) + player.attack // 2
        battle["enemy_health"] -= damage
        if battle["enemy_health"] <= 0:
            gold_gain = random.randint(battle["reward"][0], battle["reward"][1])
            player.gold += gold_gain
            del battles[battle_id]
            return jsonify({"victory": True, "message": f"ПОБЕДА! +{gold_gain} золота", "player": player.to_dict()})
        enemy_damage = max(1, battle["enemy_attack"] - player.defense // 3)
        player.health -= enemy_damage
        if player.health <= 0:
            player.health = player.max_health // 2
            del battles[battle_id]
            return jsonify({"defeat": True, "message": "ВЫ ПОГИБЛИ!", "player": player.to_dict()})
        return jsonify({"action": "attack", "damage": damage, "enemy_damage": enemy_damage, "enemy_health": battle["enemy_health"], "player_health": player.health, "message": f"Урон {damage}! Враг атакует -{enemy_damage}", "player": player.to_dict()})
    
    if action == "battle_heal" and battle_id in battles:
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        if "Зелье здоровья" in player.inventory:
            player.inventory.remove("Зелье здоровья")
            player.health = min(player.max_health, player.health + 30)
            return jsonify({"action": "heal", "heal": 30, "player_health": player.health, "message": "Вылечили 30 HP!", "player": player.to_dict()})
        return jsonify({"error": "Нет зелий!"})
    
    return jsonify({"error": f"Неизвестное действие: {action}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    application = app
