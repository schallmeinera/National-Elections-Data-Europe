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
    # MECh: PopuList lists it as far right, so "No family" was inconsistent.
    # The 2024 CIK source spells it "ПП МЕЧ", which the old pattern missed.
    ("BG", r"МОРАЛ, ЕДИНСТВО, ЧЕСТ|MECh|ПП МЕЧ", "Radical right", "MECh"),
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
    ("LT", r"Nacionalinis susivienijimas|^NATIONAL ALLIANCE$",
     "Radical right", None),
    ("LT", r"ANTI-CORRUPTION|Lietuvos liaudies partija|"
           r"^LITHUANIAN PEOPLE'S PARTY$", "No family", None),
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

    # ====================================================================
    # Every party reaching >=1% of any single election that the automatic
    # pipeline left with a null family. Sources: party name + national
    # election context; coalitions take the dominant partner's family, as
    # above. Residual official categories (misc-left, none-of-the-above)
    # get "No family" unless the label itself carries a direction, in which
    # case the direction is honoured (e.g. FR "Union de l'Extrême Droit").
    # AT
    ("AT", r"^VGO$", "Green", None),
    ("AT", r"^BIER$", "No family", None),
    ("AT", r"Burgerinitiative gegen die EU|^NEIN$", "No family", None),
    ("AT", r"^FRITZ$", "Liberal", None),
    ("AT", r"^JETZT$", "Green", None),
    # BE
    ("BE", r"^VIVANT$", "No family", None),
    # BG

    ("BG", r"Bulgaria Patriots|Patriotic Coalition Volya-NFSB|"
           r"natsionalno obedinenie", "Radical right", None),
    ("BG", r"Bulgarian Rise|Bulgarski Vazhod", "Radical right", "BV"),
    ("BG", r"Republikantsi za Balgariya", "Radical right", None),
    ("BG", r"THE LEFT!|Левицата", "Radical left", None),
    ("BG", r"СИНЯ БЪЛГАРИЯ", "Conservative", None),
    ("BG", r"СОЛИДАРНА БЪЛГАРИЯ", "Social democratic", None),
    ("BG", r"GET UP BG|Izpravi se\.BG", "Liberal", None),
    ("BG", r"Bulgarian Summer|ЦЕНТЪР|^NR$|^NV$|^KNR$|^PV$|^C-FD$|"
           r"MOVEMENT 21|EVROROMA|DOST ALL", "No family", None),
    ("BG", r"NO ONE|None of the Above|I do not support anyone",
     "No family", None),
    # CH
    ("CH", r"^FGA$", "Green", None),
    # CZ
    ("CZ", r"Stačilo|Stacilo", "Radical left", None),
    ("CZ", r"PRISAHA|PŘÍSAHA", "No family", None),
    ("CZ", r"Trikolora", "Radical right", None),
    ("CZ", r"^ZELENI$", "Green", None),
    ("CZ", r"^SPOZ$", "Social democratic", None),
    ("CZ", r"^SUVEREN", "Radical right", None),
    ("CZ", r"^SNK$", "Liberal", None),
    # DE
    ("DE", r"^BSW$|Bündnis Sahra Wagenknecht", "Radical left", None),
    ("DE", r"^dieBasis$", "No family", None),
    ("DE", r"^B90/GR$", "Green", None),
    # DK (ballot letters; the pfid fixes above pin the identities)
    ("DK", r"^B$", "Liberal", None),
    ("DK", r"^K$", "Christian democratic", None),
    ("DK", r"^FK$|^SK$", "No family", None),
    # EE
    ("EE", r"^EEKD$", "Christian democratic", None),
    ("EE", r"^EE$", "No family", None),
    # ES
    ("ES", r"^IU-UPEC$|^CUP-PR$", "Radical left", None),
    ("ES", r"SOCIALISTAS DE GALICIA|SOCIALISTA DE EUSKADI",
     "Social democratic", None),
    ("ES", r"EUZKO ALDERDI JELTZALEA", "Regionalist", None),
    # FI
    ("FI", r"^LIIKE$", "Liberal", None),
    ("FI", r"^IP$|^SEP", "No family", None),
    # FR (official "nuance" categories of the Interior Ministry)
    ("FR", r"^Union de l'Extr[êe]me Droit|^Droite souverainiste$",
     "Radical right", None),
    ("FR", r"^OTHER FAR-LEFT$|^Divers extr[êe]me gauche$|^Extr[êe]me Gauche$",
     "Radical left", None),
    ("FR", r"^Ecologistes$|^ECO$", "Green", None),
    ("FR", r"^MDM$|^CEN$|^Divers centre$|^Divers Centre$", "Liberal", None),
    ("FR", r"^MAJORITE PRESIDENTIELLE$|^MAJ$", "Conservative", None),
    ("FR", r"^OTHER LEFT$|^Divers gauche$|^Divers Gauche$|^GE\+\+$|^REEP$",
     "No family", None),
    # GR
    ("GR", r"^XANA$", "No family", None),
    # HR
    ("HR", r"HSP AS-HCSP", "Radical right", None),
    ("HR", r"BUZ-PGS-HRS", "Regionalist", None),
    ("HR", r"HSS-ZELENA STRANKA", "Agrarian/center", None),
    ("HR", r"SUCCESSFUL CROATIA|^UIO$", "No family", None),
    # HU
    ("HU", r"MIEP-JOBBIK", "Radical right", None),
    ("HU", r"^MSZMP$", "Radical left", None),
    ("HU", r"^MSZDP$", "Social democratic", None),
    ("HU", r"^ASZ$", "Agrarian/center", None),
    ("HU", r"^VP$", "Liberal", None),
    ("HU", r"MDNP-NEPPART", "Christian democratic", None),
    ("HU", r"^HVK$|^KP-CONS$|Megoldás Mozgalom", "No family", None),
    # IE
    ("IE", r"^AONTU$", "Conservative", None),
    ("IE", r"CATHOLIC DEMOCRATS", "Christian democratic", None),
    # IT
    ("IT", r"LEGA PER SALVINI PREMIER", "Radical right", "Lega"),
    ("IT", r"ALLEANZA VERDI E SINISTRA", "Green", None),
    ("IT", r"AZIONE - ITALIA VIVA", "Liberal", None),
    ("IT", r"ITALEXIT PER L'ITALIA", "Radical right", None),
    ("IT", r"ITALIA SOVRANA E POPOLARE|UNIONE POPOLARE|POTERE AL POPOLO",
     "Radical left", None),
    ("IT", r"POP-SVP-PRI-UD-PRODI|DEMOCRAZIA EUROPEA",
     "Christian democratic", None),
    ("IT", r"^PLI$|LISTA PANNELLA|PANNELLA-SGARBI|LA ROSA NEL PUGNO|"
           r"FARE PER FERMARE IL DECLINO", "Liberal", None),
    ("IT", r"MOVIMENTO PER L'AUTONOMIA", "Regionalist", None),
    ("IT", r"LA RETE-MOV|RETE - MOVIMENTO DEMOCRATICO", "No family", None),
    # LT
    ("LT", r"CHRISTIAN DEMOCRATIC UNION|LITHUANIAN CHRISTIAN DEMOCRATIC|"
           r"^CHRISTIAN PARTY$", "Christian democratic", None),
    ("LT", r"MODERATE CONSERVATIVE UNION", "Conservative", None),
    ("LT", r"UNION OF LITHUANIAN PEASANTS", "Agrarian/center", None),
    ("LT", r"Lietuvos žaliųjų|Lietuvos zaliuju", "Green", None),
    ("LT", r"Lietuvos regionų|Lietuvos regionu", "Regionalist", None),
    ("LT", r"YOUNG LITHUANIAS", "Radical right", None),
    ("LT", r"UNION YES|LIST OF LITHUANIA|FOR THE FAIR LITHUANIA|"
           r"PARTY OF CIVIC DEMOCRACY|LITHUANIA - FOR ALL|"
           r"Tautos ir teisingumo", "No family", None),
    # LV
    ("LV", r"^Konservatīvie$|^Konservativie$", "Conservative", None),
    ("LV", r"^SDS$|^SDLP$", "Social democratic", None),
    ("LV", r"^JD$|^PVL$|^VL$|Republika|Tautas varas|TAUTAS KALPI",
     "No family", None),
    # NL
    ("NL", r"^SP \(Socialistische Partij\)$", "Radical left", None),
    ("NL", r"^AOV$|^LN$", "No family", None),
    # NO
    ("NO", r"Demokratene i Norge", "Radical right", None),
    ("NO", r"^KYST$", "Agrarian/center", None),
    ("NO", r"^PP$", "No family", None),
    # PL
    ("PL", r"POLSKA JEST JEDNA|^PJKM$", "Radical right", None),
    ("PL", r"^UW$", "Liberal", None),
    ("PL", r"^PJN$", "Conservative", None),
    ("PL", r"BEZPARTYJNI SAMORZ", "No family", None),
    # PT
    ("PT", r"^ADN$", "Radical right", None),
    ("PT", r"^CDS$", "Conservative", None),
    ("PT", r"PCTP/MRPP|^PSR$", "Radical left", None),
    ("PT", r"^PSN$", "No family", None),
    # RO
    ("RO", r"SĂNĂTATE EDUCA|PARTIDUL ECOLOGIST", "Green", None),
    ("RO", r"FORȚA DREPTEI", "Conservative", None),
    ("RO", r"REÎNNOIM PROIECTUL EUROPEAN", "Liberal", None),
    ("RO", r"^PNGCD$", "Radical right", None),
    ("RO", r"^PNTCD$", "Christian democratic", None),
    ("RO", r"PUTERII UMANISTE", "Social democratic", None),
    ("RO", r"DREPTATE ȘI RESPECT", "No family", None),
    # SK
    ("SK", r"^Demokrati$", "Liberal", None),
    ("SK", r"^SDL$", "Social democratic", None),
    ("SK", r"^DV$|^99PERCENT$|^ZZDS$|^SSS NM$", "No family", None),
    # TR
    ("TR", r"^DYP$|^DP$|^ANAP$", "Conservative", None),
    ("TR", r"^SAADET PARTISI$", "Confessional/agrarian/other", None),
    ("TR", r"^DSP$", "Social democratic", None),
    ("TR", r"^YTP$", "Liberal", None),
    ("TR", r"^BBP$", "Radical right", None),
]

# ---------------------------------------------------------------------------
# Partyfacts identities to pin BEFORE the automatic name matching runs.
# Format: (country_code, name-regex, partyfacts_id).
#
# These are cases where the automatic matcher lands on a real but wrong party.
# The Danish 2022 source codes parties by ballot letter, and the letters
# collide with other parties' abbreviations: "A" (Socialdemokratiet, 27.5% of
# the vote) matched Alternativet and was classified Green, and "K"
# (Kristendemokraterne) matched Konservative Folkeparti. Belgium's CD&V is
# labelled with the 2004-07 CD&V/N-VA cartel name by EU-NED and so inherited
# Partyfacts 756, which PopuList in turn uses for N-VA -- putting N-VA's
# far-right flag on CD&V while N-VA itself carried none.
PFID_FIX = [
    # DK 2022 ballot letters -> the party that actually bears each letter
    ("DK", r"^A$", 379),     # Socialdemokratiet (not Alternativet)
    ("DK", r"^B$", 1507),    # Radikale Venstre
    ("DK", r"^K$", 53),      # Kristendemokraterne (not Konservative)
    ("DK", r"^Å$", 4070),    # Alternativet
    # BE
    ("BE", r"^CD&V$|^Christen-Democratisch & Vlaams / Nieuw-Vlaams", 604),
    # parties the matcher missed entirely
    ("IT", r"^LEGA PER SALVINI PREMIER$", 1221),
    ("NL", r"^SP \(Socialistische Partij\)$", 1363),
    ("CZ", r"^PRISAHA Roberta Slachty$|^PŘÍSAHA občanské hnutí$", 9002),
]

# Families applied unconditionally at the end, overriding whatever the
# automatic sources produced. Use only where the automatic family is wrong,
# not merely missing.
FAMILY_FIX = [
    ("GR", r"NIKI", "Radical right"),
    # CD&V is Christian democratic; "Regionalist" was inherited from the
    # cartel id it was wrongly matched to.
    ("BE", r"^CD&V$|^Christen-Democratisch & Vlaams / Nieuw-Vlaams",
     "Christian democratic"),
    # DK ballot letters, following PFID_FIX
    ("DK", r"^A$", "Social democratic"),
]

# PopuList 4.0 partyfacts links that point at the wrong party. Applied to the
# PopuList table before its flags are joined on.
# Format: (party_name_short, country_name, wrong_id, right_id_or_None).
POPULIST_PFID_FIX = [
    # PopuList gives N-VA the id of the 2004-07 CD&V/N-VA cartel (756);
    # Partyfacts 36 is N-VA proper.
    ("N-VA", "Belgium", 756, 36),
    # PopuList gives Poland's Congress of the New Right the id of Slovenia's
    # Zdruzena levica (4714), which put a far-right flag on a radical-left
    # list. No Partyfacts id for KNP is available here, so the link is
    # dropped rather than redirected.
    ("KNP", "Poland", 4714, None),
]
