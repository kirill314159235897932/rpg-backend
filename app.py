from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import random
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'rpg-game-secret-key-2024'
CORS(app)

# ============ ВАШ ПОЛНЫЙ КОД (БЕЗ TELEGRAM) ============

# Класс персонажа (ваш оригинальный, без изменений)
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
            "Обычные титаны": {"цель": 5, "прогресс": 0, "награда": 50},
            "Броня Титана": {"цель": 1, "прогресс": 0, "награда": 500, "босс": True}
        }
        self.titan_kills = {
            "Обычный титан": 0,
            "Аномальный титан": 0,
            "Звероподобный титан": 0,
            "Броня Титана": 0,
            "Колоссальный титан": 0,
            "Дракон": 0
        }
        self.last_action = datetime.now()
        self.battle_data = None
        self.last_rest = None
        self.kills_counter = 0
        self.last_training = None
        self.daily_reward = None
        self.name_change_cooldown = None
        self.mikasa_relationship = 0
        self.mikasa_available = False
        self.mikasa_cooldown = None
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
            "battle_data": self.battle_data,
            "last_rest": self.last_rest.isoformat() if self.last_rest else None,
            "kills_counter": self.kills_counter,
            "last_training": self.last_training.isoformat() if self.last_training else None,
            "daily_reward": self.daily_reward.isoformat() if self.daily_reward else None,
            "name_change_cooldown": self.name_change_cooldown.isoformat() if self.name_change_cooldown else None,
            "mikasa_relationship": self.mikasa_relationship,
            "mikasa_available": self.mikasa_available,
            "mikasa_cooldown": self.mikasa_cooldown.isoformat() if self.mikasa_cooldown else None,
            "mikasa_level": self.mikasa_level,
            "has_companion": self.has_companion,
            "companion_name": self.companion_name
        }
    
    @classmethod
    def from_dict(cls, data):
        char = cls(data["user_id"], data["name"])
        char.level = data["level"]
        char.exp = data["exp"]
        char.max_exp = data["max_exp"]
        char.health = data["health"]
        char.max_health = data["max_health"]
        char.energy = data.get("energy", 100)
        char.max_energy = data.get("max_energy", 100)
        char.attack = data["attack"]
        char.defense = data["defense"]
        char.agility = data.get("agility", 20)
        char.gold = data["gold"]
        char.odm_gear = data.get("odm_gear", False)
        char.gas_level = data.get("gas_level", 100)
        char.blades_count = data.get("blades_count", 6)
        char.inventory = data["inventory"]
        char.location = data["location"]
        char.quests = data["quests"]
        char.titan_kills = data.get("titan_kills", {})
        char.battle_data = data.get("battle_data")
        char.kills_counter = data.get("kills_counter", 0)
        
        if data.get("last_rest"):
            char.last_rest = datetime.fromisoformat(data["last_rest"])
        if data.get("last_training"):
            char.last_training = datetime.fromisoformat(data["last_training"])
        if data.get("daily_reward"):
            char.daily_reward = datetime.fromisoformat(data["daily_reward"])
        if data.get("name_change_cooldown"):
            char.name_change_cooldown = datetime.fromisoformat(data["name_change_cooldown"])
        
        char.mikasa_relationship = data.get("mikasa_relationship", 0)
        char.mikasa_available = data.get("mikasa_available", False)
        if data.get("mikasa_cooldown"):
            char.mikasa_cooldown = datetime.fromisoformat(data["mikasa_cooldown"])
        char.mikasa_level = data.get("mikasa_level", 0)
        char.has_companion = data.get("has_companion", False)
        char.companion_name = data.get("companion_name", None)
        
        return char
    
    def can_change_name(self):
        if not self.name_change_cooldown:
            return True, None
        time_since_last_change = datetime.now() - self.name_change_cooldown
        if time_since_last_change > timedelta(days=7):
            return True, None
        time_left = timedelta(days=7) - time_since_last_change
        return False, time_left
    
    def change_name(self, new_name):
        old_name = self.name
        self.name = new_name[:20]
        self.name_change_cooldown = datetime.now()
        return old_name
    
    def can_use_odm(self):
        return self.odm_gear and self.gas_level > 0 and self.blades_count > 0
    
    def use_odm_attack(self):
        if not self.can_use_odm():
            return False
        self.gas_level -= 10
        self.blades_count -= 1
        self.energy -= 15
        if self.blades_count < 0:
            self.blades_count = 0
        return True
    
    def can_rest(self):
        if not self.last_rest:
            return True
        return datetime.now() - self.last_rest > timedelta(minutes=5)
    
    def rest(self):
        self.health = self.max_health
        self.energy = self.max_energy
        self.gas_level = 100 if self.odm_gear else 0
        self.blades_count = 6 if self.odm_gear else 0
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
    
    def can_summon_mikasa(self):
        if not self.mikasa_available:
            return False
        if not self.mikasa_cooldown:
            return True
        return datetime.now() - self.mikasa_cooldown > timedelta(minutes=30)
    
    def summon_mikasa(self):
        if self.can_summon_mikasa():
            self.has_companion = True
            self.companion_name = "Микаса Аккерман"
            self.mikasa_cooldown = datetime.now()
            return True
        return False
    
    def dismiss_mikasa(self):
        if self.has_companion and self.companion_name == "Микаса Аккерман":
            self.has_companion = False
            self.companion_name = None
            return True
        return False
    
    def get_mikasa_bonuses(self):
        bonuses = {
            "attack_bonus": 0,
            "defense_bonus": 0,
            "agility_bonus": 0,
            "critical_chance": 0.0,
            "heal_per_turn": 0
        }
        if self.has_companion and self.companion_name == "Микаса Аккерман":
            if self.mikasa_level >= 1:
                bonuses["attack_bonus"] = 5
            if self.mikasa_level >= 2:
                bonuses["agility_bonus"] = 10
            if self.mikasa_level >= 3:
                bonuses["critical_chance"] = 0.15
            if self.mikasa_level >= 4:
                bonuses["defense_bonus"] = 8
            if self.mikasa_level >= 5:
                bonuses["heal_per_turn"] = 5
        return bonuses

# Данные титанов
titans = {
    "Обычный титан": {
        "здоровье": 40, "атака": 8, "защита": 5,
        "награда": (20, 30), "слабое_место": "Шея", "скорость": 3,
        "описание": "15-метровый титан с глупым выражением лица"
    },
    "Аномальный титан": {
        "здоровье": 80, "атака": 15, "защита": 8,
        "награда": (50, 70), "слабое_место": "Глаза", "скорость": 10,
        "особенность": "Неожиданные движения",
        "описание": "Быстрый и непредсказуемый титан"
    },
    "Звероподобный титан": {
        "здоровье": 150, "атака": 25, "защита": 15,
        "награда": (100, 150), "слабое_место": "Спина", "скорость": 20,
        "особенность": "Может кидаться предметами",
        "описание": "Титан, похожий на зверя, обладает интеллектом"
    },
    "Броня Титана": {
        "здоровье": 500, "атака": 40, "защита": 50,
        "награда": (300, 500), "слабое_место": "Суставы", "скорость": 15,
        "особенность": "Броня ломается при атаках", "босс": True, "фазы": 3,
        "описание": "⚔️ БРОНЯ ТИТАНА\nГигант в полной броне!"
    },
    "Колоссальный титан": {
        "здоровье": 800, "атака": 60, "защита": 30,
        "награда": (500, 800), "слабое_место": "Шея", "скорость": 5,
        "особенность": "Паровой взрыв", "босс": True, "фазы": 2,
        "описание": "🔥 КОЛОССАЛЬНЫЙ ТИТАН\n60-метровый гигант!"
    },
    "Дракон": {
        "здоровье": 1000, "атака": 70, "защита": 40,
        "награда": (1000, 1500), "слабое_место": "Сердце", "скорость": 25,
        "особенность": "Огненное дыхание", "босс": True, "фазы": 4,
        "описание": "🐉 ДРЕВНИЙ ДРАКОН\nМифическое существо!"
    }
}

# Локации
locations = {
    "Стена Мария": {"description": "🏛️ СТЕНА МАРИЯ\n\nСамый внешний округ человечества."},
    "Стена Роза": {"description": "🏛️ СТЕНА РОЗА\n\nВторой округ."},
    "Стена Сина": {"description": "🏛️ СТЕНА СИНА\n\nВнутренний округ."},
    "За стеной": {"description": "🌲 ТИТАНИЧЕСКИЙ ЛЕС\n\nОпасная территория."},
    "Казармы": {"description": "⚔️ КАЗАРМЫ\n\nЗдесь можно получить задания."},
    "Тренировочная площадка": {"description": "🎯 ТРЕНИРОВОЧНАЯ ПЛОЩАДКА"},
    "Торговый район": {"description": "🛒 ТОРГОВЫЙ РАЙОН"},
    "Магазин оружия": {"description": "⚔️ МАГАЗИН ОРУЖИЯ"},
    "Аптека": {"description": "❤️ АПТЕКА"},
    "Магазин ODM": {"description": "⚡ МАГАЗИН ODM"},
    "Центральная площадь": {"description": "🏙️ ЦЕНТРАЛЬНАЯ ПЛОЩАДЬ"},
    "Таверна": {"description": "🍺 ТАВЕРНА"},
    "Госпиталь": {"description": "🏥 ГОСПИТАЛЬ"},
    "Лаборатория": {"description": "🔬 ЛАБОРАТОРИЯ"},
    "Королевский дворец": {"description": "👑 КОРОЛЕВСКИЙ ДВОРЕЦ"},
    "Рынок Сины": {"description": "💰 РЫНОК СИНЫ"},
    "Храм воинов": {"description": "🛐 ХРАМ ВОИНОВ"},
    "Дом Аккерманов": {"description": "🏠 ДОМ АККЕРМАНОВ"}
}

# Хранилище игроков и битв
players = {}
battles = {}

# ============ API ЭНДПОИНТЫ ============

@app.route('/')
def index():
    return render_template('index.html')

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
    if action in locations:
        player.location = action
        return jsonify({"success": True, "location": action, "description": locations[action]["description"], "player": player.to_dict()})
    
    if action == "Назад" or action == "Вернуться к стене" or action == "На стену":
        player.location = "Стена Мария"
        return jsonify({"success": True, "location": "Стена Мария", "description": locations["Стена Мария"]["description"], "player": player.to_dict()})
    
    # Характеристики
    if action == "stats":
        total_kills = sum(player.titan_kills.values())
        return jsonify({"stats": player.to_dict(), "total_kills": total_kills})
    
    # Инвентарь
    if action == "inventory":
        return jsonify({"inventory": player.inventory, "player": player.to_dict()})
    
    # Отдых
    if action == "rest":
        if player.can_rest():
            player.rest()
            return jsonify({"success": True, "message": "Вы отдохнули! Здоровье и энергия восстановлены.", "player": player.to_dict()})
        time_left = 5 - int((datetime.now() - player.last_rest).total_seconds() / 60)
        return jsonify({"error": f"Отдых возможен через {max(0, time_left)} минут!"})
    
    # Ежедневная награда
    if action == "daily":
        if player.can_get_daily():
            player.daily_reward = datetime.now()
            reward = random.randint(50, 150)
            player.gold += reward
            bonus_text = ""
            if random.random() < 0.3:
                bonus = random.choice(["Зелье здоровья", "Лечебные травы"])
                player.inventory.append(bonus)
                bonus_text = f"\n🎁 Бонус: {bonus}"
            return jsonify({"success": True, "message": f"Ежедневная награда! +{reward} золота{bonus_text}", "player": player.to_dict()})
        next_reward = 24 - int((datetime.now() - player.daily_reward).total_seconds() / 3600)
        return jsonify({"error": f"Следующая награда через {max(0, next_reward)} часов!"})
    
    # Лечение
    if action == "heal":
        if player.gold >= 10:
            player.gold -= 10
            player.health = player.max_health
            return jsonify({"success": True, "message": "Вылечены! Здоровье восстановлено.", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 10, у вас {player.gold}"})
    
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
            level_up(player)
            level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
        
        return jsonify({"success": True, "message": f"Тренировка с ODM! +{exp_gain} опыта, ловкость +{agility_gain}{level_msg}", "player": player.to_dict()})
    
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
            level_up(player)
            level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
        
        return jsonify({"success": True, "message": f"Тренировка! +{exp_gain} опыта, атака +{attack_gain}{level_msg}", "player": player.to_dict()})
    
    # Покупки
    if action == "buy_odm":
        if player.gold >= 100:
            player.gold -= 100
            player.odm_gear = True
            player.gas_level = 100
            player.blades_count = 6
            return jsonify({"success": True, "message": "Куплено ODM снаряжение!", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 100, у вас {player.gold}"})
    
    if action == "buy_gas":
        if player.gold >= 20:
            player.gold -= 20
            player.gas_level = min(100, player.gas_level + 50)
            return jsonify({"success": True, "message": f"Куплен газ! Газ: {player.gas_level}/100", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 20, у вас {player.gold}"})
    
    if action == "buy_blades":
        if player.gold >= 10:
            player.gold -= 10
            player.blades_count = min(6, player.blades_count + 3)
            return jsonify({"success": True, "message": f"Куплены лезвия! Лезвий: {player.blades_count}/6", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 10, у вас {player.gold}"})
    
    if action == "buy_sword":
        if player.gold >= 50:
            player.gold -= 50
            player.attack += 5
            player.inventory.append("Меч")
            return jsonify({"success": True, "message": "Куплен меч! Атака +5", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 50, у вас {player.gold}"})
    
    if action == "buy_shield":
        if player.gold >= 30:
            player.gold -= 30
            player.defense += 3
            player.inventory.append("Щит")
            return jsonify({"success": True, "message": "Куплен щит! Защита +3", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 30, у вас {player.gold}"})
    
    if action == "buy_potion":
        if player.gold >= 20:
            player.gold -= 20
            player.inventory.append("Зелье здоровья")
            return jsonify({"success": True, "message": "Куплено зелье здоровья!", "player": player.to_dict()})
        return jsonify({"error": f"Недостаточно золота! Нужно 20, у вас {player.gold}"})
    
    # Исследование леса
    if action == "explore":
        events = [
            {"text": "🌿 Нашли лечебные травы!", "item": "Лечебные травы"},
            {"text": "💰 Нашли 15 золота!", "gold": 15},
            {"text": "⚡ Восстановили энергию!", "energy": 20},
            {"text": "⚠️ Ничего не нашли..."}
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
        titan = titans[titan_name]
        
        battle_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
        battles[battle_id] = {
            "player_id": session_id,
            "enemy_name": titan_name,
            "enemy_health": titan["здоровье"],
            "enemy_max_health": titan["здоровье"],
            "enemy_attack": titan["атака"],
            "enemy_defense": titan["защита"],
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
            return jsonify({"error": f"Для битвы с {action} нужен {level_req[action]}+ уровень! Ваш уровень: {player.level}"})
        
        titan = titans[action]
        battle_id = str(random.randint(10000, 99999)) + str(int(datetime.now().timestamp()))
        battles[battle_id] = {
            "player_id": session_id,
            "enemy_name": action,
            "enemy_health": titan["здоровье"],
            "enemy_max_health": titan["здоровье"],
            "enemy_attack": titan["атака"],
            "enemy_defense": titan["защита"],
            "reward": titan["награда"],
            "weak_spot": titan["слабое_место"],
            "description": titan["описание"],
            "is_boss": True,
            "phases": titan.get("фазы", 1),
            "phase": 1
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
    
    # Боевое действие - атака
    if action == "battle_attack":
        if not battle_id or battle_id not in battles:
            return jsonify({"error": "Битва не найдена"})
        
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        
        mikasa_bonuses = player.get_mikasa_bonuses()
        
        # Расчет урона
        has_critical = random.random() < mikasa_bonuses["critical_chance"]
        hit_weak = random.random() < 0.2
        damage = player.attack + mikasa_bonuses["attack_bonus"] + random.randint(5, 20)
        
        if has_critical:
            damage *= 1.5
            crit_text = "💥 КРИТИЧЕСКИЙ УДАР! "
        else:
            crit_text = ""
        
        if hit_weak:
            damage *= 2
            weak_text = f"🎯 ПОПАДАНИЕ В СЛАБОЕ МЕСТО ({battle['weak_spot']})! "
        else:
            weak_text = ""
        
        battle["enemy_health"] -= damage
        
        if battle["enemy_health"] <= 0:
            gold_gain = random.randint(battle["reward"][0], battle["reward"][1])
            exp_gain = random.randint(15, 30)
            player.gold += gold_gain
            player.exp += exp_gain
            player.titan_kills[battle["enemy_name"]] = player.titan_kills.get(battle["enemy_name"], 0) + 1
            
            level_msg = ""
            if player.exp >= player.max_exp:
                level_up(player)
                level_msg = f"\n⭐ НОВЫЙ УРОВЕНЬ {player.level}!"
            
            del battles[battle_id]
            return jsonify({
                "victory": True,
                "message": f"ПОБЕДА! +{gold_gain} золота, +{exp_gain} опыта{level_msg}",
                "player": player.to_dict()
            })
        
        # Атака врага
        enemy_damage = max(1, battle["enemy_attack"] - player.defense // 3 + random.randint(-5, 10))
        player.health -= enemy_damage
        
        if player.health <= 0:
            player.health = player.max_health // 2
            player.gold = max(0, player.gold - 20)
            player.location = "Стена Мария"
            del battles[battle_id]
            return jsonify({
                "defeat": True,
                "message": "ВЫ ПОГИБЛИ! Вас доставили на Стену Мария.",
                "player": player.to_dict()
            })
        
        return jsonify({
            "action": "attack",
            "damage": int(damage),
            "enemy_damage": enemy_damage,
            "enemy_health": battle["enemy_health"],
            "enemy_max_health": battle["enemy_max_health"],
            "player_health": player.health,
            "message": f"{crit_text}{weak_text}Вы нанесли {int(damage)} урона! {battle['enemy_name']} атакует! -{enemy_damage} HP",
            "player": player.to_dict()
        })
    
    # Боевое действие - зелье
    if action == "battle_heal":
        if not battle_id or battle_id not in battles:
            return jsonify({"error": "Битва не найдена"})
        
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        
        zelie_index = -1
        for i, item in enumerate(player.inventory):
            if item in ["Зелье здоровья", "Большое зелье"]:
                zelie_index = i
                break
        
        if zelie_index == -1:
            return jsonify({"error": "Нет зелий здоровья!"})
        
        zelie = player.inventory[zelie_index]
        heal = 60 if zelie == "Большое зелье" else 30
        player.health = min(player.max_health, player.health + heal)
        player.inventory.pop(zelie_index)
        
        enemy_damage = max(1, battle["enemy_attack"] - player.defense // 3 + random.randint(-5, 10))
        player.health -= enemy_damage
        
        if player.health <= 0:
            player.health = player.max_health // 2
            player.gold = max(0, player.gold - 20)
            player.location = "Стена Мария"
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
            "message": f"Вы использовали {zelie}! +{heal} HP. {battle['enemy_name']} атакует! -{enemy_damage} HP",
            "player": player.to_dict()
        })
    
    # Боевое действие - побег
    if action == "battle_flee":
        if not battle_id or battle_id not in battles:
            return jsonify({"error": "Битва не найдена"})
        
        battle = battles[battle_id]
        player = players[battle["player_id"]]
        
        if random.random() < 0.5:
            del battles[battle_id]
            return jsonify({
                "fled": True,
                "message": "Вы успешно сбежали!",
                "player": player.to_dict()
            })
        else:
            enemy_damage = max(1, battle["enemy_attack"] + random.randint(5, 15))
            player.health -= enemy_damage
            
            if player.health <= 0:
                player.health = player.max_health // 2
                player.gold = max(0, player.gold - 20)
                player.location = "Стена Мария"
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
                "message": f"Не удалось сбежать! {battle['enemy_name']} атакует! -{enemy_damage} HP",
                "player": player.to_dict()
            })
    
    # Микаса - разговор
    if action == "talk_mikasa":
        if player.level < 5:
            return jsonify({"error": "Микаса появится после 5 уровня!"})
        
        gain = random.randint(1, 3)
        player.mikasa_relationship = min(100, player.mikasa_relationship + gain)
        
        old_level = player.mikasa_level
        if player.mikasa_relationship >= 100:
            player.mikasa_level = 5
        elif player.mikasa_relationship >= 80:
            player.mikasa_level = 4
        elif player.mikasa_relationship >= 60:
            player.mikasa_level = 3
        elif player.mikasa_relationship >= 40:
            player.mikasa_level = 2
        elif player.mikasa_relationship >= 20:
            player.mikasa_level = 1
        
        level_msg = ""
        if old_level < player.mikasa_level:
            level_msg = f"\n⭐ УРОВЕНЬ ОТНОШЕНИЙ ПОВЫШЕН до {player.mikasa_level}!"
        
        return jsonify({
            "success": True,
            "message": f"💬 Разговор с Микасой. Отношения +{gain} ({player.mikasa_relationship}/100){level_msg}",
            "player": player.to_dict()
        })
    
    # Микаса - статус
    if action == "mikasa_status":
        return jsonify({
            "mikasa_status": True,
            "relationship": player.mikasa_relationship,
            "level": player.mikasa_level,
            "has_companion": player.has_companion,
            "player": player.to_dict()
        })
    
    # Микаса - призвать
    if action == "summon_mikasa":
        if player.level < 5:
            return jsonify({"error": "Микаса появится после 5 уровня!"})
        if player.mikasa_level < 1:
            return jsonify({"error": "Улучшите отношения с Микасой (нужен 1+ уровень)!"})
        if player.has_companion:
            return jsonify({"error": "Микаса уже в команде!"})
        
        player.has_companion = True
        player.companion_name = "Микаса Аккерман"
        return jsonify({
            "success": True,
            "message": "👤 Микаса присоединилась к команде! +5% к атаке, +10% к ловкости!",
            "player": player.to_dict()
        })
    
    return jsonify({"error": f"Неизвестное действие: {action}"})

def level_up(player):
    player.level += 1
    player.exp -= player.max_exp
    player.max_exp = int(player.max_exp * 1.5)
    player.max_health += 20
    player.health = player.max_health
    player.max_energy += 10
    player.energy = player.max_energy
    player.attack += 5
    player.defense += 3
    player.agility += 2
    if player.level >= 5 and not player.mikasa_available:
        player.mikasa_available = True
# В самом конце файла замените эту часть:
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Это нужно для Render.com
    application = app