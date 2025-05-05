import json
import utils
import config
import getInfo

def getBest40(userData, needCharacter=False, justDATA=False, justHTML=False):
    songs, player = getInfo.getSave(userData)
    songs = sorted(songs, key=lambda x: x.rating, reverse=True)[:40]
    
    if justDATA:
        return (songs, player)
    with open(config.ASSETS_HTML_B40 if not needCharacter else config.ASSETS_HTML_B40_CHARACTER, "r", encoding="utf-8") as f:
        html = f.read()
        html = html.replace("/{{{data}}}/", json.dumps([songs, player], indent=4, ensure_ascii=False))
    if justHTML:
        return html
    if needCharacter:
        return utils.renderHtmlToImage((2800, 1310), 1.5, html_data=html, isHTML=True)
    return utils.renderHtmlToImage((2600, 1310), 1.5, html_data=html, isHTML=True)
