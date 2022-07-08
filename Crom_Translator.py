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

def sep_tag_def(tag_line_propre,debug=False):
    """Identifie et sépare une étiquette de sa définition.
    Retourne un tuple(list[str],str)
    
    tag_line_propre -> str"""

    #On utilise le tiret central comme du séparateur. On aurait pu faire un tag_line_propre.split(" - "), tout simplement.
    pattern_tag = re.compile(r"(.|\d)*?(?= - )")
    tag_brut = re.search(pattern_tag,tag_line_propre)
    if debug:
        print("Tag brut")
        print(tag_brut[0])
    if not tag_brut:
        #Si on ne trouve pas, c'est que le séparateur - n'est pas correctement placé. On soulève une exception.
        tag_error = re.match(re.compile("[^\s]*"),tag_line_propre)
        raise Exception('Attention, il semblerait qu\'un tag ne soit pas bien entré dans le guide. Il faut suivre le format "nom (ang : traduction) - definition", la partie de traduction étant facultative. Le tag qui pose problème est : {} .'.format(tag_error[0]))
    #On veut s'assurer qu'il n'y a pas de mention de langue et de traduction dans nos données.
    pattern_lang = re.compile(r" {0,1}\(.+?\)")
    tag_sans_lang,_ = re.subn(pattern_lang,"",tag_brut[0])
    if debug:
        print("Tag sans langue")
        print(tag_sans_lang)
    #Au cas où plusieurs tags sont définis ensemble, on les sépare.
    multiple_tags = tag_sans_lang.split(" / ")
    if debug and len(multiple_tags)>1:
        print("Tous les tags séparés :")
        print(multiple_tags)
    #La définition correspond à tout ce qui suit.
    definition = tag_line_propre[tag_brut.end()+3:]
    if debug:
        print("Définition :")
        print(definition)
        input('Appuyez sur votre clavier pour continuer le débugage :')
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

def traitement_fondation_fr(onglet,debug=False):
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
                    tags,definition = sep_tag_def(tag_line,debug)
                    for tag in tags:
                        #on met à jour notre dictionnaire
                        if tag=="sûr":
                            correspondances_nom_def[tag]="Les objets de classe Sûr sont des anomalies qui sont soit assez bien comprises pour être confinées sans aucun risque de façon permanente, soit dotées de propriétés qui ne s'activent qu'en réponse à une action extérieure intentionnelle."
                        elif tag=="euclide":
                            correspondances_nom_def[tag]="Les objets de classe Euclide sont des anomalies qui sont soit peu comprises soit intrinsèquement imprévisibles, de telle sorte qu'un confinement précis est nécessaire pour bloquer leurs effets."
                        elif tag=="keter":
                            correspondances_nom_def[tag]="Les objets de classe Keter sont des anomalies dont le confinement requiert des procédures avancées et complexes, ou qui ne peuvent pas être confinées efficacement par la Fondation avec ses connaissances et capacités actuelles."
                        elif tag=="thaumiel":
                            correspondances_nom_def[tag]="Les objets de classe Thaumiel sont des anomalies hautement secrètes et extrêmement rares qui sont utilisées par la Fondation pour confiner ou contrer les effets d'autres anomalies qu'il serait très difficile ou impossible de confiner autrement."
                        elif tag=="classe-ésotérique":
                            correspondances_nom_def[tag]="Certains objets nécessitent un confinement très atypique ou ne correspondant à aucune des autres classes : il faut alors en créer une nouvelle rien que pour eux."
                        elif tag=="en-attente":
                            correspondances_nom_def[tag]="Un objet SCP en attente de classification."
                        elif tag=="blanc":
                            correspondances_nom_def[tag]="L'objet est bénéfique à la Fondation et son usage est strictement réglementé comme précisé dans les procédures de confinement spéciales de l'objet."
                        elif tag=="bleu":
                            correspondances_nom_def[tag]="L'objet peut être bénéfique mais ne peut être utilisé comme on l'entend, cela correspond aux artefacts imprévisibles ou aux entités n'agissant d'une certaine manière que sur certains individus."
                        elif tag=="vert":
                            correspondances_nom_def[tag]="L'objet n'est ni bénéfique, ni nocif tant qu'il est utilisé correctement."
                        elif tag=="jaune":
                            correspondances_nom_def[tag]="L'objet est nocif mais facilement limitable, cela signifie par exemple qu'il ne peut agir que sous certaines circonstances (comprises ou non) et reste stable tant que ces conditions ne sont pas remplies."
                        elif tag=="orange":
                            correspondances_nom_def[tag]="L'objet est imprévisible, il peut se montrer dangereux et n'est pas aisément contrôlable."
                        elif tag=="rouge":
                            correspondances_nom_def[tag]="L'objet est imprévisible et a la capacité de causer des dégâts sur une grande échelle."
                        elif tag=="noir":
                            correspondances_nom_def[tag]="L'objet peut causer des dégâts sur une échelle globale, voire plus."
                        elif tag=="indéterminé":
                            correspondances_nom_def[tag]="Absence de niveau de menace."
                        else:
                            correspondances_nom_def[tag]=definition
        else:
            #Le cas plus facile où tout est listé :
            for li in tag_li:
                #On nettoie
                li_brut = nettoyage_html(li)
                #On cherche la correspondance tag/def
                tags,definition = sep_tag_def(li_brut,debug)
                for tag in tags:
                    #on met à jour notre dictionnaire
                    if tag=="sûr":
                        correspondances_nom_def[tag]="Les objets de classe Sûr sont des anomalies qui sont soit assez bien comprises pour être confinées sans aucun risque de façon permanente, soit dotées de propriétés qui ne s'activent qu'en réponse à une action extérieure intentionnelle."
                    elif tag=="euclide":
                        correspondances_nom_def[tag]="Les objets de classe Euclide sont des anomalies qui sont soit peu comprises soit intrinsèquement imprévisibles, de telle sorte qu'un confinement précis est nécessaire pour bloquer leurs effets."
                    elif tag=="keter":
                        correspondances_nom_def[tag]="Les objets de classe Keter sont des anomalies dont le confinement requiert des procédures avancées et complexes, ou qui ne peuvent pas être confinées efficacement par la Fondation avec ses connaissances et capacités actuelles."
                    elif tag=="thaumiel":
                        correspondances_nom_def[tag]="Les objets de classe Thaumiel sont des anomalies hautement secrètes et extrêmement rares qui sont utilisées par la Fondation pour confiner ou contrer les effets d'autres anomalies qu'il serait très difficile ou impossible de confiner autrement."
                    elif tag=="classe-ésotérique":
                        correspondances_nom_def[tag]="Certains objets nécessitent un confinement très atypique ou ne correspondant à aucune des autres classes : il faut alors en créer une nouvelle rien que pour eux."
                    elif tag=="en-attente":
                        correspondances_nom_def[tag]="Un objet SCP en attente de classification."
                    elif tag=="blanc":
                        correspondances_nom_def[tag]="L'objet est bénéfique à la Fondation et son usage est strictement réglementé comme précisé dans les procédures de confinement spéciales de l'objet."
                    elif tag=="bleu":
                        correspondances_nom_def[tag]="L'objet peut être bénéfique mais ne peut être utilisé comme on l'entend, cela correspond aux artefacts imprévisibles ou aux entités n'agissant d'une certaine manière que sur certains individus."
                    elif tag=="vert":
                        correspondances_nom_def[tag]="L'objet n'est ni bénéfique, ni nocif tant qu'il est utilisé correctement."
                    elif tag=="jaune":
                        correspondances_nom_def[tag]="L'objet est nocif mais facilement limitable, cela signifie par exemple qu'il ne peut agir que sous certaines circonstances (comprises ou non) et reste stable tant que ces conditions ne sont pas remplies."
                    elif tag=="orange":
                        correspondances_nom_def[tag]="L'objet est imprévisible, il peut se montrer dangereux et n'est pas aisément contrôlable."
                    elif tag=="rouge":
                        correspondances_nom_def[tag]="L'objet est imprévisible et a la capacité de causer des dégâts sur une grande échelle."
                    elif tag=="noir":
                        correspondances_nom_def[tag]="L'objet peut causer des dégâts sur une échelle globale, voire plus."
                    elif tag=="indéterminé":
                        correspondances_nom_def[tag]="Absence de niveau de menace."
                    else:
                        correspondances_nom_def[tag]=definition
    return(correspondances_nom_def)

def traitement_fondation_etranger(onglet,debug=False):
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
                tags,definition = sep_tag_def(tag_line,debug)
                for tag in tags:
                    #Pour chaque tag, on vérifie qu'on n'écrase rien car les étiquettes locales sont de faible importance. Actuellement, cette partie du code est inutile car assurée par une autre fonction.
                    if tag not in correspondances_nom_def.keys():
                        #on met à jour notre dictionnaire
                        correspondances_nom_def[tag]="Étiquette du site "+nom_langue+" qui veut dire : « "+definition+" »."
        ind_lang+=1
    
    return correspondances_nom_def

def traitement_guide_des_tags(tag_etranger):
    """Fait les correspondances tag/def pour tous les onglets.
    Retourne un disc{str:str}"""
    guide_tag = recup_page()
    onglets = selection_onglets(guide_tag)
    #On met du moins important au plus important, selon l'ordre de priorité : Etranger < Bibliothèque FR < Fondation FR
    if tag_etranger:
        correspondances_nom_def = traitement_fondation_etranger(onglets[1])
        correspondances_nom_def.update(traitement_fondation_fr(onglets[2]))
    else:
        correspondances_nom_def = traitement_fondation_fr(onglets[2])
    correspondances_nom_def.update(traitement_fondation_fr(onglets[0]))
    return correspondances_nom_def

def creation_fichier(nom="tom_crom.txt",chemin=os.getcwd(),tags_etranger=False):
    """Crée ou met à jour le fichier répertoriant les correspondances, à des fins de lecture par Crom.
    Ne retourne rien.

    nom->str
    chemin->str
    
    http://crom.wikidot.com/tag-search#toc2"""
    correspondances_nom_def=traitement_guide_des_tags(tags_etranger)
    with open(file=chemin+"\\"+nom,mode='w',encoding="UTF-8") as fichier:
        fichier.write("[[code]]\n")
        for tag in correspondances_nom_def.keys():
            fichier.write("[[tags]]\nname = \""+tag+"\"\ndescription = \""+correspondances_nom_def[tag]+"\"\n")
        fichier.write("[[/code]]")

creation_fichier()
