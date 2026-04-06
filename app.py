from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'rpg-game-secret-key-2024'
CORS(app)

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
        self.quests = {
            "Обычные титаны": {"цель": 5, "прогресс": 0, "награда": 50}
        }
        self.titan_kills = {
            "Обычный титан": 0,
            "Аномальный титан": 0,
            "Звероподобный титан": 0,
            "Броня Титана": 0,
            "Колоссальный титан": 0,
            "Дракон": 0
        }
        self.last_rest = None
        self.last_training = None
        self.daily_reward = None
        self.mikasa_relationship = 0
        self.mikasa_available = False
        self.mikasa_level = 0
        self.has_companion = False
        self.companion_name = None
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "level": self.level,
            "exp": self.exp,
            "max_exp": self.max_exp,
            "health": self.health,
            "max_health": self.max_health,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "attack": self.attack,
            "defense": self.defense,
            "agility": self.agility,
            "gold": self.gold,
            "odm_gear": self.odm_gear,
            "gas_level": self.gas_level,
            "blades_count": self.blades_count,
            "inventory": self.inventory,
            "location": self.location,
            "quests": self.quests,
            "titan_kills": self.titan_kills,
            "last_rest": self.last_rest.isoformat() if self.last_rest else None,
            "last_training": self.last_training.isoformat() if self.last_training else None,
            "daily_reward": self.daily_reward.isoformat() if self.daily_reward else None,
            "mikasa_relationship": self.mikasa_relationship,
            "mikasa_available": self.mikasa_available,
            "mikasa_level": self.mikasa_level,
            "has_companion": self.has_companion,
            "companion_name": self.companion_name
        }
    
    def can_rest(self):
        if not self.last_rest:
            return True
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
        if not self.last_training:
            return True
        return datetime.now() - self.last_training > timedelta(seconds=10)
    
    def can_get_daily(self):
        if not self.daily_reward:
            return True
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

# Локации (ВСЕ, включая новые)
LOCATIONS = {
    "Стена Мария": {"description": "🏛️ СТЕНА МАРИЯ\nСамый внешний округ"},
    "Стена Роза": {"description": "🏛️ СТЕНА РОЗА\nВторой округ"},
    "Стена Сина": {"description": "🏛️ СТЕНА СИНА\nВнутренний округ"},
    "За стеной": {"description": "🌲 ТИТАНИЧЕСКИЙ ЛЕС\nОпасная территория"},
    "Казармы": {"description": "⚔️ КАЗАРМЫ\nЗдесь можно получить задания"},
    "Тренировочная площадка": {"description": "🎯 ТРЕНИРОВОЧНАЯ ПЛОЩАДКА"},
    "Торговый район": {"description": "🛒 ТОРГОВЫЙ РАЙОН"},
    "Магазин оружия": {"description": "⚔️ МАГАЗИН ОРУЖИЯ"},
    "Аптека": {"description": "❤️ АПТЕКА"},
    "Магазин ODM": {"description": "⚡ МАГАЗИН ODM"},
    "Черный рынок": {"description": "🛒 ЧЕРНЫЙ РЫНОК"},
    "Центральная площадь": {"description": "🏙️ ЦЕНТРАЛЬНАЯ ПЛОЩАДЬ"},
    "Таверна": {"description": "🍺 ТАВЕРНА\nИгры и сплетни"},
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

# ============ API ЭНДПОИНТЫ ============

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
    
    # НАВИГАЦИЯ ПО ЛОКАЦИЯМ (ВСЕ локации)
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
    
    # Отдых
    if action == "rest":
        if player.can_rest():
            player.rest()
            return jsonify({"success": True, "message": "Вы отдохнули!", "player": player.to_dict()})
        return jsonify({"error": "Отдых доступен раз в 5 минут!"})
    
    # Ежедневная награда
    if action == "daily":
        if player.can_get_daily():
            player.daily_reward = datetime.now()
            reward = random.randint(50, 150)
            player.gold += reward
            return jsonify({"success": True, "message": f"Ежедневная награда! +{reward} золота", "player": player.to_dict()})
        return jsonify({"error": "Награда доступна раз в 24 часа!"})
    
    # Лечение в госпитале
    if action == "heal":
        if player.gold >= 10:
            player.gold -= 10
            player.health = player.max_health
            return jsonify({"success": True, "message": "Вылечены!", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 10"})
    
    # Тренировки
    if action == "train_odm":
        if not player.odm_gear:
            return jsonify({"error": "Нет ODM снаряжения!"})
        if player.gas_level < 20 or player.blades_count < 2:
            return jsonify({"error": "Недостаточно газа или лезвий!"})
        if not player.can_train():
            return jsonify({"error": "Подождите 10 секунд!"})
        
        player.gas_level -= 20
        player.blades_count -= 2
        exp_gain = random.randint(25, 40)
        agility_gain = random.randint(1, 3)
        player.exp += exp_gain
        player.agility += agility_gain
        player.last_training = datetime.now()
        
        level_msg = ""
        if player.exp >= player.max_exp:
            player.level += 1
            player.exp -= player.max_exp
            player.max_exp = int(player.max_exp * 1.5)
            level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
        
        return jsonify({"success": True, "message": f"Тренировка! +{exp_gain} опыта, ловкость +{agility_gain}{level_msg}", "player": player.to_dict()})
    
    if action == "train_normal":
        if not player.can_train():
            return jsonify({"error": "Подождите 10 секунд!"})
        
        exp_gain = random.randint(10, 20)
        attack_gain = random.randint(1, 2)
        player.exp += exp_gain
        player.attack += attack_gain
        player.last_training = datetime.now()
        
        level_msg = ""
        if player.exp >= player.max_exp:
            player.level += 1
            player.exp -= player.max_exp
            player.max_exp = int(player.max_exp * 1.5)
            level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
        
        return jsonify({"success": True, "message": f"Тренировка! +{exp_gain} опыта, атака +{attack_gain}{level_msg}", "player": player.to_dict()})
    
    # Покупки
    if action == "buy_odm" and player.gold >= 100:
        player.gold -= 100
        player.odm_gear = True
        player.gas_level = 100
        player.blades_count = 6
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
        player.inventory.append("Меч")
        return jsonify({"success": True, "message": "Куплен меч! Атака +5", "player": player.to_dict()})
    
    if action == "buy_shield" and player.gold >= 30:
        player.gold -= 30
        player.defense += 3
        player.inventory.append("Щит")
        return jsonify({"success": True, "message": "Куплен щит! Защита +3", "player": player.to_dict()})
    
    if action == "buy_potion" and player.gold >= 20:
        player.gold -= 20
        player.inventory.append("Зелье здоровья")
        return jsonify({"success": True, "message": "Куплено зелье!", "player": player.to_dict()})
    
    # Исследование леса
    if action == "explore":
        events = [
            {"text": "🌿 Нашли травы!", "item": "Лечебные травы"},
            {"text": "💰 Нашли 15 золота!", "gold": 15},
            {"text": "⚡ Восстановили энергию!", "energy": 20}
        ]
        event = random.choice(events)
        if event.get("item"):
            player.inventory.append(event["item"])
        if event.get("gold"):
            player.gold += event["gold"]
        if event.get("energy"):
            player.energy = min(player.max_energy, player.energy + event["energy"])
        return jsonify({"success": True, "message": event["text"], "player": player.to_dict()})
    
    # Охота на титанов
    if action == "hunt":
        if not player.odm_gear:
            return jsonify({"error": "Нужно ODM снаряжение!"})
        
        titan_names = ["Обычный титан", "Аномальный титан", "Звероподобный титан"]
        weights = [0.6, 0.3, 0.1]
        titan_name = random.choices(titan_names, weights=weights)[0]
        titan = TITANS[titan_name]
        
        battle_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
        battles[battle_id] = {
            "player_id": session_id,
            "enemy_name": titan_name,
            "enemy_health": titan["здоровье"],
            "enemy_max_health": titan["здоровье"],
            "enemy_attack": titan["атака"],
            "reward": titan["награда"],
            "weak_spot": titan["слабое_место"],
            "description": titan["описание"],
            "is_boss": False
        }
        
        return jsonify({
            "battle_start": True,
            "battle_id": battle_id,
            "enemy": titan_name,
            "enemy_health": titan["здоровье"],
            "enemy_max_health": titan["здоровье"],
            "weak_spot": titan["слабое_место"],
            "description": titan["описание"],
            "player_health": player.health
        })
    
    # Боссы
    if action in ["Броня Титана", "Колоссальный титан", "Дракон"]:
        if not player.odm_gear:
            return jsonify({"error": "Нужно ODM снаряжение!"})
        
        level_req = {"Броня Титана": 10, "Колоссальный титан": 20, "Дракон": 30}
        if player.level < level_req[action]:
            return jsonify({"error": f"Нужен {level_req[action]}+ уровень!"})
        
        titan = TITANS[action]
        battle_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
        battles[battle_id] = {
            "player_id": session_id,
            "enemy_name": action,
            "enemy_health": titan["здоровье"],
            "enemy_max_health": titan["здоровье"],
            "enemy_attack": titan["атака"],
            "reward": titan["награда"],
            "weak_spot": titan["слабое_место"],
            "description": titan["описание"],
            "is_boss": True
        }
        
        return jsonify({
            "battle_start": True,
            "battle_id": battle_id,
            "enemy": action,
            "enemy_health": titan["здоровье"],
            "enemy_max_health": titan["здоровье"],
            "weak_spot": titan["слабое_место"],
            "description": titan["описание"],
            "is_boss": True,
            "player_health": player.health
        })
    
    # Боевые действия (атака, лечение, побег)
    if action == "battle_attack":
        if not battle_id or battle_id not in battles:
            return jsonify({"error": "Битва не найдена"})
        
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        
        damage = random.randint(10, 25) + player.attack // 2
        battle["enemy_health"] -= damage
        
        if battle["enemy_health"] <= 0:
            gold_gain = random.randint(battle["reward"][0], battle["reward"][1])
            exp_gain = random.randint(15, 30)
            player.gold += gold_gain
            player.exp += exp_gain
            player.titan_kills[battle["enemy_name"]] = player.titan_kills.get(battle["enemy_name"], 0) + 1
            
            level_msg = ""
            if player.exp >= player.max_exp:
                player.level += 1
                player.exp -= player.max_exp
                player.max_exp = int(player.max_exp * 1.5)
                level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
            
            del battles[battle_id]
            return jsonify({
                "victory": True,
                "message": f"ПОБЕДА! +{gold_gain} золота, +{exp_gain} опыта{level_msg}",
                "player": player.to_dict()
            })
        
        enemy_damage = max(1, battle["enemy_attack"] - player.defense // 3 + random.randint(-5, 10))
        player.health -= enemy_damage
        
        if player.health <= 0:
            player.health = player.max_health // 2
            player.gold = max(0, player.gold - 20)
            del battles[battle_id]
            return jsonify({
                "defeat": True,
                "message": "ВЫ ПОГИБЛИ!",
                "player": player.to_dict()
            })
        
        return jsonify({
            "action": "attack",
            "damage": damage,
            "enemy_damage": enemy_damage,
            "enemy_health": battle["enemy_health"],
            "enemy_max_health": battle["enemy_max_health"],
            "player_health": player.health,
            "message": f"Вы нанесли {damage} урона! {battle['enemy_name']} атакует! -{enemy_damage} HP",
            "player": player.to_dict()
        })
    
    if action == "battle_heal":
        if not battle_id or battle_id not in battles:
            return jsonify({"error": "Битва не найдена"})
        
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        
        zelie_index = -1
        for i, item in enumerate(player.inventory):
            if item == "Зелье здоровья":
                zelie_index = i
                break
        
        if zelie_index == -1:
            return jsonify({"error": "Нет зелий!"})
        
        player.inventory.pop(zelie_index)
        heal = 30
        player.health = min(player.max_health, player.health + heal)
        
        enemy_damage = max(1, battle["enemy_attack"] - player.defense // 3 + random.randint(-5, 10))
        player.health -= enemy_damage
        
        if player.health <= 0:
            player.health = player.max_health // 2
            player.gold = max(0, player.gold - 20)
            del battles[battle_id]
            return jsonify({
                "defeat": True,
                "message": "ВЫ ПОГИБЛИ!",
                "player": player.to_dict()
            })
        
        return jsonify({
            "action": "heal",
            "heal": heal,
            "enemy_damage": enemy_damage,
            "player_health": player.health,
            "enemy_health": battle["enemy_health"],
            "enemy_max_health": battle["enemy_max_health"],
            "message": f"Вылечили {heal} HP! {battle['enemy_name']} атакует! -{enemy_damage} HP",
            "player": player.to_dict()
        })
    
    if action == "battle_flee":
        if not battle_id or battle_id not in battles:
            return jsonify({"error": "Битва не найдена"})
        
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        
        if random.random() < 0.5:
            del battles[battle_id]
            return jsonify({
                "fled": True,
                "message": "Вы сбежали!",
                "player": player.to_dict()
            })
        else:
            enemy_damage = max(1, battle["enemy_attack"] + random.randint(5, 15))
            player.health -= enemy_damage
            
            if player.health <= 0:
                player.health = player.max_health // 2
                player.gold = max(0, player.gold - 20)
                del battles[battle_id]
                return jsonify({
                    "defeat": True,
                    "message": "ВЫ ПОГИБЛИ при побеге!",
                    "player": player.to_dict()
                })
            
            return jsonify({
                "action": "flee_fail",
                "enemy_damage": enemy_damage,
                "player_health": player.health,
                "message": f"Не сбежали! -{enemy_damage} HP",
                "player": player.to_dict()
            })
    
    # Микаса
    if action == "talk_mikasa":
        gain = random.randint(1, 3)
        player.mikasa_relationship = min(100, player.mikasa_relationship + gain)
        
        if player.mikasa_relationship >= 20 and player.mikasa_level < 1:
            player.mikasa_level = 1
        elif player.mikasa_relationship >= 40 and player.mikasa_level < 2:
            player.mikasa_level = 2
        elif player.mikasa_relationship >= 60 and player.mikasa_level < 3:
            player.mikasa_level = 3
        elif player.mikasa_relationship >= 80 and player.mikasa_level < 4:
            player.mikasa_level = 4
        elif player.mikasa_relationship >= 100 and player.mikasa_level < 5:
            player.mikasa_level = 5
        
        return jsonify({"success": True, "message": f"Отношения +{gain} ({player.mikasa_relationship}/100)", "player": player.to_dict()})
    
    if action == "mikasa_status":
        return jsonify({
            "mikasa_status": True,
            "relationship": player.mikasa_relationship,
            "level": player.mikasa_level,
            "has_companion": player.has_companion
        })
    
    if action == "invite_mikasa" or action == "summon_mikasa":
        if player.mikasa_level < 1:
            return jsonify({"error": "Улучшите отношения!"})
        if player.has_companion:
            return jsonify({"error": "Микаса уже в команде!"})
        
        player.has_companion = True
        player.companion_name = "Микаса Аккерман"
        return jsonify({"success": True, "message": "Микаса присоединилась!", "player": player.to_dict()})
    
    if action == "train_with_mikasa":
        if not player.odm_gear:
            return jsonify({"error": "Нужно ODM снаряжение!"})
        if player.gas_level < 30 or player.blades_count < 4:
            return jsonify({"error": "Недостаточно газа или лезвий!"})
        
        player.gas_level -= 30
        player.blades_count -= 4
        player.energy -= 40
        exp_gain = random.randint(50, 80)
        agility_gain = random.randint(2, 5)
        player.exp += exp_gain
        player.agility += agility_gain
        relationship_gain = random.randint(3, 6)
        player.mikasa_relationship = min(100, player.mikasa_relationship + relationship_gain)
        
        level_msg = ""
        if player.exp >= player.max_exp:
            player.level += 1
            player.exp -= player.max_exp
            player.max_exp = int(player.max_exp * 1.5)
            level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
        
        return jsonify({"success": True, "message": f"Тренировка с Микасой! +{exp_gain} опыта, ловкость +{agility_gain}, отношения +{relationship_gain}{level_msg}", "player": player.to_dict()})
    
    if action == "give_gift":
        gifts = ["Красный шарф", "Шоколад", "Книга", "Цветы", "Чай"]
        gift_values = {"Красный шарф": 30, "Шоколад": 15, "Книга": 20, "Цветы": 25, "Чай": 10}
        
        for gift in gifts:
            if gift in player.inventory:
                player.inventory.remove(gift)
                player.mikasa_relationship = min(100, player.mikasa_relationship + gift_values[gift])
                return jsonify({"success": True, "message": f"Вы подарили {gift}! Отношения +{gift_values[gift]}", "player": player.to_dict()})
        
        return jsonify({"error": "Нет подарков!"})
    
    return jsonify({"error": f"Неизвестное действие: {action}"})

# Для Render.com
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    application = app
