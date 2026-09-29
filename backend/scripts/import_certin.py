import asyncio
import csv
import re
import sys
import uuid
from datetime import date
from sqlalchemy.future import select

# Adjust path so we can import from app
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.agency import Agency

csv_data = """certin_list_no,agency_name,address,website,phone,mobile,contact_person,email,source
1,AAA Technologies Ltd,"278-280, F-Wing, Solaris-1, Saki Vihar Road, Opp. L&T Gate No. 6, Powai, Andheri (East), Mumbai – 400072.",http://www.aaatechnologies.co.in,022-28573815 / 16,+91 8448295960,Mr. Jasmeet Bajaj,info[at]aaatechnologies.co.in,Empanel_org(1).pdf
2,AKS Information Technology Services Pvt Ltd,"B-21, Sector-59, Noida - 201309 (Uttar Pradesh)",https://www.aksitservices.co.in/,0120-4545911,+91-7290058951,"Mr. Ashish Kumar Saxena, Managing Director",enquiry[at]aksitservices.co.in,Empanel_org(1).pdf
3,AQM Technologies Pvt Ltd.,"A 401, Raheja Plaza, LBS Road, Nityanand Nagar, Ghatkopar West, Mumbai, Maharashtra 400086. INDIA",,022 4050 8200,+91 -9022663132 / 022-40508262,"Mr. Sachin Mirajkar, AVP InfoSec",sachin.mirajkar[at]aqmtechnologies.com,Empanel_org(1).pdf
4,Allied Boston Consultants India Pvt. Ltd.,"2205, Express Trade Towers-2, B-36, Sector 132, Noida Expressway, Noida 201301 (U.P.)",,"9891555625, 0120-4113529",9899589111,Mr. T. Ganguly,itsec[at]alliedboston.com,Empanel_org(1).pdf
5,A3S Tech & Company,"421-423, 4th Floor Devika Tower, Nehru Place, New Delhi - 110019",,9810899624,,Sagar Gupta,sagar[at]a3stech.co.in,Empanel_org(1).pdf
6,Andhra Pradesh Technology Services Ltd,"(Govt. of AP Undertaking) 3rd Floor, R&B Building, MG Road, Labbipet, Vijayawada, Andhra Pradesh 520010",https://www.apts.gov.in/,0866-2468121,9440469194,"K Raju, Principal Systems Analyst",mgr-apcsp-apts[at]ap[dot]gov[dot]in,Empanel_org(1).pdf
7,ANB Solutions Private Limited,"901,Kamla Executive Park, Off Andheri-Kurla Road, J. B. Nagar, Andheri East, Mumbai 400 059",,+91 (22) 4221 5300,,Preeti Raut,preeti.kothari[at]anbglobal.com,Empanel_org(1).pdf
8,Accenture Solutions Pvt. Ltd.,"Accenture BDC7C, Piritech Park (SEZ), Phase 1, RMZ Ecospace Internal Rd, Adarsh Palm Retreat, Bellandur, Bengaluru, Karnataka 560047, India",,+91- 9972556569,,Dheeraj Bhatia,dheeraj.a.bhatia[at]accenture.com,Empanel_org(1).pdf
9,ANZEN TECHNOLOGIES PVT. LTD.,"A-429, Second Floor, A-Wing, Vashi Plaza, Sector 17, Vashi, Navi Mumbai, 400703",,09821775814,,Ramesh Tendulkar,rtendulkar[at]anzentech.com,Empanel_org(1).pdf
10,Aujas Cybersecurity Limited,"#595, 4th Floor, 15th Cross, 24th Main Rd, 1st Phase, J. P. Nagar, Bengaluru, Karnataka 560078",,+91 96325 93399,,"Godwin Paul, Vice President – Delivery",Godwin.Paul [at] aujas.com,Empanel_org(1).pdf
11,AURISEG CONSULTING PRIVATE LIMITED,"No 17/22 Valliammai Street , Vijayalakshmi Nagar, Chrompet, Chennai - 600 044",,+91 99408 64275,,M.S SRINIVASAN - DIRECTOR -CONSULTING PRACTICE,SRINI.MANI[at]AURISEG.COM,Empanel_org(1).pdf
12,Army Cyber Group,New Delhi Ph No - 011 26151531 Mob No: 09958866453,,,,,tandelab22 [at] gmail.com,Empanel_org(1).pdf
13,Audix Techno Consulting Solutions Private Limited,"B-451, Orchid Corporate Park, Opp. TOPS Security Bldg., Royal Palms, Aarey Road, Gorgeaon East, Mumbai - 400065, Maharashtra, India.",,+91 9702249709,,Mr. Vivek Devendra Tiwari,vivek[at]audixindia.in,Empanel_org(1).pdf
14,AVASURE TECHNOLOGIES PVT. LTD.,"4-Chandra Jyoti, Bhimani Street, Matunga, Mumbai 400019.",,9820058628,,Mr. JAIVEEN MEHTA,jaiveen.mehta[at]avasuretechnologies.com,Empanel_org(1).pdf
15,Acquisory Consulting LLP,"1116, World Trade Tower, Sector 16, Noida-201301",,9911395751,,Sujeet Singh,saleshead[at]acquisory.com,Empanel_org(1).pdf
16,ANA Cyber Forensic Private Limited,"Office No. 3.1, 3.2, Dr. Herekar Park, Rajyog, 2nd Floor, C wing, Near Kamla Nehru Park, Pune, Maharashtra 411004",,+91-9011046490,,Mrs. Kailash Nevagi,kailash[at]anacyber.com,Empanel_org(1).pdf
17,Ankura Consulting India Private Limited,"20th Floor, Oberoi Commerz II, 1 Mohan Gokhale Road, Off Western Express Highway, Goregaon (East), Mumbai 400 063 Maharashtra, India",,+91 9820073695,,Amit Jaju,Amit.Jaju[at]ankura.com,Empanel_org(1).pdf
18,Arridae Infosec Private Limited,"C/O Regus World Trade Center Unit No 2201A, 22nd Floor WTC Bangalore, Brigade Gateway Rajajinagar Extension, Malleswaram Bangalore - 560055 Karnataka, India",,9686361842,,Pranab Jyoti Roy,pranab.roy[at]arridae.com,Empanel_org(1).pdf
19,Ameya Cyber Risk Solutions Pvt. Ltd.,"4th Floor, WoCo Spaces, No. 74, V Block, 5th Avenue, Anna Nagar, Chennai 600040",,+91 9500022813/ +91 9791004895,,"Gopalakrishnan Ganesan/ Rajan TV, Co-founder & Principal Consultant",gopal[at]ameyacrs.com/ rajan[at]ameyacrs.com,Empanel_org(1).pdf
20,Associated IT Consultants Private Limited,"Regd. address: Plot No. 32, Vasant Vishwas Park, Near Tapowan, Kolhapur. 416007. Office Address: CS No. 1592, E Ward, Flat No. 101, Sai Guru apartment, 5th Lane, Rajarampuri, Kolhapur. 416008.",,"+91 9881191441, +91 9422581553",,Mr. Sujit Joshi,"sujit[at]aitcpl.in, sujitaitcpl[at]outlook.com",Empanel_org(1).pdf
21,Astra Security (Czar Securities Pvt. Ltd.),"SCO No. 830 NAC, Manimajra, Chandigarh - 160101, India",,+91 7737371307,,"Ananda Krishna - CTO, Director",vapt[at]getastra.com,Empanel_org(1).pdf
22,ASA & Associates LLP,"18th Floor, G - 1801, Lotus Corporate Park, CTS No. 185/A, Graham Firth Complex. Western Express Highway, Goregaon East, Mumbai, Maharashtra, India",,+91 22 4921 4000,,Mr. Bhushan Sharma,bhushan.sharma[at]asa.in,Empanel_org(1).pdf
23,ASPL Info Services Private Limited,"No. 903/1/1, 19th Main Road, 4th Sector, H.S.R. Layout, Bangalore 560102, Karnataka, India",,+91-9901490796,,Ajay Badrinath,ajay.b[at]asplinfo.com,Empanel_org(1).pdf
24,AuthenticOne Cybersecurity Private Limited,"#265, 2nd Floor, 1st Main, 6th Cross, 1st Stage Domlur, Bengaluru, Karnataka - 560071",,+91 9160053350,,Kamal Sharma,kamal.sharma[at]authenticone.com,Empanel_org(1).pdf
25,Accedere Limited,"119 Andheri Industrial Estate, Off Veera Desai Road, Andheri West, Mumbai 400053",,+91 8169212554,,Abhishek Raghani,certin.presales[at]accedere.io,Empanel_org(1).pdf
26,Amigosec Consulting Private Limited (SynRadar),"Dev Corpora, Level 16, Off. Eastern Express Highway, Opp. Cadbury Junction, Thane(w), Maharashtra, India - 400601.",,+91-8655620121 / +91-8655620118,,Mr. Ashish Rao,ashish.p.rao[at]synradar.com,Empanel_org(1).pdf
27,ARM INNOVATIONS PRIVATE LIMITED,"A-105, FIRST FLOOR, TOWER A, LOGIX TECHNOVA, SECTOR 132, NOIDA, UTTAR PRADESH - 201301",,91-9278648782,,ARUN GUPTA,arun.gupta[at]arm-innovations.com,Empanel_org(1).pdf
28,Aurionpro Solution Limited,"Head Quarter:- Synergia IT Park, Rabale, Navi Mumbai – 400 701, Maharashtra, India Regional Office:- 7th Floor, B-704, Unitech Business Zone, Nirvana Central Road,Gurugram, Haryana – 122001",,+91-22-4040 7070,,Mr. Naman Chaturvedi,,Empanel_org(1).pdf
29,BHARAT ELECTRONICS LIMITED,"Office of GM/NWCS Network and Cyber Security Bharat Electronics Limited, Jalahalli Post, Bengaluru-560013 Karnataka. FAX No : 080-28381407",,,+91 9986344397,"Mr. Antony Benedict Raja G , Manager , NWCS",itsecurityauditteam[at]bel.co.in,Empanel_org(1).pdf
30,Bharti Airtel Service Limited,"Plot# 16, Udyog Vihar-Phase-IV Sector 18, Gurgaon-122016",,+91-9987891999,,Rana Singh,rana2.singh[at]airtel[dot]com,Empanel_org(1).pdf
31,BDO India LLP,"The Ruby, Level 9, North West Wing, 29, Senapati Bapat Marg, Dadar West, Mumbai, 400028.",,+91 022 62771600,,Mr. Ashish Gangrade / Mr. Virendra Singhi,AshishGangrade[at]bdo.in / VirendraSinghi [at]bdo.in,Empanel_org(1).pdf
32,Black Box Limited,"501, Gigaplex Building No.9, 5th Floor, Mindspace, Patni Road, Navi-Mumbai,Airoli West, Thane, Maharashtra, 40070",,022 66617272,,Mr Anant Bhat,anant.bhat[at]blackbox.com,Empanel_org(1).pdf
33,Briskinfosec Technology and Consulting Pvt Ltd,"No:21, 2nd Floor, Krishnama Road, Nungambakkam, Chennai - 600034",,8608634123,,Arulselvar Thomas,arul[at]briskinfosec.com,Empanel_org(1).pdf
34,Be4Breach,"179/1A, Wing B, Flat 104, Vanshree Society, Hadapsar, Pune. Pin: 411208, Maharashtra, India",,+91 75972 85151,,Nikhil Agarwal,contact[at]be4breach.com,Empanel_org(1).pdf
35,Bosch Global Software Technologies Private Limited (BGSW),"123, Industrial Layout, Hosur Road, Koramangala, Bengaluru - 560095, India",,+91-99528-41064,,Anish T S,Anish.TS[at]in.bosch.com,Empanel_org(1).pdf
36,BharatCyber Solutions LLP,"8 A P Misquitta House ,Tarun Bharat Society ,Chakala, Andheri(east), Mumbai-400099",,+91 758 8765432,,Bharat Pandiya,admin[at]bharatcyber.solutions,Empanel_org(1).pdf
37,Bug Hunters Private Limited,"G-04, 04A, 05 & 07 SSR Corporate Park 13/6, Mathura Road, Sector-27B, Faridabad, Haryana - 121003",,+91 9953575857,,Sachin Arora,sachin[at]bughunters.io,Empanel_org(1).pdf
38,Centre for Development of Advanced Computing (C - DAC),"Plot No. 6 & 7, Hardware Park, Sy No. 1/1, Srisailam Highway, Pahadi Shareef Via Keshavagiri (Post), Hyderabad - 501510",,9100034448 (Ext.310),,"Mr. Rakesh Katakam, 8332001999",cswan[at]cdac.in,Empanel_org(1).pdf
39,Crossbow Labs LLP,"Unit 406, Brigade IRV Center, Nallurhalli, Whitefield, Bangalore Karnataka 560066, India",,"+91 80 470 91427 , +917259385008",,Mr. Deepak Umapathy,deepak.umapathy[at]crossbowlabs.com,Empanel_org(1).pdf
40,CyRAAC Services Private Limited,"2nd Floor, Napa Prime, 7/24, 11th Main Road, 4th Block East, Jayanagar, Bengaluru - 560011",,+919886210050,,Mr. Murari Shanker,ms[at]cyraacs.com,Empanel_org(1).pdf
41,Codec Networks Pvt. Ltd.,"507, New Delhi House, Barakhamba Road, New Delhi - 110001",,"+91 9971676124, +91 9911738718",,Mr. Piyush Mittal,amittal[at]codecnetworks[dot]com; piyush[at]codecnetworks[dot]com,Empanel_org(1).pdf
42,Cyber Security Works Pvt. Ltd.,"No.6, 3rd Floor, A-Block, IITM Research Park Taramani, Chennai – 600 113",,+91-44-42089337,,"Mr. Ravi Pandey, Senior Director, Security Services",rpandey[at]cybersecurityworks.com,Empanel_org(1).pdf
43,CEREIV Advisory LLP,"Chembakam Building, Koratty Infopark, Thrissur Dt, Kerala - 680 308",,9745767949,,Mridul Menon,mridul[at]cereiv.com,Empanel_org(1).pdf
44,ControlCase International Pvt. Ltd.,"Corporate Center, Level 3, Andheri-Kurla Road, Marol, Andheri (East), Mumbai 400059, Maharashtra.",,+91 22 6647 1800,,Mr. Satya Rane,infosecaudit[at]controlcase.com,Empanel_org(1).pdf
45,CyberSRC Consultancy Private Limited,"Unit no 605, 6th floor, World Trade Tower, Sector 16 Noida - Uttar Pradesh 201301",,"+91 8800377255, +91 120 4160448",,"Vikram Taneja, CEO","vikram[at]cybersrcc.com , info[at]cybersrcc.com",Empanel_org(1).pdf
46,Code Decode Labs,"A-302-402, ‘Runwal Sanket’, Beside Zudio Store, Ganaraj Chowk, Baner, Pune – 411045 (MAH), India.",,- +91-9975682646,,Alisha / Yogita,audits[at]codedecodelabs.com / vivaan[at]codedecodelabs.com,Empanel_org(1).pdf
47,CYBERNERDS SOLUTIONS PRIVATE LIMITED,"Ground Floor, NerdsHive, Vetri E-Square, Behind New Bus Stand, Vallam Quarry Road, Thanjavur, Tamilnadu - 613005",,+91 8807258558,,Siva,security[at]cybernerds.in,Empanel_org(1).pdf
48,CoreIT Services Pvt Ltd,"1st Floor, Badheka Chambers 31, Manohardas Street, Near Pancham Puriwala, Fort, Mumbai - 400001 INDIA",,022 40065252,"+91 9821123389, 9920561969",Mr. Parag Nandimath,"pnandimath[at]coreitx.com, sgaikwad[at]coreitx.com",Empanel_org(1).pdf
49,Dr CBS Cyber Security Services LLP,"113, Suraj Nagar East, Civil Lines, Jaipur, Rajasthan-302006",,"0141-2229475, +91- 9414035622, 9828877777",,Dr C B Sharma IPS Retd.,contact[at]drcbscyber.com,Empanel_org(1).pdf
50,cyberSecurist Technologies Pvt. Ltd,"Office Address:- Vasant Vihar, Plot 59, off, Senapati Bapat Road Shivaji Co. Operative Housing Society. Pune,Maharashtra, India 411016 Registered Office Address:- Regd. Office: #20 Cinderella Bungalows, S.No. 39/3,Nr Peony Apartment, Baner, Pune – 411045.Maharashtra, INDIA.",,9595816884,,Mr. Mahesh Saptarshi,mahesh[at]cybersecurist.com/Sachin.k[at]cybersecurist.com,Empanel_org(1).pdf
51,Cybertryzub Infosec Pvt Ltd,"Plot No 76d Udyog Vihar 4 Sector 18,Gurgaon – 122001 Haryana, India",,"+91 9990887992, +91 7988006096",,Mr. Shubham Raj Mourya,"shubham.raj[at]cybertryzub.com,info.audit[at]cybertryzub.com",Empanel_org(1).pdf
52,CyberNX Technologies Pvt Ltd,"Unit # 43, 2nd Floor, Sumatinath Industrial Estate, Chincholi Bunder Road, Mind Space, Malad (W) 400064 Mumbai, MH, India",,022-40231687 | 022-40231363,+91-9987870222,"Bhowmik Shah, CTO and Co-Founder",bhowmik.shah[at]cybernx.com,Empanel_org(1).pdf
53,"Crowe Advisory Services (India) LLP,","1105 Embassy Centre, Nariman Point, Mumbai 400021, India, Maharashtra.",,+91 98450 40000,,Abhijeet Nath,abhijeet.nath[at]crowe.in,Empanel_org(1).pdf
54,CyberCube Services Pvt. Ltd.,"Plot No - 190, Second Floor, Udyog Vihar Phase - IV, Sector 18, Gurugram, Haryana - 122015",,"+91-9891675123, +91-9996022274",,Anil Kumar,anil[at]cybercube.co.in,Empanel_org(1).pdf
55,Certcube Labs Pvt Ltd,"3500, 1st floor, Raja Park, New Delhi-110034",,"9999508202, 7727874562",,"Naresh Singh, Richa Aggarwal","Naresh.singh[at]certcube.com, Consulting[at]certcube.com",Empanel_org(1).pdf
56,Cybersigma Consulting Services LLP,"E-1403, Wallrock Aishwaryam, Gaur City-2, Gautam Budha Nagar, Ghaziabad, U.P. - 201016 Corporate Office Location in India: C-320 Tower C, KLJ Noida One, Noida, 201309.",,+91 8076949229,,Neha Abbad ( +91 9975301963 ),neha[at]cybersigmacs.com,Empanel_org(1).pdf
57,CYBERSMITH SECURE PRIVATE LIMITED,"House No.1107, Niwant, Visrodi, Agashi, Thane MH 401301 Maharashtra INDIA 401301.",,+91 95032 59778,,Smith Gonsalves,smith.gonsalves[at]cybersmithsecure.com,Empanel_org(1).pdf
58,CyberXchange Private Limited,"A 12, S/F, West Patel Nagar, New Delhi 110008",,+919871144626 / +919873264886,,Rajinder Singh,rajinder.singh[at]cyberxchange.in,Empanel_org(1).pdf
59,Cynox Security LLP,"332,3rd Floor, Ashiana Trade Centre, Adityapur, Jamshedpur, Jharkhand 831013",,"7303347098, +91-6577964531",,Rishu Kumar,rishu.kumar[at]cynoxsecurity.com,Empanel_org(1).pdf
60,Climate ETC Technology Services Private Limited,"NO 4/1, 8TH & 9TH Floor, Tower C & D, IBC Knowledge Park, Bannerghatta Main Road, Bengaluru, Karnataka-560029",,08067476000,,Arvind Chikmath,Arvind.Chikmath[at]tranetechnologies.com,Empanel_org(1).pdf
61,ConsultEdge Global Services (OPC) Private Limited,"Magnum Tower – 2 | Unit No - 901 | 9th Floor Golf Course Extension | Sector 58 | Gurugram, Haryana-122011, India",,+91 8448296800/01,,,,Empanel_org(1).pdf
62,Cypros Technologies Private Limited,"GR Samriddhi, No.273, 1st Floor, 7th Cross, Basavanapura Main Rd, near Silicon City College, Krishnarajapuram, Bengaluru, Karnataka – 560036.",,9964722968,,Mr. Nagaraja M (9538591980) / Mr. P Rakesh Shenoy (97423 53695),"info[at]cypros.in, nagaraja.m[at]cypros.in, rakesh.shenoy[at]cypros.in",Empanel_org(1).pdf
63,Certbar Security Private Limited,"409-410, Sunday Hub, Amba talavadi, Katargam, Surat, Gujarat - 395004",,+91 63537 89955,,Nirav Goti,n[at]certbar.com,Empanel_org(1).pdf
64,Cyethack Solutions Private Limited,C2-815 8th floor Gardenia Gateway Plot-9 Sector-75 Noida UP 201301,,7223820107 / 7909458351,,Shivbihari Pandey,shivbh[at]cyethack.com,Empanel_org(1).pdf
65,Cuttingej Solutions India Private Limited,"Plot 224, Ramdaspeth, Behind KRIMS Hospital, (PO - Shankar Nagar), Nagpur, Maharashtra 440010",,+91 99869 42540,,"Mayank Umbarkar, Vishakha Adkar, Phanindra Kumar Kopparapu. (9052355444)","mayank.umbarkar[at]cuttingej.com, phanindrakumar.kopparapu[at]cuttingej.com ,",Empanel_org(1).pdf
66,9USRcraft,"8th Floor, Niharika Mirage, Plot No 274 Sector 10, Kharghar, Navi Mumbai, Maharashtra 410210",,+919222200009,,Parikshit Kathale,parikshit.k[at]9usrcraft.com,Empanel_org(1).pdf
67,Deloitte Touche Tohmatsu India LLP,"7th Floor, Building 10, Tower B, DLF Cyber City Complex, DLF City Phase II, Gurgaon, Haryana, India",,+91 9810618871,,Mr. Digvijaysinh Chudasama,dchudasama[at]deloitte.com,Empanel_org(1).pdf
68,DigitalTrack Solution Pvt Ltd.,"No: 9, Vinayakar Koil Street, Venkatapuram, Little Mount, Saidapet, Chennai – 600015",,044-66292222,,Vijay Iyer,vijay[at]digitaltrack.in,Empanel_org(1).pdf
69,DREAMWORKS INFOTECH PRIVATE LIMITED,"277K-5, Dam Side Road, Near Vodafone Tower Pajhra Toli, Kanke Ranchi Ranchi JH 834006 INDIA",,9534042175,,DEONANDAN ORAON,"support[at]dwinfotech.in, dir[at]dreamworksinfotech.com",Empanel_org(1).pdf
70,Digital Age Strategies Pvt. Ltd,"28, Om Arcade, 2nd & 3rd Floors, Thimmapa Reddy Layout, Hulimavu, Bannerghatta Road Bangalore - 560076",,"9448088666, 8095488666, 9448055711",,Mr. Dinesh S Shastri,audit[at]digitalage.co.in / dinesh.shastri[at]digitalage.co.in,Empanel_org(1).pdf
71,DigiFortex Technologies Private Limited,"A207, Sterling Shalom, ITPL Main Road, Brookefields, Kundalahalli Colony, Bangalore - 560037, Karnataka",,9448353194,,Vijay Kumar,vijay[at]digifortex.com,Empanel_org(1).pdf
72,Deccan Infotech (P) Ltd.,"13, Jakkasandra block. 7th cross. Koramangala. Bengaluru - 560034",,080 - 2553 0819,,Mr. Dilip Hariharan,dilip[at]deccaninfotech.in,Empanel_org(1).pdf
73,DARKNEXT LLP,"RIIDL, K.J.Somaiya Institute of Technology, Eastern Express Highway, Near Everard Nagar, Sion East, Mumbai 400022 Registered Office Address: 15 A, Fairlawn, Diamond Garden, Chembur, Mumbai 400071.",,9820380225,,Lalit Vazirani,Lalit.vazirani[at]darknext.com,Empanel_org(1).pdf
74,Defhawk TechServices Private Limited,"500 P, ground floor, sector 39, Bakhtawar chowk, Gurgaon, Sadar Bazar, Gurgaon- 122001, Haryana",,8708209880,,"Gitesh Sawariya, E-mail : gitesh[at]defhawk.com",gitesh[at]defhawk.com,Empanel_org(1).pdf
75,eSec Forte Technologies Pvt. Ltd.,"Plot No. 888, Phase V, Udyog Vihar, Sector 20, Gurugram, Haryana 122008",,+91 9871699555,,Kunal Bajaj,kunal[at]esecforte.com,Empanel_org(1).pdf
76,Ernst & Young LLP,"601, 6th Floor World Mark 1 Asset 11 Hospitality District Aerocity, Delhi – 110037",,,9971496366,"Mr. Navin Kaul, Partner – Consulting",Navin.kaul[at]in.ey.com,Empanel_org(1).pdf
77,ESF LABS LIMITED,"D.No:1-624/2,Bank Colony, Chilakaluripet, Guntur District, Andhra Pradesh, India. PIN-522616",,9930369920 / 9963971531,,Mr. Anil,anil[at]esflabs.com,Empanel_org(1).pdf
78,Entersoft Information Systems Private Limited,"Unit No. 1607, 16th Floor, Orbit, Plot No. 30C, Sy. No. 83/1, Hyderabad Knowledge City, TSIIC, Madhapur, Hyderabad, Shaikpet, Telangana – 500081, India.",,+91-9573777145,,Sri Chakradhar Kurmapu,chakri[at]entersoftsecurity.com,Empanel_org(1).pdf
79,Expleo Solutions Limited,"Plot 25/1, Rajiv Gandhi IT Park, Hinjewadi Phase III, Pune, Maharashtra 411057, India",,,,"Mr. Srinivasarao Yeluri, Associate Capability Director – Project & Delivery Management",srinivasarao.yeluri[at]expleogroup.com,Empanel_org(1).pdf
80,eSecurify Technologies LLP,"G-110, Titanium City Center, Near Sachin Tower, Anand Nagar Road, Ahmedabad - 380015",,+919033443715 / +917016810295,,Smit Shah,"smit[at]esecurify.com, smitbshah92[at]gmail.com",Empanel_org(1).pdf
81,EVANTI TECH PRIVATE LIMITED,"Unit-3012, F12,Eaze Zone,Off Link Road, Goregaon West, Mumbai,MH 400062 INDIA",,8169624284/9916227338,,Laheree Goswami,admin[at]evanti.in,Empanel_org(1).pdf
82,Eventus Security Private Limited,"#604, 605, 606, Kesar Solitaire, Palm Beach Road, Sector 19, Sanpada, Navi Mumbai, Maharashtra - 400705",,8655785625,,MANISH CHASTA,manish.chasta[at]eventussecurity.com,Empanel_org(1).pdf
83,"Fortune4 Expert Advisors,","A 2404 - C, Marathon Futurex, NM Joshi Marg, Lower Parel East, Mumbai - 400013",,+91 9833097663/ +91 7689925734,,Rohit Date/ Virendra Singh,rohit[at]astra,Empanel_org(1).pdf
84,Five Tattva Cyberhub Security LLP,"SCO-33, Second & Forth Floor, M3M 113 Market, Sector 113, Dwarka Expressway, Gurgaon – 122017, Haryana",,+91-9999039290 / +91-9811784254,,Manpreet Singh,manpreet[at]5tattva.com,Empanel_org(1).pdf
85,Forensic CyberTech Private Limited,"7th Floor, Shivarth The Ace, Besides Courtyard by Marriott, Sindhu Bhavan Road, Ahmedabad – 380053.",,+91 9099556604,,Rushit Soni,rushit.soni[at]forensiccybertech.com,Empanel_org(1).pdf
86,GRM Technologies Private Limited,"Postal address: Corporate address: Old No, 2/127,Mani Sethupattu, Sriperumbudur Taluk, Kanchipuram District, Chennai -601 301 Tamil Nadu. India.. Branch Office address: No-9, 2nd floor Shoba Homes, Gokul Nagar West Tambaram, Chennai600045,India.",,"+91-9042000525, +91-9042645524, +91-44-27174225, +91-44-22261489",,"Mr. Babu G, Director, Cyber Services","babug[at]grmtechnologies.com, cyber[at]grmtechnologies.com",Empanel_org(1).pdf
87,Grant Thornton Bharat LLP,"L 41, Connaught Circus, Outer Circle, New Delhi. PIN - 110 001",,0124-4628000 (Ext. 277),+91 9820208515,"Mr. Akshay Garkel, Partner Cyber",Akshay.Garkel[at]IN.GT.COM and cyber[at]IN.GT.COM,Empanel_org(1).pdf
88,G-Info Technology Solutions Pvt. Ltd.,"Plot no. 144, 3rd Floor, Pocket -11, Sector-24, Rohini, Delhi-110085",,9810956838,,Naveen Dham,naveen.dham[at]gisconsulting.in / Info[at]gisconsulting.in,Empanel_org(1).pdf
89,G. D. Apte & Company,"Head Office: D -509, Neelkanth Business Park, Nathani Road, Vidyavihar West, Mumbai – 400 086 Branch Office: GDA House, Plot No. 85, Right Bhusari Colony, Paud Road, Pune 411 038.",,+9122 3512 3184,,"CA Saurabh S. Peshwe,Partner",saurabh.peshwe[at]gdaca.com,Empanel_org(1).pdf
90,GlobalTech & Infosec Pvt Ltd.,"6th Floor, VSR Avenue, Unit No. 601–604, Sector 114, Bajghera, Gurugram, Haryana – 122017",,+91 9818398494,,Nishikant Singh,nishikant[at]gtisec.com,Empanel_org(1).pdf
91,Globals ITES Private Limited,"6th Floor, Brigade Senate, 2, Outer Ring Rd, Hebbal Kempapura, Bengaluru, Karnataka 560024",,99459675610,,Ganaindar Daliwal,ganender.d[at]globalsinc.com,Empanel_org(1).pdf
92,Happiest Minds Technologies Limited,"SMILES 1, SJR Equinox, Sy.No.47/8, Doddathogur Village, Begur Hobli, Electronics City Phase 1, Hosur Road, Bengaluru – 560 100",,"+91 80 61960300, +91 80 61960400",,"Vijay Bharti, SVP & CISO",vijay.bharti[at]happiestminds.com,Empanel_org(1).pdf
93,HONEYWELL AUTOMATION INDIA LIMITED,"56 57, Hadapsar Industrial Estate, Hadapsar, Pune, Maharashtra, 411013",,+91-9689911631,,Shailesh Garbhe- (Sales Director),shailesh.garbhe[at]honeywell.com,Empanel_org(1).pdf
94,HackIT Technology And Advisory Services,"64/2453, 2nd Floor, JVC Tower, Kaloor-Kadavanthara Road Kaloor PO, Cochin, Kerala, India PIN - 682 017",,(+91) 484 4044 234,94962 09743,Allen Jose James,"Projects[at]hackit.co , Allen[at]hackit.co",Empanel_org(1).pdf
95,Hitachi Systems India Private Limited,"Plot No-126-A, Kh.no - 1183 and 1177, Pkt-5, B-Block, Rangpuri, New Delhi, Delhi, 110037.",,+91-98716 90901,,Vivek Gupta,vivek.gupta.ac[at]hitachi-systems.com,Empanel_org(1).pdf
96,HiTrust Infotech Solution Private Limited,"Level 1, Khasra No 187, Near Mahaveer Bhawan, Rithala, Pocket-11, Sector 5, Rohini, New Delhi, Delhi 110085",,9891178809,,Mr. Gaurav Masih,gaurav[at]hitrustinfotech.com,Empanel_org(1).pdf
97,HKIT Security Solutions,"Site 192, 13th Cross, Jayasurya Nagar Phase I, Gastikempanahalli, Jakkur Post, Bangalore PIN 560 064",,+91-9845568869,,Dr. Harsha,harsha[at]hkit.in,Empanel_org(1).pdf
98,HackersFood Private Limited,"First Floor, H. No. 351, HACKERSFOOD PRIVATE LIMITED, Thakur Brajpal Singh Govt. Hospital, Dataganj, Budaun, Uttar Pradesh, 243635",,+91 - 7830206338,,Sagar Goyal,sagar[at]hackersfood.com,Empanel_org(1).pdf
99,ITORIZIN TECHNOLOGY SOLUTIONS PVT. LTD.,"8/14, SHAHID NAGAR, GROUND FLOOR. WING “A”. KOLKATA – 700078. West Bengal, India",,9883019472,,Sangeeta Ganguly,g.sangeeta[at]itorizin[dot]in / connect[at]itorizin[dot]in,Empanel_org(1).pdf
100,Innovador Infotech Private Limited,"4th Floor, New Janpath Complex, Ashok Marg, Lucknow – 226001, (Uttar Pradesh)",,"+91-8896605755, 7080259900, 7080239900",,Rahul Mishra,"rahul[at]innovadorinfotech.com, contact[at]innovadorinfotech.com, cybercoprahul[at]gmail.com",Empanel_org(1).pdf
101,ISECURION Technology & Consulting PVT LTD,"2nd floor, #670, 6th Main Road, RBI Layout, J.P. Nagar 7th Phase, opp. Elita Promenade, Bengaluru, Karnataka 560078",,8861201570,,Manjunath NG,manjunath[at]isecurion.com,Empanel_org(1).pdf
102,IHUB NTIHAC Foundation (C3iHub),"C3iHub, 2nd Floor, Technopark Phase I, IIT Kanpur Kanpur - 208016 , Uttar Pradesh, India",,9416212814,,"Ras Dwivedi, Sr. Vice President (Blockchain)",ras[at]c3ihub.iitk.ac.in,Empanel_org(1).pdf
103,Imperium Solutions,401 Maruti Bhavan Ram Maruti Road Naupada Thane(W) 400602,,9870484240 / 9324210232,,Ms Tasneam P / Mr Murtuza Laheri,tasneam[at]imperiumsolution.com / murtuza[at]imperiumsolution.com,Empanel_org(1).pdf
104,Indusface Pvt. Ltd.,"A-2/3, 3rd Floor, Status Plaza, Opp. Relish Resort, Atladara Old Padra Road, Vadodara - 390020, Gujarat, India.",,+91 265 6133021,,"Mr. Jayesh Kumar Warier, VP of Sales",Sales[at]Indusface.com,Empanel_org(1).pdf
105,Infopercept Consulting Private Limited,"3rd floor, Optionz Complex Opp. Hotel Regenta, CG Road, Navrangpura, Ahmedabad - 380 009, Gujarat",,Fax,+91 9033955155,Mr Jaydeep Ruparelia,jaydeepr[at]infopercept.com,Empanel_org(1).pdf
106,Inspira enterprise India Ltd,"23 & 31, Kalpataru Square, Kondivita Lane, Andheri East, Mumbai - 400 059",,Fax,,"Phani Mudigonda, Vice President and Chief Information Officer (CIO)",Phani.mudigonda[at]inspiraenterprise.com,Empanel_org(1).pdf
107,ISOAH Data Securities Private Limited.,"Kariwala Towers, 4th Floor, Plot J/1-5, Block EP, Sector-V, Salt Lake City, Kolkata – 700091",,+91-9830310550,,Gulab Mondal,gulab[at]isoeh.com,Empanel_org(1).pdf
108,Intelliroot Technologies (OPC) Private Limited,"27th Main Road, Sector 2, HSR Layout 2nd and 5th Floor, 1685, Bengaluru, Karnataka 560102",,+91 99453 35857 and +91 89290 42052,,Priyabrata Mohanty,mohanty[at]intelliroot.com,Empanel_org(1).pdf
109,IBM India Pvt. Ltd.,"No.12, Subramanya Arcade , Bannerghatta Main Road, Bengaluru, India – 560029",,080 26788015,,Harsh Pant - IBM Security X-Force Red ( VAPT ) Leader - India & South Asia,harsh.pant[at]ibm.com,Empanel_org(1).pdf
110,IITM Pravartak Technologies Foundation,"B5 - 01, B - Block, 5th Floor, IIT Madras Research Park, Kanagam Road, Taramani, Chennai – 600113",,+91 9840882964,,Dr.M.J.Shankar Raman,ceo[at] iitmpravartak.net,Empanel_org(1).pdf
111,IEMA Research & Development Private Limited,"Unit - 601, Godrej Genesis Building, Block EP & GP, Sector V, Kolkata - 700091",,+91 98319 78317,,Mr. Sovik Sinha,coo[at]iemlabs.com,Empanel_org(1).pdf
112,INFOCUS IT CONSULTING PRIVATE LIMITED,"A-19 Yadav Park , Behind Bank of Baroda , Rohtak Road , West Delhi Behind: Bank of Baorda,Delhi -110041",,"8800827932 , 9266047050",,Jagbir Singh,Jagbir[at]infocus-it.com,Empanel_org(1).pdf
113,InventOnUs Tech Pvt Ltd,"1018, Sushma Apartment, Ground Floor, Shukrawar Peth, Tilak Road, Swargate, Pune 411002.",,+91 7588245200 / +91 7975612277,,Keataan Shah,iou[at]inventonus.com,Empanel_org(1).pdf
114,INNSPARK SOLUTIONS PRIVATE LIMITED,"CP / XII / 482, Clappana P.O, Kollam, Kerala, India, 690525",,"+91 6238609449, 0476 2805497",,Govindamrit G,govindamrit[at]innspark.com,Empanel_org(1).pdf
115,Jio Platforms Limited,"10th Floor, TC 23, Block A, Reliance Corporate Park, MIDC Industrial Area, Ghansoli, Navi Mumbai, Maharashtra 400701",,+919082961964,,Mr. Ravi Burlagadda,ravi.burlagadda[at]ril.com,Empanel_org(1).pdf
116,John and Smith Solutions LLP,"Government Cyberpark, KSITIL Special Economic Zone, Kozhikode, Kerala PIN: 673016",,"+91(0)4952999131, +91 9746004949",,Rahul Raju,"rahul[at]johnandsmith.co.in, audits[at]johnandsmith.co.in",Empanel_org(1).pdf
117,JHS & Associates LLP,"Exit No.3, Tecno, Naka Metro Station, B Wing 4th Floor, Navarkar Chambers, Marol, Andheri East, Mumbai, Maharashtra 400059",,9820051936/8169021958,,Huzeifa Unwala/Taher Pepermintwala,huzeifa.unwala[at]jhsassociates.in/taher.pepermintwala[at]jhsassociates.in,Empanel_org(1).pdf
118,KPMG Assurance and Consulting Services LLP,"DLF Building No. 10, 8th Floor, Tower C, DLF Cyber City, Phase 2, Gurgaon, Haryana-122002",,+91 124334 5162,+91 9818199432,"Mr. Manish Tembhurkar, Partner Cyber Defense and Incident Response",mtembhurkar[at]kpmg.com,Empanel_org(1).pdf
119,Kochar Consultants Private Limited,"Office no : 302, Swapna Bhoomi Building, A Wing, S.K. Bole Road, Near Portuguese Church, Dadar West, Mumbai: 400028.",,,9819845198,Mr. Piyush Kochar,,Empanel_org(1).pdf
120,KRATIKAL TECH LIMITED,"B-70, Second Floor, Sector 67, NOIDA, Uttar Pradesh — 201301",,"7042292081, 9651506036",,Pavan Kumar / Paratosh Kumar,pavan[at]kratikal.com / paratosh[at]kratikal.com,Empanel_org(1).pdf
121,KERALA STATE ELECTRONICS DEVELOPMENT CORPORATON LIMITED,"Information Technology Business Group Keltron House, Vellayambalam Thiruvananthapuram 695 033",,"0471- 4094444 Extn:724 , 760",,Aswathi Mohanan,cybersecurity[at]keltron.org,Empanel_org(1).pdf
122,Kirtane & Pandit LLP,"601, 6th Floor, Earth Vintage Building, Senapati Bapat Marg, Dadar West, Mumbai, 400028",,7777080848,,Bhakti Dalbhide,bhakti.d[at]kirtanepandit.com,Empanel_org(1).pdf
123,K7 Enterprise Security Private Limited,"2nd Floor, Tower C, Tek Meadows, 51, Rajiv Gandhi Salai (OMR), Sholinganallur, Chennai - 600119.",,+91-44-6611-7777,,Ms. Rathna Kalidas,rathna[at]k7computing.com,Empanel_org(1).pdf
124,"Kerala University of Digital Sciences, Innovation and Technology.","Technopark Phase IV, Pallipuram, Thiruvananthapuram Kerala – 695317",,"0471-2788072 / 2788049, 9447582856, 9496848602",,Md Meraj Uddin and Anu Sivarajan,meraju[at]duk.ac.in and anu.sivarajan[at]duk.ac.in,Empanel_org(1).pdf
125,Kalkin Intelligence Private Limited,"Plot No.20, Block: H-1/A, Sector-63, Noida-201301, Uttar Pradesh (India)",,9910536888,,Mr. Pankaj Kumar Singh,Pankaj.singh[at]kalkin.io,Empanel_org(1).pdf
126,KCyber Experts Pvt. Ltd.,"Plot No. 246-A, GPO Road, Civil Line, Nagpur, Maharashtra - 440001",,"0712-2990109, 7767045215",,Mr. Akshay Gorle,"info[at]kcyberexperts.com, akshay[at]kcyberexperts.com",Empanel_org(1).pdf
127,Levithan Technologies private Limited,"Office No 205, Second Floor, SSR Corporate Park, 13/6 Mathura Road, Sector 27B, Faridabad, Haryana - 121003",,+91-9718047400,,Sh. Varun Bansal,varun.bansal[at]levithan.tech,Empanel_org(1).pdf
128,LORCAM SOLUTIONS PRIVATE LIMITED,"B28, SECOND FLOOR, SECTOR 1, NOIDA, UTTAR PRADESH - 201301",,"8448897649, 7858084550",,ROSE SINGH,info[at]lorcamsecurities.com,Empanel_org(1).pdf
129,Mahindra Special Services Group,"(Division of Mahindra Defence Systems Limited) Mahindra Towers, P.K Kurne Chowk, Dr. G.M Bhosale Marg, Worli, Mumbai - 400018, India",,+91 8652848222,,Mr. Chandrasekhar Konangi,Konangi.chandrasekhar[at]mahindra.com,Empanel_org(1).pdf
130,Maverick Quality Advisory Services Private Limited,"123 RADHEY SHYAM PARK P.O SAHIBABAD Ghaziabad, U.P, INDIA – 201005",,9871991928,,"Mr. Ashok Vardhan,Director",ashok[at]mqasglobal.com,Empanel_org(1).pdf
131,Madhya Pradesh State Electronics Development Corporation (MPSEDC),"(A Regt. Society of Department of Science & Technology, Government of Madhya Pradesh) 47-A , State IT Center, Arera Hills, Bhopal, Madhya Pradesh- 462011",,"0755 2518534, 0755 2518531, 0755 2518546",,"Mr. Ambar Pande, Principal Consultant, MPSeDC",ambar[dot]pande[at]mpsedc[dot]mp[dot]gov[dot]in,Empanel_org(1).pdf
132,Mirox Cyber Security & Technology Pvt Ltd,"4th Floor Nila Technopark Kariyavttom PO 695581 Trivandrum, Kerala",,,9995799499,Mr. Rajesh Babu,,Empanel_org(1).pdf
133,Marven Data Systems Private Limited,"201, Sai Vaishnavi Enclave, Puppalaguda, Manikonda, 500089, Telangana, India",,+91-8886533448,,Praveen Choudary Muppaneni,mpc[at]mdsinc.in/mpc.ingen1[at]gmail.com,Empanel_org(1).pdf
134,Macksofy Technologies Pvt Ltd,"Office no 308, 3rd floor, SRA Commercial Tower, Motilal Nehru Nagar, Bandra Kurla Complex, Bandra East, Mumbai: 400051",,+91 9930824239,,Dhwani Vakhariya,Dhwani[at]macksofy.com,Empanel_org(1).pdf
135,MITKAT ADVISORY SERVICES PRIVATE LIMITED,"511, ASCOT CENTRE, ADJACENT TO HILTON, NEAR INTERNATIONAL AIRPORT, OFF SAHAR ROAD, ANDHERI (EAST), MUMBAI",,01141236710,,PAWAN DESAI,pawan.desai[at]mitkatadvisory.com,Empanel_org(1).pdf
136,MapleCloud Technologies,"Office No-203 2nd Floor, Building No D-219, Sector-63, Noida, India",,+91-9739995151,,Yogendra Rajput,yogendra.rajput[at]maplecloudtechnologies.com,Empanel_org(1).pdf
137,Matrix3D Infocom Private Ltd,"156/C, Mittal Court. 224, Nariman Point, Mumbai 400021",,+91 9930472590,,Murtaza Motiwala,murtaza.motiwala[at]matrix3d.com,Empanel_org(1).pdf
138,Mindsprint Digital (India) Private Limited (Formerly known as Olam Information,"services Pvt ltd) International Tech Park,12th Floor, Zenith Building, Ascendas, Taramani Link Road, Taramani,Chennai, Tamil Nadu - 600113",,04442223700,,Mr. Venkat Krishnan,venkat.krishnan[at]mindsprint.com,Empanel_org(1).pdf
139,Net Square Solutions Private Limited,"1, SanjivBaug baug, Near Parimal Crossing, Paldi, Ahmedabad - 380007, Gujarat",,,+9i 9011813358,Ms. Aashi Chaturvedi,"aashi[at]net-square.com, bizdev[at]net-square.com",Empanel_org(1).pdf
140,Network Intelligence Pvt. Ltd.,"2nd Floor, 204, Ecospace IT Park, Off Old Nagardas Road, Andheri-E, Mumbai-400069.",,+919820049549,,Mr. Kanwal Kumar Mookhey,kkmookhey[at]niiconsulting.com,Empanel_org(1).pdf
141,Nangia & Co LLP,"A-109, Sector 136, Noida (Delhi-NCR) - 201304",,+91 98203 65305,,1. Mr. Pushpendra Bharambe (Executive Director),,Empanel_org(1).pdf
142,Netrika Consulting India Pvt. Ltd.,"Plot no.2, Industrial Estate, Udyog Vihar, Phase-IV, Gurugram, Haryana, India. PIN: 122015",,+91-124-4883000,,Sanjay Kaushik & Salil Kapoor,sanjay[at]netrika.com; Salil.kapoor[at]netrika.com,Empanel_org(1).pdf
143,Netsentries Infosec Solutions Private Limited,"No.5, 4th Floor, Wing II Jyothirmaya Building, Infopark SEZ Phase-II, Brahmapuram P.O. Cochin 682303",,+91 8884909578,,Sudheer Elayadath,Sudheer[at]netsentries.com,Empanel_org(1).pdf
144,NG TECHASSURANCE PRIVATE LIMITED,"Shop No. S-06 and S-07 (206 & 207), 2nd Floor, Atlanta Shopping Mall, Althan Bhimrad Road, Surat, Gujarat - 395017",,+91 99795-80410,,Mr. Niraj Goyal,admin[at]ngtech.co.in,Empanel_org(1).pdf
145,NET ACCESS INDIA LIMITED,"No.43, Moore Street, Parry House, 6th Floor, Chennai – 600 001",,+91 73583 00888 / +91 75500 75881,,Gunalan V,info[at]netaccess-india.com / gunalanV[at]netaccess-india.com,Empanel_org(1).pdf
146,NTT INDIA PRIVATE LIMITED,"Unit No. FOF-B-08-10 &10A, Fourth Floor, B Wing, Art Guild House, Phoenix Market City, LBS Marg, Kurla West, Mumbai 400070. India.",,9980166992,,Surendranath Wuntakal,surendranath.wuntaka[at]global.ntt,Empanel_org(1).pdf
147,OwnZap Infosec Pvt. Ltd.,"1st floor, 15, Savina Main Rd, above jodhpur sweets and bakery, New Colony, Savina, Udaipur, Gordhan Vilas Rural, Rajasthan 313002.",,+91 9875770345,,Puneet Matta,puneet@ownzapinfosec.co.in,Empanel_org(1).pdf
148,Panacea InfoSec Pvt. Ltd.,"226, Pocket A2, Sector 17, Dwarka, New Delhi - 110075",,+91 11 49403170,+91-9650028323/ +91 9205786094,"Apurva K Malviya, Global Business Head",apurva[at]panaceainfosec.com,Empanel_org(1).pdf
149,Peneto Labs Pvt Ltd,"Level 8 & 9, Olympia Teknos, No - 28, SIDCO Industrial Estate, Guindy, Chennai 600032",,+91 8861913615 / +91 44 4065 2770,,Parthiban J,Parthiban[at]penetolabs.com,Empanel_org(1).pdf
150,Paladion Networks Pvt. Ltd.,"Shilpa Vidya, 49 1st Main, 3rd Phase JP Nagar, Bangalore - 560078",,+91-80-42543444,,Mr. Balaji Venkatasubramanian,balaji.vs[at]eviden.com,Empanel_org(1).pdf
151,Payatu Security Consulting Private Limited,"Office No. 308, Lunkad Sky Vista, Near Dorabjee Mall, Viman Nagar, Pune, Maharashtra",,8264144797 / 020-47248026,,Mr. Mihir Doshi,security[at]payatu.io,Empanel_org(1).pdf
152,Price water house Coopers Pvt. Ltd.,"7th & 8th Floor, Tower B, Building 8, DLF Cyber City, Gurgaon, Haryana -122002",,[91] 9811299662,,Mr.Rahul Aggarwal,rahul2.aggarwal[at]pwc.com,Empanel_org(1).pdf
153,Protiviti India Member Private Limited,"GTB Nagar, Lalbaug, Everard Nagar, Sion, Mumbai, Maharashtra 400022",,022 6626 3333,,Mr. Sandeep Gupta (Managing Director),Sandeep.Gupta[at]protivitiglobal.in,Empanel_org(1).pdf
154,Phoenix TechnoCyber,"411, B Wing, Shivam-1, Amba Business Park, Adalaj, Ahmedabad. Gujarat 382421",,9898054244 / 9016076035,,Bhinang Tejani,bhinang[at]p-technocyber.com,Empanel_org(1).pdf
155,PKF Consulting Services LLP,"406, 4th Floor, Madhava Building, Bandra Kurla Complex, Bandra (East) Mumbai 400051, Maharashtra, India",,+91 22 49749812,,Venkatesh Krishnamoorthy,venkatesh.k[at]pkf.co.in,Empanel_org(1).pdf
156,ProTechmanize Solutions Pvt. Ltd.,"209, Srishti Square, LBS Marg, Bhandup West, Mumbai-400078 New Postal Address (From 1st May 2022): 110, 1st Floor, Plot A, 315, Rd Number 34, Wagle Estate, Jai Bhavani Nagar, MIDC Industrial Area, Thane West, Maharashtra 400604",,9769915281,,Hakimuddin Wadlawala,hakim[at]protechmanize.com,Empanel_org(1).pdf
157,PARALOK INFORMATION SECURITY PRIVATE LIMITED,"SY NO: 14, FLAT NO 330, BLOCK 1, MANSAROVAR HEIGHTS 3, HASMATHPET, SECUNDERABAD Andhra Pradesh, INDIA Pin code: 500015",,+91 7349676555/+91 6295690922,,Nisha Lisa G,nisha[at]paralok.com,Empanel_org(1).pdf
158,Primefort Private Limited,"Alpha Wing, Unit-812, Raheja Towers, NO.177, Annasalai, Chennai, Tamil Nadu, 600002",,+91 90471 40793,,Sriram (Director - Technical),sriram@primefort.net,Empanel_org(1).pdf
159,Pristine InfoSolutions Pvt. Ltd.,"305-B, Town Centre II, Marol, Andheri-Kurla Road, Andheri (east), Mumbai - 400 059, India.",,022-28501116 | +91-9029029632,,Kushal Hadkar,kushal[at]pristineinfo.com,Empanel_org(1).pdf
160,PSY9 Security Consulting Private Limited,"A block, 103(C), Ganesh Meridian, near, Sarkhej - Gandhinagar Hwy, opp. Kargil Petrol Pump, near Gujarat High Court, Vishwas City 1, Sola, Ahmedabad, Gujarat 380061",,+918160281166 and +919825826568,,Khush N. Bhatt,khush[at]psy9.in,Empanel_org(1).pdf
161,Pyramid Cyber Security & Forensic Private Limited,"FB-03, NSIC STP Extn., Okhla Industrial Estate, New Delhi - 110020",,"+91-11-41078091, +91-9811115849",,Pankaj Bhargava,"pankaj.bhargava[at]pyramidcyber.com, sales[at]pyramidcyber.com",Empanel_org(1).pdf
162,Qseap Infotech Pvt. Ltd.,"Unit No.105, Building No.03, Sector No.03, Millennium Business Park, Mahape (MIDC), Maharashtra- 400710, India",,9987655544,,Mr. Abhijit Doke,infosec[at]qseap.com,Empanel_org(1).pdf
163,QRC Assurance and Solutions Private Limited,"Office No 508, Plot No 8, Ellora Fiesta, Sector -11, Sanpada, Navi Mumbai, Maharashtra, India, 400705",,,,Dr. Deepti Somayajula,audit[at]qrcsolutionz[dot]com,Empanel_org(1).pdf
164,Qadit Systems and Solutions Pvt Ltd,"1st Floor, Reach Offices No. 1, Chamiers 4th Lane, Nandanam, Chennai 600035",,,,Mr. Mahesh Balan,mahesh[at]qadit.com,Empanel_org(1).pdf
165,QOS Technology Private Limited,"#48, 2nd Floor, R.V. Road, Basavanagudi, Bengaluru, Karnataka - 560004",,+91 9810091550; +91 80 41312419,,Ramandeep Singh Walia,ramandeep[at]qostechnology.in,Empanel_org(1).pdf
166,Risk Quotient Consultancy Private Limited,"6TH FLOOR, Building No./Flat No.: 601, KAMDHENU 23 WEST TTC INDUSTRIAL AREA MIDC Plot Number : A-10/2 and A-11, Nearby Landmark: NEXT TO WHITE HOUSE Kopar Khairane Navi Mumbai,Thane, Maharashtra: 400709",,+91 9619199375,,"Mr. Nilesh Patil, Chief Business Officer",nilesh.patil[at]rqsolutions.com,Empanel_org(1).pdf
167,RSM Astute Consulting Pvt. Ltd.,"301-307, A Wing, Technopolis Knowledge Park, Mahakali Caves Road, Andheri (East), Mumbai – 400093 Tel: 91-22- 6108 5555",,,,Mr. Anup Nair,anup.nair[at]rsmindia.in,Empanel_org(1).pdf
168,RNR Consulting Private Limited,"E-16/169, Sector-8, Rohini, Delhi 110085",,"+91 9999132873 , +91 9971214199",,"Nitish Goyal , Practice Head – Information and Cyber Security",nitish[at]consultrnr[dot]com,Empanel_org(1).pdf
169,RiskBerg Consulting Pvt Ltd,"423-424, 4th Floor, Tower – B3, Spaze I Tech Park, Sohna Road, Sector-49, Gurugram, Haryana-122018, India",,+91 124 4284087; +91 995 314 4939,,Rohit Agrawal,rohit.agrawal[at]riskberg.com,Empanel_org(1).pdf
170,Reserve Bank Information Technology Pvt Ltd. (ReBIT).,"502, Building No 1, Mindspace Juinagar, Nerul, Navi Mumbai – 400706",,+91-22-5023 3100,,Mahesh Gharat,Empanelled.Team[at]rebit.org.in,Empanel_org(1).pdf
171,REVERSE ENGINEERING INFOSEC PRIVATE LIMITED,"DOOR NO 808, 1ST FLOOR, A BLOCK, SAHAKARNAGAR, BENGALURU - 560092",,9740028096,,SAMARTH BHASKAR BHAT,samarth[at]reinfosec.com,Empanel_org(1).pdf
172,RAH Infotech Private Limited,"F-8 Okhla Phase 1, New Delhi - 110020",,"+91 9311562664, 8900000043",,Itasha Anand & Khushboo Lama,infosec[at]rahinfotech.com,Empanel_org(1).pdf
173,RedHunt Labs India Private Limited,"127, Prakash Vihar, Ajabpur Kalan, Dehradun, Uttarakhand, India - 248001",,+91-9971658929,,Sudhanshu Chauhan,sudhanshu[at]redhuntlabs.com,Empanel_org(1).pdf
174,ROOTNIK Labs Cybersecurity Private Limited,"BL-257, Sector-II, Salt Lake City, Kolkata- 700 091, West Bengal, India",,9735 717 763,,Arindam Halder,"arindam.halder[at]rootniklabs.com, info[at]rootniklabs.com",Empanel_org(1).pdf
175,Renault Nissan Technology & Business Centre India (RNTBCI),"Ascendas Mahindra IT Park, Mahindra World City SEZ, Plot No TP2/1 Natham Sub-post Office Ground Floor, Chengalpattu, Chennai - 603004. Tamilnadu",,"+91 89398 75175 ; 044 6748 1008,",99622 01737,,karthekeyan.thangavel[at]rntbci.com,Empanel_org(1).pdf
176,SecurEyes Techno Services Pvt. Ltd.,"4th Floor, Delta Block, Sigma Soft Tech Park, Whitefield Main Road, Varathur, Bangalore - 560066",,+91 9449035102/ 080-41264078,,Ms. Uma Pendyala,umap[at]secureyes.net,Empanel_org(1).pdf
177,Security Brigade InfoSec Pvt. Ltd.,"3rd Floor, Kohinoor Estate, Lower Parel, Mumbai - 400013",,+919004041456,,Ms. Jamila Pittalwala,sales[at]securitybrigade.com,Empanel_org(1).pdf
178,Suma Soft Private Limited,"Suma Center, 2nd Floor, Opp. Himali Society, Erandawane, Pune, Maharashtra – 411 004. Tel: +91.20.4013 0700, +91.20.4013 0400",,,,"Mr. Milind Dharmadhikari,",milind.dharmadhikari[at]sumasoft.net / infosec[at]sumasoft.net,Empanel_org(1).pdf
179,SISA Information Security Private Limited,"No. 79, Road Number 9, KIADB IT PARK, Arebinnamangala Village, Jala Hobli Bengaluru, Karnataka, India - 562149",,+91-7042027487,,Mr. Bharat Malik,warlabs[at]sisainfosec.com,Empanel_org(1).pdf
180,Sequretek IT Solutions Pvt. Ltd.,"304, Satellite Silver, Andheri Kurla Road, Marol, Andheri East, Mumbai, INDIA - 400 097",,022-40227034,9920895758,"Mr. Pritish Bharambe, Director - Service Assurance",pritish.bharambe[at]sequretek.com,Empanel_org(1).pdf
181,Siemens Limited,"Birla Aurora Towers, Level 21, Plot 1080, Dr. Annie Basant Road, Worli, Mumbai - 400030",,+91 22 39677640,,Mr. Amitava Mukherjee,Amitava.Mukherjee[at]siemens.com,Empanel_org(1).pdf
182,Software Technology Parks Of India,"1st Floor, Plate B, Office Block-1, East Kidwai Nagar, New Delhi-110023",http://www.stpi.in,"+91-11-24628081 , 20815076",,"Shri Pavitra Aggarwal, Director & CISO",pavitra[at]stpi[dot]in,Empanel_org(1).pdf
183,SUMERU TECHNOLOGY SOLUTIONS PVT LTD,"“SAMVIT”, 1st Floor, Near Art of Living Ashram, Udayapura, 21KM Kanakapura Main Road, Bangalore,560082 Karnataka India",,+91 6364357139,,Asish Kumar Behera,secure[at]sumerusolutions.com,Empanel_org(1).pdf
184,SWADESH SYSTEM PVT.LTD.,"504,5th Floor, 58, Sahyog Building, Nehru Place, New Delhi-110019",,011-45621761,,Mr. Rohit Jain,rohit[at]swadeshsystem.in,Empanel_org(1).pdf
185,SecureInteli Technologies Private Limited,"3rd Floor, Nandi Infotech | Plot No 8, 1st Cross, KIADB, Sadaramangala Industrial Area Mahadevpura, Bangalore 560 048, INDIA",,+91 90358 33818,,Pradeep Kumar,contactus[at]secureinteli.com,Empanel_org(1).pdf
186,SECURIUM SOLUTIONS PRIVATE LIMITED,"B28, FIRST FLOOR, SECTOR 1, NOIDA - 201301.",,+91 99906 02449,,NEHA SINGH,neha.singh[at]securiumsolutions.com,Empanel_org(1).pdf
187,SOC ANALYST PRIVATE LIMITED,"10-11, Central Cahambers, 1017, Tilak Road, Swargate Corer, Pune- 411002",,020-24444090,,i) RAJENDRA PONKSHE,,Empanel_org(1).pdf
188,Shieldbyte Infosec Private Limited,"1301/1302, 13th Floor, H Wing, Aaradhya Four Point by MICL, Naidu Colony, Pant Nagar, Ghatkopar East, Mumbai - 400075 Maharashtra",,+91-8779784050,,Vaishali Mutalik,vaishali[at]shieldbyteinfosec.com,Empanel_org(1).pdf
189,SYNOPSYS SOFTWARE INTERGRITY SOLUTIONS (INDIA) PVT LTD.,"Prestige Blue Chip Tech Park, No. 9, Hosur Main Road, 3rd Block, 4th Floor, Bangalore, Karnataka – 560029.",,+91.80.6742.6946; +91.80.6772.0200,,"Amarnadh Kolli, Director – Operations",akolli[at]synopsys.com,Empanel_org(1).pdf
190,SCHNEIDER ELECTRIC SYSTEMS INDIA PRIVATE LIMITED,"Tamarai Tech Park, SP Plot 16-19 , 20A, Thiru Vi Ka Industrial Estate Inner Ring Road, Guindy, Chennai Tamilnadu India- PIN 600032. Contact: Mr. Abhay Thodge (General Manager- Engineering)",,,+91- 9324447895,,abhay.thodge[at]se.com,Empanel_org(1).pdf
191,Staqo World Private Ltd,"Sleepwell Tower #14, Sector 135, Noida, Uttar Pradesh 201301",,0120 468 6440,,Neelesh Gaur,neelesh.gaur[at]staqo.com,Empanel_org(1).pdf
192,Secnic Consultancy Services Pvt. Ltd.,"Corporate Office: First Floor, F-342, Kamla Nagar, Agra – 282004",,"+919811779128, +91-7906588456",,Sandhya Sharma,"info[at]secnic.in, sandhya.s[at]secnic.in",Empanel_org(1).pdf
193,Secnuo Consulting (OPC) Private Limited,"Office No. 202, Leela Grandeur, Solapur-Pune Highway, Pune, Maharashtra, India, 412307",https://www.secnuo.com,(+91) 832-931-1869,(+91) 721-967-7576,"1. Ms. Anupama Srivastava, Director",anupama.srivastava[at]secnuo.com,Empanel_org(1).pdf
194,SecurityBoat Cybersecurity Solutions Private Limited,"4th Floor M- Arch Center, Pashan-Sus Road, Baner, Pune 411021",,,,Ninad Mathpati,,Empanel_org(1).pdf
195,Softcell Technologies Global Private Limited,"303 B-Wing, Commercial-1, Kirol Road, Kohinoor City Phase 1 Rd, Kurla, Mumbai, Maharashtra 400070",,+91 92235 86746,,- 1. Name - Deepak Fernandes,deepak[at]softcell.com,Empanel_org(1).pdf
196,Synclature Consultancy Private Limited,"1306, Hubtown Solaris, Professor N. S. Phadke Road, Andheri East, Mumbai, Maharashtra 400069.",,+919011054960,,Nitish Sabnis,consultancy[at]synclature.com,Empanel_org(1).pdf
197,Security Innovation India,"516 WORLD TRADE CENTER - TOWER 2 PUNE, MAHARASHTRA - 411014",,9049484027,,Satish Surapuraju,satishs[at]securityinnovation.com,Empanel_org(1).pdf
198,Securityium (OPC) Pvt. Ltd.,"C/285, 1st Floor, Dreams The Mall, LBS Marg, Bhandup West Mumbai City MH 400078 IN",,+91 7506439669,,Mayank Sahu,bd[at]securityium.com,Empanel_org(1).pdf
199,Sify Digital Services Ltd,"Regd Office – 2nd Floor, Tidel Park, No 4, Rajiv Gandhi Salai, Taramani, Chennai – 600 113.",,044 - 22540770,90032 77877,"S Shankara Narayanan, Head, Sify Security Delivery Practice",mss.fortknox[at]sifycorp.com (Sify GRC – Mailbox),Empanel_org(1).pdf
200,Saptang Labs Private Limited,"9th Floor, TVH Belicia Towers, MRC Nagar,1st Lane, Raja Annamalai Puram, Chennai, Tamil Nadu 600028",,729193837,,Budamgunta Venkata Sathya Saikrishna (CEO & Director),saikrishnabvs[at]saptanglabs.com,Empanel_org(1).pdf
201,SecLance Private Limited,"2575/1, First Floor, 17th Main, 2nd Cross, HAL 2nd Stage, Bangalore - 560008",,"+919363082920, +918884229919",,Saurabh Kumar and Paritosh Kumar Tripathi,Kumar[at]seclance.com and Paritosh.k.tripathi[at]seclance.com,Empanel_org(1).pdf
202,Sicherten Info Consulting Private Limited,"TSS Towers, Kavuri Hills Phase 2 Road, Doctor's Colony, Madhapur, Hyderabad, Telangana, India",,9246553451,,Kesava Rao Somayajula,kesava.somayajula[at]sicherten.com,Empanel_org(1).pdf
203,SQ1 Security Technology Private Limited,"Futura Tech Park, 2nd Floor, Block B, 334 Rajiv Gandhi Salai, Sholinganallur, OMR, Chennai 600119",,044 69205600,,Prabhu Venkatesa Kumar,prabhu[at]sq1.security,Empanel_org(1).pdf
204,Saint Fox Consultancy Private Limited,"2nd Floor, Building 491, 17th Cross Road, 27th Main Rd, Sector 2, HSR Layout, Bengaluru, Karnataka 560102.",,+91 9739935038,,Rajeshwar Rao Thatiparthy,rajeshwar[at]stfox.com,Empanel_org(1).pdf
205,Secunatix Consultants Private Limited,"Registered Address: C-31, Rashtra Sarathi C.H.S, Deendayal Nagar, Navghar Road, Mulund East, Mumbai, Maharashtra - 400081. Corporate Address: Office No 21, 4th Floor, Bellezza, Shanti Sadan CHS, 90ft Road, Mulund East, Mumbai, Maharashtra - 400081.",,+91 9930966766 / +91 7738555366,,Mr. Vijay Sawant,info[at]secunatix.com,Empanel_org(1).pdf
206,Sysman Computers,"312, Sundram, Rani Laxmi Chowk, Sion Circle, Mumbai 400022",,99672-48000 / 99672-47000,,Dr. Rakesh Mohan Goyal,rakesh[at]sysman.in; sysman[at]sysman.in,Empanel_org(1).pdf
207,SECURENEXGEN LLP,"8, Opp GE Medicals, Dinnur Main Road, Kadugodi Colony, Bengaluru, 560067",,+91 998-601-8143 | +91 976-990-0101,,JAYAPRAKASH GOPAL REDDY,JAYAPRAKASH.REDDY[at]SECURENEXGEN.COM,Empanel_org(1).pdf
208,Sveltetech Technologies Private Limited,"8th Floor, Tower-B, Picasso Centre, Sector 61, Gurugram, Haryana 122102",,8147050614,,Sahil Bagati,sahil[at]sveltetech.com,Empanel_org(1).pdf
209,TAC InfoSec Limited,"C203, 4th Floor, World Tech Tower Phase-8B, Mohali-160055",,"9876200821, 9988850821",,"Mr. Trishneet Arora, Founder and CEO",india[at]tacsecurity.com,Empanel_org(1).pdf
210,Tata Communications Ltd,"5th Next Gen Tower New IDC Building, Ho Chi Minh Marg, opp. Savitri Cinema, Greater Kailash, New Delhi -110048",,+91 11 66512760,9594950749,Mr. Amit Rathi - Product Manager GRC Product/Services,Amit.Rathi [at]tatacommunications.com,Empanel_org(1).pdf
211,Talakunchi Networks Pvt Ltd,"Postal address: 505, Topiwala Centre, Off S.V. Road, Goregaon West, Mumbai 400104",,,,Vishal Shah,infosec[at]talakunchi.com,Empanel_org(1).pdf
212,Tata Advanced Systems Ltd.,"Cyber & Physical Security Division Postal address: C-27, Sector 58, Noida 201309, Uttar Pradesh, India",,0120-4015500,,Mr. Rajiv Khandelwal,cybersec[at]tataadvancedsystems[dot]com,Empanel_org(1).pdf
213,TUV-SUD south Asia Pvt. ltd,"Solitaire, 4th Floor, ITI Road, Aundh, Pune – 411007 Maharashtra",,+91 20 6684 1212,,Atul Srivastava,atul.srivastava[at]tuvsud.com Phone:+91 9819955909,Empanel_org(1).pdf
214,Tata Power Delhi Distribution Ltd,"Tata Power Delhi Distribution Ltd, NDPL House, Hudson Lane, New Delhi - 110009",,01166112222,,Aamir Hussain Khan,aamir.hussain[at]tatapower-ddl.com,Empanel_org(1).pdf
215,TechD Cyber Security Limited       (Formerly Techdefence Labs Solutions Private Limited),"215. M/s TechD Cyber Security Limited (Formerly Techdefence Labs Solutions Private Limited) 901-904 & 908, 9th Floor Abhishree Adroit, Near Mansi Circle, Judges Bungalow Road, Vastrapur, Ahmedabad - 380015",,9924822224/ 7567867776,,Sunny Vaghela,sunny[at]techdefencelabs.com,Empanel_org(1).pdf
216,Tek Cube Pvt. Ltd. (WeSecureApp),"6th Floor, 91 Springboard, LVS Arcade, Madhapur, 71, Jubilee Enclave, HITECH City, Hyderabad, Telangana- 500081",,+91- 7842283183,,Anurag Giri,anurag[at]wesecureapp.com,Empanel_org(1).pdf
217,Trinay Cyber Technologies Pvt Ltd,"5-9, Near Bank Bazar / Opp Union Bank, Tsundur, Guntur, Andhra Pradesh - 522318",,+91 89196 74695,,Lavanya Bhavanam,lavanya[at]trinaytechnologies.com,Empanel_org(1).pdf
218,Tuxcentrix Consultancy Pvt. Ltd,"TuxZone Near AIR , Mythripuram Road, Thrikkakara Cochin Kerala 682021 India",,7356335511,,Sobin Joseph,sobin[at]tuxcentrix.in,Empanel_org(1).pdf
219,TCG Digital Solutions Pvt. Ltd.,"BIPPL, Building- Omega, 16th Floor, Block EP & GP, Sector- V, Salt Lake Electronics Complex, Kolkata- 700091, WB",,91 33 4051 7300 / +91 33 4051 7000,"+91 9434243285, +91 9874285577",Abir Ranjan Atarthy,abir.atarthy[at]tcgdigital.com,Empanel_org(1).pdf
220,TATA CONSULTANCY SERVICES LIMITED,"TCS HOUSE, RAVELINE STREET, 21, D.S. Marg, Fort, Mumbai- 400001, INDIA",,022 67789595,,Lalatendu Pattnaik,pattnaik.lalatendu[at]tcs.com,Empanel_org(1).pdf
221,The Intect (M/s Hion Security Private Limited),"Ground Floor, FIEE Complex, A-19, Block A, Okhla Phase II, Okhla Industrial Estate, New Delhi, Delhi 110020",,+91-8800299792,,Sahil Pahwa,sahil[at]theintect.com,Empanel_org(1).pdf
222,Terasoft Technologies Pvt. Ltd.,"Shivanand, Vedantnagar, Savedi Road, Ahmednagar, Maharashtra 414003",,"0241-2431115, +91 7709991117",,Rashmi Rajendra Jalindre,rashmi[at]terasoft.in,Empanel_org(1).pdf
223,Techensglobal Private Limited,"JJS Building, Vettichira, Malappuram District, Valanchery, Punnathala Kerala, 676552",,+919539144322,,Shijas Mohidheen,Shijas[at]Techensglobal.com,Empanel_org(1).pdf
224,Tribastion Technologies Private Limited,"4th Floor, Commercial Tower- I, INSPIRE Business Park, Adani Shantigram Township, Vaishnodevi Circle, S.G. Highway, Ahmedabad - 382421, Gujarat, India",,9979854022,,"1. Ishika Jain, E-mail : ishika.jain[at]tribastion.com",ishika.jain[at]tribastion.com,Empanel_org(1).pdf
225,Techumen Infosec Private Limited,"E-103, Happy Residency, Vesu, Surat -395007 Corporate Office: Shop no. 113, Exceluss Business Space, Bhimrad Althan Road, Bhimrad, Surat-395007",,+91 98989 51269,,Gaurav Goyal,connect[at]techumeninfosec.com,Empanel_org(1).pdf
226,Tsaaro Solutions Private Limited,"3rd Floor, ATS, Tower C, ATS BOUQUET, Block B, Sector 132, Noida, Uttar Pradesh 201304",,9818087122,,Shilpi Singh,shilpi[at]tsaaro.com,Empanel_org(1).pdf
227,Utthunga Technologies Private Limited,"Indiqube, South Summit, S End Rd, Vijayarangam Layout, Jayanagar, Bengaluru, Karnataka 560004.",,080 68151900,,Mr Pavithran A,pavithran.a[at]utthunga.com,Empanel_org(1).pdf
228,VISTA InfoSec,"001, Neoshine House, New Link Road, Andheri West, Mumbai - 400053",,+91-9029236292,,Supriya Deshpande,Sales[at]vistainfosec.com,Empanel_org(1).pdf
229,Vault Infosec,"No. 47, Vaidhyanathan Street, Shenoy Nagar, Aminijkarai, Chennai - 600030",,+91 89398 91041,,Sudhakar Kathirvel,sudhakar[at]vaultinfosec.com,Empanel_org(1).pdf
230,Virtual Caim Private Limited,"604, 3rd EYE THREE, BEHIND GIRISH COLD DRINK, C. G. ROAD, AHMEDABAD. 380006.",,NA,+91-8320295470 / +91-8485918837,Vatsal Raichura,vatsal[at]virtualcaim.com,Empanel_org(1).pdf
231,WEST BENGAL ELECTRONICS INDUSTRY DEVELOPMENT CORPORATION LIMITED,"[WEBEL] WEBEL BHAVAN, BLOCK EP & GP SECTOR-V, SALT LAKE CITY, KOLKATA-700091, WEST BENGAL",,033-2239-2387,- +91 98319 61152,Kausik Halder,halder.kausik[at]webel-india.com,Empanel_org(1).pdf
232,Wings2i IT Solutions Private Limited,"No. 18, 3RD E Cross, 18th Main, BTM 2nd Stage, Bengaluru, Karnataka, INDIA - 560076",,+918050271700,9341223631 / 9740030215,Reena Ramachandran,"infosec[at]Wings2i.com, reenar[at]wings2i.com",Empanel_org(1).pdf
233,WST Technologies Private Limited,"5th Floor, Smartworks Victoria Park, Block GN, Plot no 37/2, Sector V, Salt Lake, Kolkata, West Bengal, India, Pin Code-700091",,"+91 6289231229, 8420703492",,Rajdeep Mukherjee,rajdeep.m[at]wstth.com,Empanel_org(1).pdf
234,Xiarch Solutions Private Limited,"352, 2nd Floor, Tarun Enclave, Pitampura, New Delhi-110034, India",,011-45510033,,"Mr. Utsav Mittal, Principal Consultant","utsav[at]xiarch.com, info[at]xiarch.com",Empanel_org(1).pdf
235,x-Biz Techventures Private Limited,"118-120, IJMIMA Complex, Near Goregaon Sports Complex, Off Link Road, Malad - West, Mumbai - 400064",,+91 9892108663 / 1800-266-8575,,Sunil Yadav,sunil.yadav[at]xbizventures.com,Empanel_org(1).pdf
236,Yoganandh & Ram LLP,"G-1, Shree Vishnu Apartments, 12, Twelfth Cross Street, Dhandeeswaram Nagar, Velachery, Chennai - 600042",,044-22432030,9940156515 / 98415 82933,Mr. Manoj Kumar Jain,manoj[at]yandr.in / isaudit[at]yandr.in,Empanel_org(1).pdf
"""

async def run_import():
    import io
    
    reader = csv.DictReader(io.StringIO(csv_data))
    
    async with AsyncSessionLocal() as session:
        for row in reader:
            list_no = row['certin_list_no'].strip()
            agency_code = f"CERTIN_{list_no.zfill(3)}"
            agency_name = row['agency_name'].strip()
            
            # Check if exists
            result = await session.execute(select(Agency).where(Agency.agency_code == agency_code))
            existing = result.scalar_one_or_none()
            if existing:
                continue
                
            contact_person = row['contact_person'].strip()
            if not contact_person:
                contact_person = "Unknown"
                
            raw_email = row['email'].strip()
            email = raw_email.replace("[at]", "@").replace("[dot]", ".").replace(" ", "")
            # take first email if multiple exist separated by / or ,
            if '/' in email:
                email = email.split('/')[0].strip()
            if ',' in email:
                email = email.split(',')[0].strip()
                
            # validation
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
                email = f"contact_{list_no}@example.com"
                
            phone = row['phone'].strip()
            mobile = row['mobile'].strip()
            contact_phone = phone
            if mobile:
                contact_phone = f"{phone} / {mobile}" if phone else mobile
                
            website = row['website'].strip()
            address = row['address'].strip()
            
            agency = Agency(
                agency_id=uuid.uuid4(),
                agency_code=agency_code,
                agency_name=agency_name,
                agency_type="CERT_IN_EMPANELLED",
                cert_in_empanelled=True,
                empanelment_number=list_no,
                contact_person=contact_person[:255],
                contact_email=email[:255],
                contact_phone=contact_phone[:50],
                website=website[:255],
                address=address,
                country="India",
                status="ACTIVE",
                onboarding_date=date.today()
            )
            session.add(agency)
            
        await session.commit()
        print("Import completed!")

if __name__ == "__main__":
    asyncio.run(run_import())
