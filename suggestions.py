import json, re
from random import choice

from discord import Interaction as Itr

def loadSuggestions(custom):
    with open('./suggestions.json') as file:
        suggestions = json.load(file)

    origin, images, groups = False, False, {}
    for name in suggestions:
        if name == "_origin":
            origin = suggestions[name]
        if name == "_images":
            images = suggestions[name]
        else:
            groups[name] = suggestions[name]
            if name == "alesan":
                groups[name] += custom["custom_names"]
            if name == "games":
                groups[name] += custom["custom_games"]
            if name == "enemies":
                groups[name] += custom["custom_enemies"]
            if name == "people":
                groups[name] += custom["custom_people"]
            if name == "powerups":
                groups[name] += custom["custom_powerups"]

    return origin, images, groups

def createSuggestion(itr:Itr, custom):
    origin, images, groups = loadSuggestions(custom)
    result = choice(origin)
    data = []
    while "{" in result:
        splited = re.split("{(.*?)}", result)
        result = ""
        text = True
        for s in splited:
            if text:
                result += s
            else:
                decision = choice(groups[s])
                if decision.startswith("$"):
                    decision = formatDollar(itr, decision[1:])
                result += decision
                data.append(decision)
            text = not text
            
    result_images = []
    for d in data:
        if d in images and images[d] != "??":
            result_images.append(images[d])

    result = result.strip()
    result = result[0].upper() + result[1:]
    return result, result_images

def formatDollar(itr:Itr, type):
    if type == "member":
        return choice(itr.guild.members).display_name
    return "N/A"