from bs4 import BeautifulSoup
import re, requests,os

def recup_page(lien = "http://fondationscp.wikidot.com/guide-des-tags"):
    """Récupère le tableau d'onglet sur la page du guide francophone, ou sur une autre selon les attentes de l'utilisateur.
    Retourne un objet de type bs4.element.Tag (objet web scrappé avec la bibliothèque python BeautifulSoup4).
    
    lien -> str

    Fonction créée dans le cadre de mon code de mémoire "Veil_Lifter" suivi à l'Ecole Nationale des Chartes, et perfectionnée dans le cadre d'un stage réalisé à l'ObTIC, Sorbonne Université, été 2022.
    Source : https://github.com/Cendres06/Veil_Lifter"""

    #On récupère les données web
    ma_page = requests.get(lien)
    #On fait la soupe
    ma_page_soup = BeautifulSoup(ma_page.text,'html.parser')

    #Cas de lien vide
    if ma_page_soup.find(class_="bloc-404"):
        raise Exception("La page n'existe pas encore sur le site.")

    #On ne retourne que le tableau d'onglet
    return ma_page_soup.find(class_="yui-content")

def selection_onglets(ma_page,liste_num_onglets=['1','2','4']):
    """Récupère le contenu des onglets spécifiés par l'utilisateur sur une page contenant un tableau d'onglet (objet tabview). Par défaut, la fonction récupère les onglets contenant des étiquettes.
    Retourne une list[bs4.element.Tag], un élément par onglet.
    
    ma_page -> bs4.element.Tag
    liste_num_onglets -> list[str] avec chaque string pouvant être castée en entier."""
    liste_contenu = []
    for nb in liste_num_onglets:
        #On récupère l'id de l'onglet
        id_onglet = "wiki-tab-0-"+nb
        #On ajoute son contenu à la liste
        liste_contenu.append(ma_page.find(id=id_onglet))
    
    return liste_contenu

def nettoyage_html(field):
    """Utilise la fonction de récupération des données de fond de BeautifulSoup4 comme d'un nettoyeur HTML.
    Retourne une str.
    
    field -> bs4.element.Tag"""
    return field.get_text()

def sep_tag_def(tag_line_propre):
    """Identifie et sépare une étiquette de sa définition.
    Retourne un tuple(list[str],str)
    
    tag_line_propre -> str"""

    #On utilise le tiret central comme du séparateur. On aurait pu faire un tag_line_propre.split(" - "), tout simplement.
    pattern_tag = re.compile(r"(.|\d)*?(?= - )")
    tag_brut = re.search(pattern_tag,tag_line_propre)
    
    if not tag_brut:
        #Si on ne trouve pas, c'est que le séparateur - n'est pas correctement placé. On soulève une exception.
        tag_error = re.match(re.compile("[^\s]*"),tag_line_propre)
        raise Exception('Attention, il semblerait qu\'un tag ne soit pas bien entré dans le guide. Il faut suivre le format "nom (ang : traduction) - definition", la partie de traduction étant facultative. Le tag qui pose problème est : {} .'.format(tag_error[0]))
    #On veut s'assurer qu'il n'y a pas de mention de langue et de traduction dans nos données.
    pattern_lang = re.compile(r" {0,1}\(((.)* {0,1}: {0,1}.*? {0,1})*\)")
    tag_sans_lang,_ = re.subn(pattern_lang,"",tag_brut[0])
    #Au cas où plusieurs tags sont définis ensemble, on les sépare.
    multiple_tags = tag_sans_lang.split(" / ")
    #La définition correspond à tout ce qui suit.
    definition = tag_line_propre[tag_brut.end()+3:]
    return multiple_tags,definition

def identif_format_p(p):
    """Teste le format de la ligne afin de s'assurer qu'on ne sélectionne pas un paragraphe <p></p> qui ne contient pas de tags.
    Retourne un bool.
    
    p -> str"""
    pattern_ok = re.compile(r"<p>.* - (.|\s)*</p>")
    requete = re.match(pattern_ok,p)
    if requete:
        return True
    else:
        return False

def traitement_fondation_fr(onglet):
    """Effectue le traitement des étiquettes locales. Concerne donc les onglets appropriés.
    Retourne un dict{str:str}.
    
    onglet -> bs4.element.Tag"""
    correspondances_nom_def = {}
    #On explore progressivement le contenu de l'onglet
    interieur_collapsible = onglet.find_all(class_="collapsible-block-content")
    for collapsible in interieur_collapsible:
        #Certains sont listés, ce qui facilite le travail. Ce n'est jamais le cas pour la Bibliothèque du serpent.
        #Au cas où, on essaye :
        tag_li = collapsible.find_all("li")
        if tag_li==[]:
            #Si on a pas de liste pour se repérer :
            tag_cadre = collapsible.find_all(class_="cadre") #pour les tags de la Fondation
            if not tag_cadre:
                tag_cadre = collapsible.find_all(class_="fancyborder") #pour les tags de la Bibliothèque du Serpent
            
            for cadre in tag_cadre:
                #Au sein des cadres, on va repérer les paragraphes
                texte_brut = cadre.find_all("p")
                #ceux-ci sont nettoyés et leur format est vérifier pour éviter les faux positifs
                texte_brut = [nettoyage_html(p) for p in texte_brut if identif_format_p(str(p))]
                #On split
                texte_parsed = texte_brut[0].split(sep="\n")
                for tag_line in texte_parsed:
                    #On cherche la correspondance tag/def
                    tags,definition = sep_tag_def(tag_line)
                    for tag in tags:
                        #on met à jour notre dictionnaire
                        correspondances_nom_def[tag]=definition
        else:
            #Le cas plus facile où tout est listé :
            for li in tag_li:
                #On nettoie
                li_brut = nettoyage_html(li)
                #On cherche la correspondance tag/def
                tags,definition = sep_tag_def(li_brut)
                for tag in tags:
                    #on met à jour notre dictionnaire
                        correspondances_nom_def[tag]=definition
    return(correspondances_nom_def)

def traitement_fondation_etranger(onglet):
    """"Effectue le traitement des étiquettes d'autres branches. Concerne donc l'onglet des tags étrangers.'
    Retourne un dict{str:str}.
    
    onglet -> bs4.element.Tag"""
    correspondances_nom_def = {}
    #On récupère la liste des langues pour enrichir le dictionnaire en informations pertinentes.
    liste_langues = onglet.find_all("h1")

    #Le schéma est similaire à celui de la recherche des étiquettes locales non listées.
    interieur_collapsible = onglet.find_all(class_="collapsible-block-content")
    ind_lang=0
    for collapsible in interieur_collapsible:
        #Pour chaque langue :
        nom_langue = liste_langues[ind_lang].string.lower()
        tag_cadre = collapsible.find_all(class_="cadre")
        for cadre in tag_cadre:
            #On trouve les paragraphes qui sont acceptables
            texte_brut = cadre.find_all("p")
            #On nettoie et on vérifie le format
            texte_brut = [nettoyage_html(p) for p in texte_brut if identif_format_p(str(p))]
            #On split
            texte_parsed = texte_brut[0].split(sep="\n")
            for tag_line in texte_parsed:
                #On cherche la correspondance tag/def
                tags,definition = sep_tag_def(tag_line)
                for tag in tags:
                    #Pour chaque tag, on vérifie qu'on n'écrase rien car les étiquettes locales sont de faible importance. Actuellement, cette partie du code est inutile car assurée par une autre fonction.
                    if tag not in correspondances_nom_def.keys():
                        #on met à jour notre dictionnaire
                        correspondances_nom_def[tag]="Étiquette du site "+nom_langue+" qui veut dire : « "+definition+" »."
        ind_lang+=1
    
    return correspondances_nom_def

def traitement_guide_des_tags():
    """Fait les correspondances tag/def pour tous les onglets.
    Retourne un disc{str:str}"""
    guide_tag = recup_page()
    onglets = selection_onglets(guide_tag)
    #On met du moins important au plus important, selon l'ordre de priorité : Etranger < Bibliothèque FR < Fondation FR
    correspondances_nom_def = traitement_fondation_etranger(onglets[1])
    correspondances_nom_def.update(traitement_fondation_fr(onglets[2]))
    correspondances_nom_def.update(traitement_fondation_fr(onglets[0]))
    return correspondances_nom_def

def creation_fichier(nom="tom_crom.txt",chemin=os.getcwd()):
    """Crée ou met à jour le fichier répertoriant les correspondances, à des fins de lecture par Crom.
    Ne retourne rien.

    nom->str
    chemin->str
    
    http://crom.wikidot.com/tag-search#toc2"""
    correspondances_nom_def=traitement_guide_des_tags()
    with open(file=chemin+"\\"+nom,mode='w',encoding="UTF-8") as fichier:
        fichier.write("[[code]]\n")
        for tag in correspondances_nom_def.keys():
            fichier.write("[[tags]]\nname = \""+tag+"\"\ndescription = \""+correspondances_nom_def[tag]+"\"\n")
        fichier.write("[[/code]]")

creation_fichier()
