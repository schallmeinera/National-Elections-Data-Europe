# -*- coding: utf-8 -*-
"""Manual party-family assignments (hand-coded 2026-07-13).

Covers parties/coalitions that the automatic Partyfacts/CHES/PopuList/EP-panel
pipeline cannot classify: non-EU countries outside CHES coverage (NO, CH, IS,
CY partly, TR), electoral coalitions, and script/name variants. Families use
the CHES 11-label taxonomy; coalitions get the family of the dominant partner.

Format: (country_code, name-regex, family, populist_key or None)
populist_key is matched against PopuList party_name_short / party_name to
attach the populist/farright/farleft/eurosceptic flags.
"""

MANUAL = [
    # ---- generic catch-alls handled in code; country entries below ----
    # AT
    ("AT", r"^Liste Peter Pilz$", "Green", None),
    # BE
    ("BE", r"^Vooruit$", "Social democratic", None),
    ("BE", r"^PTB-PVDA$", "Radical left", "PVDA/PTB"),
    ("BE", r"Radikale Omvormers", "No family", None),
    # BG
    ("BG", r"WE CONTINUE THE CHANGE|We Continue Changing|ПРОДЪЛЖАВАМЕ ПРОМЯНАТА",
     "Liberal", None),
    ("BG", r"GERB|ГЕРБ|Citizens for European Development", "Conservative", "GERB"),
    ("BG", r"DEMOCRATIC BULGARIA|Demokratichna Balgariya", "Liberal", None),
    ("BG", r"Reformatorski Blok|DSB-BDF", "Conservative", None),
    ("BG", r"ВЪЗРАЖДАНЕ|Vazrazhdane|Vuzrazhdane", "Radical right",
     "Vazrazhdane"),
    ("BG", r"ДПС|Dvizhenie za prava i svobodi|АЛИАНС ЗА ПРАВА И СВОБОДИ",
     "Liberal", "DPS"),
    ("BG", r"ИМА ТАКЪВ НАРОД|HAS SUCH PEOPLE", "No family", "ITN"),
    ("BG", r"БСП|Balgarska sotsialisticheska", "Social democratic", "BSP"),
    ("BG", r"Obedineni Patrioti", "Radical right", None),
    ("BG", r"Patriotichen front", "Radical right", "NFSB"),
    ("BG", r"Izpravi se|Stand Up", "No family", None),
    ("BG", r"not rooting for anyone", "No family", None),
    ("BG", r"МОРАЛ, ЕДИНСТВО, ЧЕСТ|MECh", "No family", "MECh"),
    ("BG", r"ВЕЛИЧИЕ|Velichie", "Radical right", "Velichie"),
    # CH (outside CHES coverage)
    ("CH", r"Sozialdemokratische Partei", "Social democratic", None),
    ("CH", r"Freisinnig|FDP\.Die Liberalen|^Liberale Partei",
     "Liberal", None),
    ("CH", r"Grünliberale|Grunliberale", "Liberal", None),
    ("CH", r"GRÜNE Schweiz|Grune Partei|^Grüne", "Green", None),
    ("CH", r"Die Mitte", "Christian democratic", None),
    ("CH", r"Katholische Konservative|Christlichdemokratische Volkspartei",
     "Christian democratic", None),
    ("CH", r"Burgerlich-Demokratische|Bürgerlich", "Conservative", None),
    ("CH", r"Evangelische Volkspartei", "Christian democratic", None),
    ("CH", r"Landesring der Unabhangigen", "Liberal", None),
    ("CH", r"Auto-Partei|Freiheitspartei der Schweiz", "Radical right",
     None),
    ("CH", r"Schweizerische Volkspartei", "Radical right", "SVP"),
    ("CH", r"Eidgenossisch-Demokratische Union|Eidgenössisch", "Radical right",
     "EDU"),
    ("CH", r"Lega dei Ticinesi", "Radical right", "LdT"),
    ("CH", r"Partei der Arbeit", "Radical left", None),
    # CY (Greek-script variants; families aligned with EP-panel Latin rows)
    ("CY", r"ΔΗΜΟΚΡΑΤΙΚΟΣ ΣΥΝΑΓΕΡΜΟΣ", "Conservative", None),
    ("CY", r"ΑΚΕΛ", "Radical left", "AKEL"),
    ("CY", r"ΔΗΜΟΚΡΑΤΙΚΟ ΚΟΜΜΑ", "Conservative", None),
    ("CY", r"ΕΘΝΙΚΟ ΛΑΪΚΟ ΜΕΤΩΠΟ|Ethniko Laiko Metopo", "Radical right",
     "ELAM"),
    ("CY", r"ΕΔΕΚ", "Social democratic", None),
    ("CY", r"ΔΗΜΟΚΡΑΤΙΚΗ ΠΑΡΑΤΑΞΗ", "Liberal", None),
    ("CY", r"ΚΙΝΗΜΑ ΟΙΚΟΛΟΓΩΝ", "Green", None),
    ("CY", r"^Enomeni Dimokrates$", "Liberal", None),
    ("CY", r"ΕΝΕΡΓΟΙ ΠΟΛΙΤΕΣ", "No family", None),
    ("CY", r"ΑΛΛΑΓΗ ΓΕΝΙΑΣ", "No family", None),
    ("CY", r"Agonistiko Dimokratiko", "No family", None),
    ("CY", r"ΑΛΛΗΛΕΓΓΥΗ", "Conservative", None),
    ("CY", r"ΑΦΥΠΝΙΣΗ|ΠΝΟΗ ΛΑΟΥ|K\.E\.P|ΑΜΜΟΧΩΣΤΟΣ", "No family", None),
    ("CY", r"ΖΩΑ ΚΥΠΡΟΥ|zoa tis Kiprou", "No family", None),
    # CZ
    ("CZ", r"^SPOLU", "Conservative", None),
    ("CZ", r"PIRATI a STAROSTOVE", "Liberal", None),
    ("CZ", r"Motoristé sobě", "Conservative", None),
    # DK
    ("DK", r"Liberal Alliance", "Liberal", None),
    # EE
    ("EE", r"Res Publica|Isamaaliit", "Conservative", None),
    ("EE", r"ÜHENDATUD VASAKPARTEI", "Radical left", None),
    ("EE", r"Parempoolsed", "Conservative", None),
    # ES
    ("ES", r"SOCIALISTES DE CATALUNYA", "Social democratic", None),
    ("ES", r"PODEMOS|En Comu Podem|ECP-GUANYEM|^SUMAR", "Radical left",
     "Podemos"),
    ("ES", r"^C'S$", "Liberal", None),
    ("ES", r"^ERC-", "Regionalist", None),
    ("ES", r"^DL$", "Regionalist", None),
    # FR
    ("FR", r"Nouvelle union populaire|^Union de la Gauche$", "Radical left",
     None),
    ("FR", r"^Ensemble", "Liberal", None),
    ("FR", r"^RPR$", "Conservative", None),
    # GB
    ("GB", r"^Reform UK$", "Radical right", "BRX / Reform"),
    ("GB", r"^Green$", "Green", None),
    # GR
    ("GR", r"PASOK|Kinima Allagis", "Social democratic", None),
    ("GR", r"SPARTIATES", "Radical right", "Spartans"),
    ("GR", r"Enosi Kentroon", "Liberal", None),
    ("GR", r"MERA ?25", "Radical left", "MeRa25"),
    # HR (coalitions; families of the dominant partner)
    ("HR", r"KUKURIKU", "Social democratic", None),
    ("HR", r"^PATRIOTIC$", "Conservative", None),
    ("HR", r"GREEN-LEFT", "Green", None),
    ("HR", r"DPMS-LED", "Radical right", "DP"),
    ("HR", r"STRONGER ISTRIA", "Regionalist", None),
    ("HR", r"PAMETNO", "Liberal", None),
    ("HR", r"THE RIGHT TO OUR OWN|FOR PRIME MINISTER|THE ONLY OPTION",
     "No family", None),
    # HU
    ("HU", r"Osszefogas|MSZP-PARBESZED", "Social democratic", None),
    ("HU", r"United for Hungary", "No family", None),
    # IE
    ("IE", r"Solidarity-People Before Profit|Democratic Left",
     "Radical left", None),
    # IS (outside CHES coverage)
    ("IS", r"Sjálfstæðisflokkur", "Conservative", None),
    ("IS", r"Samfylkingin", "Social democratic", None),
    ("IS", r"Viðreisn", "Liberal", None),
    ("IS", r"Vinstrihreyfingin", "Radical left", None),
    ("IS", r"Framsóknarflokkur", "Agrarian/center", None),
    ("IS", r"Flokkur fólksins", "No family", "FIF"),
    ("IS", r"Miðflokkurinn", "Conservative", "M"),
    ("IS", r"Píratar", "No family", None),
    ("IS", r"Björt framtíð", "Liberal", None),
    ("IS", r"Sósíalistaflokkur", "Radical left", None),
    ("IS", r"Lýðræðisflokkur", "Radical right", None),
    # IT
    ("IT", r"^L'Ulivo$", "Social democratic", None),
    ("IT", r"Liga Lombarda", "Regionalist", None),
    # LT
    ("LT", r"Brazausko|Uz darba Lietuvai", "Social democratic", None),
    ("LT", r"Lietuvos valstieciu partija", "Agrarian/center", None),
    ("LT", r"Liberalu ir centro", "Liberal", None),
    ("LT", r"Nemuno Aušra|Nemuno Ausra", "Radical right", None),
    ("LT", r"Vardan Lietuvos", "Agrarian/center", None),
    ("LT", r"Darbo partija", "Liberal", "DP"),
    ("LT", r"Nacionalinis susivienijimas", "Radical right", None),
    ("LT", r"ANTI-CORRUPTION|Lietuvos liaudies partija", "No family", None),
    # LU
    ("LU", r"^PIRATEN$", "No family", None),
    ("LU", r"^Fokus", "Liberal", None),
    ("LU", r"Integral Demokratie|LIBERTÉ|LIBERTE", "No family", None),
    ("LU", r"Greng Lescht|déi Konservativ", "No family", None),
    ("LU", r"^VOLT$", "Liberal", None),
    # LV
    ("LV", r"APVIENOTAIS SARAKSTS", "Agrarian/center", None),
    ("LV", r"Latvijas Pirma partija", "Liberal", None),
    ("LV", r"Par Labu Latviju", "Conservative", None),
    ("LV", r"Saskaņa|Saskana", "Social democratic", None),
    ("LV", r"SUVERĒNĀ VARA", "No family", None),
    ("LV", r"Krievu savien", "Regionalist", None),
    ("LV", r"Latgales Gaisma", "Regionalist", None),
    ("LV", r"KATRAM UN KATRAI", "No family", None),
    ("LV", r"^STABILITĀTEI", "No family", "ST!"),
    # MT
    ("MT", r"Alternattiva Demokratika|AD ?\+ ?PD", "Green", None),
    # NL
    ("NL", r"GROENLINKS / Partij van de Arbeid", "Social democratic", None),
    ("NL", r"Nieuw Sociaal Contract", "Christian democratic", None),
    # NO (outside CHES coverage)
    ("NO", r"Arbeiderparti", "Social democratic", None),
    ("NO", r"H[øo]yre", "Conservative", None),
    ("NO", r"Senterpartiet", "Agrarian/center", None),
    ("NO", r"Kristelig Folkeparti", "Christian democratic", None),
    ("NO", r"Miljøpartiet|Miljopartiet", "Green", None),
    ("NO", r"^Venstre$", "Liberal", None),
    ("NO", r"Fremskrittspartiet", "Radical right", "FrP"),
    ("NO", r"Sosialistisk Venstreparti", "Radical left", None),
    ("NO", r"^Rødt$|^Rodt$", "Radical left", "Rodt"),
    ("NO", r"Avholdspartiet", "No family", None),
    ("NO", r"Industri- og Næringspartiet", "No family", None),
    ("NO", r"^Norgesdemokratene$", "Radical right", None),
    ("NO", r"Konservativt|Partiet De Kristne", "Christian democratic", None),
    ("NO", r"Pensjonistpartiet", "No family", None),
    # PL
    ("PL", r"^SLP-UP$|Lewica i Demokraci|^ZL$", "Social democratic", None),
    ("PL", r"TRZECIA DROGA", "Agrarian/center", None),
    # PT
    ("PT", r"PPD/PSD", "Liberal", None),  # aligned with EP-panel PSD
    # RO
    ("RO", r"Uniunea Social Liberala|PSD\+PUR", "Social democratic", None),
    ("RO", r"Dreptate si Adevar", "Liberal", None),
    ("RO", r"Alianta Romania Dreapta", "Conservative", None),
    ("RO", r"S\.O\.S\. ROM", "Radical right", "SOS"),
    ("RO", r"OAMENILOR TINERI", "Radical right", "POT"),
    ("RO", r"USR PLUS", "Liberal", None),  # 2020 USR-PLUS alliance
    # SE
    ("SE", r"^Moderaterna$", "Conservative", None),
    ("SE", r"^Centre Party$", "Agrarian/center", None),
    ("SE", r"^Liberalerna", "Liberal", None),
    # SI
    ("SI", r"Drzavljanska lista", "Liberal", None),
    ("SI", r"POVEŽIMO SLOVENIJO", "Conservative", None),
    ("SI", r"VESNA|trajnostni razvoj|Zeleni Slovenije", "Green", None),
    ("SI", r"NAŠA DEŽELA", "Agrarian/center", None),
    ("SI", r"Piratska|PIRATSKA", "No family", None),
    ("SI", r"Slovenija je nasa|Stranka Lipa|ZDRAVA DRUŽBA|"
           r"NAŠA PRIHODNOST|Dobra Drzava", "No family", None),
    # SK
    ("SK", r"OĽANO|OBYČAJNÍ ĽUDIA", "Conservative", None),
    ("SK", r"SZÖVETSÉG|ALIANCIA|^MKO$", "Regionalist", None),
    # TR (outside PopuList; standard assignments)
    ("TR", r"^AKP$", "Conservative", None),
    ("TR", r"^CHP$", "Social democratic", None),
    ("TR", r"^HDP$", "Radical left", None),
    ("TR", r"^MHP$", "Radical right", None),
    ("TR", r"^IYI PARTI$", "Conservative", None),
    ("TR", r"^GENC PARTI$", "No family", None),
    ("TR", r"^SAADET$", "Confessional/agrarian/other", None),
    ("TR", r"^DEHAP$|^DTP$|^BDP$", "Radical left", None),
    # flag fixes: PopuList-listed parties whose auto pfid variant lacked links
    ("DK", r"Danmarksdemokraterne", "Radical right", "DD"),
    ("GR", r"NIKI", "Radical right", "NIKI"),
    ("HU", r"^Fidesz", "Conservative", "Fidesz"),
]
