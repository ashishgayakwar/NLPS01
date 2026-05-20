# Body-System Disambiguation Plan

This is a design proposal only. It does not change application behavior.

The goal is to add a general body-system disambiguation layer for patient search queries where generic symptoms such as bleeding, pain, swelling, discharge, burning, itching, lump, weakness, or blockage can route to the wrong specialty because retrieval matches the symptom word but misses body-system context.

## 1. Current Catalog-Derived Specialty Map

Observed catalog structure:

- `catalog.py` contains 363 treatment entries.
- The `category` field is blank for all current entries.
- Specialty areas must therefore be inferred from `slug`, `name`, `description`, `hindi_description`, and `hinglish_terms`.
- `get_searchable_text()` currently indexes name, Hindi name, slug, Hinglish terms, descriptions, and category for both semantic search and BM25.
- `pristyn_treatments_raw.json` sometimes has useful `meta_keywords`, especially Hindi SEO terms, but the current catalog conversion path does not carry `meta_keywords` into `catalog.py`.

Catalog-derived specialty map:

| Specialty / body system | Representative slugs / pages | Typical page signals |
|---|---|---|
| Proctology / anorectal / colorectal | `piles`, `fissure`, `fistula`, `anal-abscess`, `anal-ulcers`, `colorectal`, `rectal-prolapse`, `pilonidal-sinus`, `sphincterotomy`, `fistulotomy`, `vaaft`, `ligation-of-the-intersphincteric-fistula-tract` | anal, anus, rectal, colorectal, piles, fissure, fistula, hemorrhoid, gudha, gudhe, pichwade, motion |
| Urology / kidney / male genital | `kidney-stones`, `urinary-tract-stone`, `prostate-enlargement`, `prostatitis`, `prostatectomy`, `cystoscopy`, `bladder-neck-incision`, `cystolithotomy`, `cystolithotripsy`, `urethral-stricture`, `urethral-dilatation`, `phimosis`, `paraphimosis`, `circumcision`, `zsr-circumcision`, `balanitis`, `hydrocelectomy`, `varicocele`, `testicular-torsion`, `vasectomy`, `nephrectomy`, `rirs`, `ursl`, `pcnl`, `eswl` | urine, urinary, kidney, bladder, urethra, prostate, peshab, ling, foreskin, penis, andkosh, pathri |
| Gynecology / pregnancy / menstrual | `vaginal-bleeding`, `vaginal-infection`, `vaginal-itching`, `vaginal-swelling`, `vaginal-cyst`, `vaginal-wart`, `adenomyosis`, `endometriosis`, `endometrioma`, `uterine-fibroid`, `myomectomy`, `hysterectomy`, `hysteroscopy`, `irregular-periods`, `pcos-pcod`, `pregnancy-care`, `antenatal-care`, `ectopic-pregnancy`, `miscarriage`, `silent-miscarriage`, `incomplete-abortion`, `abortion`, `mtp`, `mtp-kit`, `tubectomy`, `prolapsed-uterus`, `polypectomy`, `uterus-polyp-removal` | vaginal, yoni, uterus, bachhedani, period, maasik, mahavari, pregnancy, garbh, garbhpat, fibroid, ovarian, cyst, gynaecologist |
| Fertility / IVF / reproductive | `ivf`, `iui`, `icsi`, `female-infertility`, `male-infertility`, `blocked-fallopian-tubes`, `anti-mullerian-hormone`, `egg-freezing`, `embryo-transfer`, `embryo-freezing`, `embryo-donation`, `blastocyst-culture`, `pgta-testing`, `poor-ovarian-response`, `premature-ovarian-failure`, `repeated-implantation-failure`, `surrogacy`, `tubal-ligation-reversal` | infertility, fertility, IVF, IUI, ICSI, bacha nahi, bachcha nahi, conceive, fallopian, egg, sperm, embryo |
| ENT - ear | `ear-infection`, `laser-ear-surgery`, `micro-ear-surgery`, `myringoplasty`, `myringotomy`, `perforated-eardrum`, `cochlear-implant`, `otosclerosis`, `otitis-media`, `otitis-interna`, `tinnitus`, `mastoidectomy`, `cholesteatoma-pearl`, `earlobe-repair` | ear, kaan, hearing, sunai, eardrum, parda, tinnitus, awaaz, ear discharge |
| ENT - nose / sinus | `septoplasty`, `deviated-nasal-septum`, `nasal-polyps`, `nasal-endoscopy`, `nasal-valve-collapse`, `balloon-sinuplasty`, `sinusitis`, `chronic-sinusitis`, `acute-rhinosinusitis`, `sphenoid-sinusitis`, `turbinate-reduction`, `turbinoplasty`, `rhinoplasty`, `nose-reshaping` | nose, nasal, naak, sinus, septum, nathuna, band, saans |
| ENT - throat / sleep / voice | `tonsillitis`, `acute-tonsillitis-surgery`, `coblation-tonsillectomy`, `laser-tonsillectomy`, `throat-infection`, `microlaryngeal`, `vocal-cord-polyps`, `parotidectomy` | throat, gala, tonsil, kharrate, snoring, awaaz, voice, vocal cord |
| Ophthalmology / eye / vision | `cataract`, `best-cataract-lens`, `snowflake-cataract`, `phaco-surgery`, `lasik-eye-surgery`, `contoura-vision`, `smile-lasik-surgery`, `silk-eye-surgery`, `vision-correction`, `astigmatism`, `glaucoma`, `retinal-detachment`, `diabetic-retinopathy`, `vitrectomy`, `vitreo-retinal`, `corneal-transplant`, `cornea-blindness`, `keratoconus`, `pterygium`, `ptosis`, `squint`, `icl-surgery`, `trifocal-lens`, `vivity-lens`, `edof-lens` | eye, aankh, aankhon, vision, roshni, chashma, cataract, motiyabind, lens, retina |
| Orthopedics / spine / joints | `acl-reconstruction`, `acl-tear`, `knee-replacement`, `knee-surgery`, `knee-cartilage-repair`, `knee-ligament-injury`, `meniscus-tear`, `hip-replacement`, `shoulder-replacement`, `shoulder-dislocation`, `rotator-cuff-repair`, `arthroscopy`, `ankle-sprain`, `foot-and-ankle`, `hand-and-wrist`, `carpal-tunnel-syndrome`, `spine-surgery`, `slip-disc`, `lumbar-disc`, `spinal-fusion`, `discectomy`, `rheumatoid-arthritis`, `osteoarthritis`, `sports-injury`, `fracture-like implant/removal pages` | knee, ghutna, ghutne, joint, haddi, ligament, tendon, ankle, foot, hip, shoulder, spine, kamar, back, arthritis |
| General surgery / gastro / abdomen | `hernia`, `inguinal-hernia`, `umbilical-hernia`, `femoral-hernia`, `incisional-hernia`, `hiatal-hernia`, `appendicitis`, `gallstone`, `ercp`, `mrcp`, `endoscopy`, `percutaneous-drainage`, `adhesiolysis` | hernia, appendix, gallstone, gall bladder, pet, abdomen, stomach, liver/bile duct, drainage |
| Vascular / veins / blood vessels | `varicose-veins`, `endovenous-laser-varicose-vein`, `sclerotherapy`, `spider-veins`, `deep-vein-thrombosis`, `thrombectomy`, `peripheral-artery-disease`, `angioplasty`, `edema`, `diabetic-foot-ulcers`, `diabetic-foot-cellulitis` | vein, nas, nasen, vascular, artery, DVT, thrombosis, clot, pair me sujan, blood flow |
| Dermatology / skin / cysts / wounds | `urticaria`, `vitiligo`, `skin-pigmentation`, `pigmentation`, `skin-booster`, `skin-graft`, `scar-removal`, `sebaceous-cyst`, `infected-sebaceous-cyst`, `cyst-removal`, `facial-cyst-removal`, `lipoma`, `corn-removal`, `toenail-removal`, `large-cystic-lesion` | skin, twacha, daag, rash, allergy, hives, cyst, ganth, lipoma, corn, toenail |
| Aesthetics / plastic surgery / hair | `hair-transplant`, `women-hair-transplant`, `beard-transplant`, `mustache-transplant`, `eyebrow-transplant`, `hair-fall-prp`, `gfc-hair-transplant`, `hair-reduction`, `lhr-face`, `anti-aging`, `botox`, `botox-injection`, `dermal-fillers`, `face-prp`, `face-threadlift`, `vampire-facial`, `hydra-facial`, `blepharoplasty`, `gynecomastia`, `breast-lift`, `breast-reduction`, `breast-augmentation`, `breast-reconstruction`, `breast-lump`, `axillary-lump`, `liposuction`, `liposculpture`, `body-contouring`, `tummy-tuck`, `thigh-liposuction`, `double-chin`, `buccal-fat`, `cleft-lip` | hair, baal, ganjapan, beard, mustache, face, chehra, skin, breast, charbi, fat, contouring, cosmetic |
| Bariatrics / weight loss | `bariatric-surgery`, `weightloss-surgery`, `obesity`, `weight-loss-injections`, `weight-loss-pills`, `ozempic-injection`, `intragastric-balloon`, `swallowable-gastric-balloon`, `endoscopic-sleeve-gastroplasty`, `balloon-therapy`, `fat-loss` | weight, obesity, motaapa, vajan, charbi, gastric balloon |
| Dental / orthodontics | `teeth-straightening`, `teeth-clips`, `teeth-gaps`, `crossbite-teeth`, `openbite-teeth`, `overbite-teeth`, `bone-grafting` | teeth, tooth, dant, daant, dental, braces, clips, bite, gaps |
| Breast / endocrine / miscellaneous surgery | `breast-lump`, `fibroadenoma`, `painful-lump-in-breast-male`, `left-nipple-pain`, `axillary-breast`, `nipple-reconstruction`, `subtotal-thyroidectomy` | breast, stan, nipple, axilla, thyroid |

Design implication: the system needs an explicit specialty map because the catalog has no usable category labels today.

## 2. Generic Symptom Groups

These groups are generic signals that should not decide specialty on their own. They need body-system context, safety precedence, or clarification.

| Generic symptom group | Common English / Hindi / Hinglish terms |
|---|---|
| Blood / bleeding | blood, bleeding, bleed, bloody, khoon, khun, lahu, rakt, rakht, blood aana, khoon aana, bleeding hona, bleeding rukna nahi, spotting, clots, clot, thakka, blood clot |
| Pain | pain, ache, painful, dard, darad, dukhta, dukhti, dukh raha, takleef, discomfort, cramps, cramp, kasak, jalan dard, sharp pain |
| Swelling | swelling, swollen, sujan, soojan, phoolna, phoola, fula hua, inflammation, edema, gath with swelling, lump swelling |
| Discharge / fluid / pus | discharge, fluid, pus, paani, pani, peep, peep aana, mavad, liquid, watery discharge, white discharge, ear discharge, nasal discharge, vaginal discharge |
| Burning | burning, jalan, jalna, burn, irritation, burning sensation, peshab me jalan, pet me jalan, aankh me jalan, yoni me jalan, gudha me jalan |
| Blockage / obstruction | blockage, blocked, band, bandh, rukna, rukawat, obstruction, jam, flow kam, urine rukna, naak band, tube blocked, fallopian blocked, artery blocked |
| Leakage / incontinence | leakage, leak, leaking, urine leak, urine leakage, peshab nikalna, peshab leak, stool leak, gas leak, control nahi, incontinence |
| Itching | itching, itch, khujli, kharish, jalan khujli, yoni me khujli, skin itching, fungal itching, anal itching |
| Lump / mass / cyst | lump, mass, cyst, ganth, gath, gaanth, gilty, rasoli, fibroid, polyp, wart, massa, masse, swelling lump, breast lump |
| Infection | infection, sankraman, septic, pus, fever with swelling, bad smell, gandh, foul smell, redness, infected, sujan infection |
| Fever | fever, bukhar, high fever, temperature, chills, kapkapi, thand lagna, infection fever |
| Weakness / fatigue | weakness, kamzori, thakan, fatigue, tired, energy nahi, chakkar, dizziness, not feeling well, badan tootna |
| Breathing issue | breathing problem, breathing difficulty, saans phulna, saans nahi aa rahi, saans lene mein dikkat, breathless, shortness of breath, wheezing, choking |
| Fertility / conception issue | cannot conceive, infertility, fertility problem, bacha nahi ho raha, bachcha nahi ho raha, pregnancy nahi ho rahi, conceive nahi, garbh nahi thahar raha, sperm problem, egg problem |
| Vision issue | vision problem, blurry vision, roshni kam, aankh dhundla, chashma, cataract, motiyabind, eye pain, red eye, aankh lal, double vision |
| Hearing issue | hearing loss, sunai kam, sunai nahi dena, kaan band, kaan me awaaz, tinnitus, ringing, ear noise |
| Stone / pathri | stone, pathri, patthri, pattari, kidney stone, gallstone, bladder stone, urinary stone, pet ki pathri, peshab ki pathri |
| Rash / skin change | rash, allergy, daane, dane, hives, urticaria, daag, pigmentation, white patch, safed daag, vitiligo, redness |
| Hair loss | hair fall, hair loss, baal jhadna, baal girna, ganjapan, baal patle, hair thinning |
| Weight / fat | weight gain, weight loss, motaapa, motapa, vajan badhna, vajan kam, charbi, fat, obesity |
| Injury / trauma | injury, chot, tear, fracture, ligament tear, sprain, moch, dislocation, sports injury, accident |

## 3. Body-System Context Groups

Body context groups should be detected independently from generic symptom groups. A query may have multiple contexts, in which case the router should prefer safety, then high-specificity body contexts, then clarification.

| Body-system context | Common terms / variants | Likely specialty |
|---|---|---|
| Stool / rectal / anus / proctology | stool, motion, potty, tatti, latrine, mal, bowel, rectum, rectal, anus, anal, gudha, gudhe, pichwada, pichwade, bawasir, piles, fissure, fistula, bhagandar, hemorrhoid, massae | Proctology / anorectal |
| Urine / kidney / bladder / urology | urine, peshab, पेशाब transliteration variants, urinary, bladder, kidney, gurda, gurde, ureter, urethra, prostate, peshab rukna, peshab me jalan, pathri with urine/kidney | Urology |
| Male genital / scrotal / foreskin | penis, ling, foreskin, tight foreskin, khatna, circumcision, phimosis, paraphimosis, andkosh, testicle, testicular, scrotum, hydrocele, varicocele, balanitis | Urology / andrology |
| Vaginal / uterus / period / gynecology | vaginal, vagina, yoni, uterus, bachhedani, garbhashay, period, periods, maasik, mahavari, menstrual, bleeding between periods, white discharge, vaginal itching, vaginal swelling, fibroid, cyst | Gynecology |
| Pregnancy / miscarriage / abortion | pregnancy, pregnant, garbh, garbhwati, miscarriage, garbhpat, abortion, MTP, ectopic, antenatal, 7 week, trimester, pregnancy bleeding | Gynecology with safety caution |
| Fertility / reproductive | bacha nahi, bachcha nahi, infertility, fertility, conceive, pregnancy nahi, IVF, IUI, sperm, egg, embryo, fallopian tube, AMH, PCOS, PCOD | Fertility / IVF |
| Ear / hearing / ENT | ear, kaan, kaano, hearing, sunai, eardrum, parda, tinnitus, awaaz, kaan se paani, kaan dard, kaan band | ENT ear |
| Nose / sinus / ENT | nose, naak, nasal, sinus, septum, nathuna, naak band, naak se paani, smell, snoring if nasal/sleep context | ENT nose / sinus |
| Throat / tonsil / voice / ENT | throat, gala, gale, tonsil, tonsils, awaaz, voice, bolne me dikkat, vocal cord, kharrate, snoring, sleep apnea | ENT throat / sleep |
| Abdomen / stomach / general surgery / gastro | pet, stomach, abdomen, abdominal, liver, gall bladder, gallbladder, appendix, appendicitis, hernia, nabhi, groin, inguinal, acidity, endoscopy | General surgery / gastro, with clarification for broad pain |
| Knee / joint / bone / orthopedics | knee, ghutna, ghutne, joint, haddi, bone, ligament, tendon, ACL, meniscus, cartilage, hip, shoulder, elbow, ankle, foot, hand, wrist, spine, kamar, back, slip disc, fracture, chot | Orthopedics / spine |
| Chest / breathing / emergency | chest, seena, heart, breathing, saans, breathless, choking, severe chest pain, chest tightness | Doctor fallback / emergency |
| Eye / vision | eye, aankh, aankhon, vision, roshni, chashma, motiyabind, cataract, retina, lens, LASIK, glaucoma, red eye, eye pain | Ophthalmology |
| Skin / hair / aesthetics | skin, twacha, face, chehra, daag, pigmentation, rash, allergy, hives, vitiligo, cyst, lipoma, ganth on skin, baal, hair, beard, mustache, hair fall | Dermatology / aesthetics / hair |
| Dental / teeth | teeth, tooth, dant, daant, dental, braces, clips, bite, overbite, openbite, crossbite, gap | Dental / orthodontics |
| Vascular / veins / blood vessels | vein, veins, nas, nasen, artery, blood vessel, clot, DVT, thrombosis, varicose, spider vein, pair ki nasen, blood flow | Vascular |
| Weight / obesity / bariatric | weight, obesity, motapa, motaapa, vajan, charbi, fat loss, gastric balloon, bariatric, Ozempic | Bariatrics / weight loss |
| Breast / nipple / axilla | breast, stan, nipple, axilla, underarm lump, breast lump, gynecomastia, male breast | Breast surgery / plastics / gyne depending gender/context |
| Thyroid / neck endocrine | thyroid, gala me gland, neck swelling, goiter, subtotal thyroidectomy | General surgery / endocrine, with clinical fallback when vague |

## 4. Disambiguation Matrix

Recommended state definitions:

- `direct_match`: Use only when the query contains a specific named treatment or a body-system plus symptom that maps cleanly to a supported page and no safety trigger is present.
- `needs_confirmation`: Use when body-system and symptom point to one specialty, but the exact treatment remains uncertain.
- `needs_clarification`: Use when body-system is clear but multiple treatments in that specialty are plausible, or when symptom is generic and body context is weak.
- `doctor_fallback`: Use when safety triggers are present, when context is too clinically broad, or when routing to a specific treatment would be unsafe.

| Generic symptom + body context | Likely specialty | Recommended state | Suggested clarification / target |
|---|---|---|---|
| Stool/rectal/anus + blood/bleeding | Proctology | `needs_clarification` | Piles, fissure, fistula/abscess, rectal prolapse, talk to doctor |
| Stool/rectal/anus + pain | Proctology | `needs_clarification` | Piles, fissure, abscess, fistula, rectal prolapse |
| Stool/rectal/anus + pus/discharge/paani | Proctology | `needs_clarification` | Fistula, anal abscess, pilonidal sinus, doctor consult |
| Stool/rectal/anus + swelling/lump | Proctology | `needs_clarification` | Piles, abscess, rectal prolapse, pilonidal sinus |
| Stool/rectal/anus + itching/burning | Proctology | `needs_clarification` | Fissure, piles, anal infection/ulcer, doctor consult |
| Urine/kidney/bladder + blood | Urology | `needs_clarification` or `doctor_fallback` if severe | Blood in urine, kidney stone, bladder/prostate issue, doctor consult |
| Urine/kidney/bladder + burning | Urology | `needs_clarification` | UTI-like concern, stone, prostatitis, doctor consult |
| Urine/kidney/bladder + blockage/rukna | Urology | `needs_confirmation` or `doctor_fallback` if unable to pass urine | Urine retention, prostate, urethral stricture |
| Urine/kidney/bladder + pain/pathri | Urology | `needs_confirmation` | Kidney stone, urinary tract stone, bladder stone |
| Male genital + swelling/pain | Urology | `needs_clarification` | Hydrocele, varicocele, balanitis, torsion fallback when severe |
| Male genital + foreskin tightness/infection | Urology | `needs_confirmation` | Phimosis, balanitis, circumcision |
| Vaginal/period + bleeding | Gynecology | `needs_confirmation` | Vaginal bleeding, irregular periods, fibroid, pregnancy-related fallback if pregnant |
| Vaginal + itching/burning/discharge | Gynecology | `needs_confirmation` | Vaginal infection, vaginal itching, vaginal swelling |
| Uterus/pelvic + lump/ganth/rasoli | Gynecology | `needs_clarification` | Fibroid, ovarian cyst, polyp, endometriosis |
| Pregnancy + bleeding/pain | Gynecology | `doctor_fallback` | Pregnancy bleeding should not be normal retrieval-first |
| Fertility context + conception issue | Fertility / IVF | `needs_confirmation` | Female infertility, male infertility, IVF/IUI, blocked tubes |
| Ear + pain | ENT | `needs_clarification` | Ear infection, eardrum issue, otitis, doctor consult |
| Ear + discharge/paani/pus | ENT | `needs_clarification` | Ear infection, eardrum perforation, myringotomy |
| Ear + hearing issue/tinnitus | ENT | `needs_confirmation` | Hearing loss, tinnitus, cochlear/otosclerosis depending results |
| Nose/sinus + blockage/band | ENT | `needs_clarification` | Septoplasty, sinusitis, nasal polyps, turbinate reduction |
| Nose/sinus + discharge/paani | ENT | `needs_clarification` | Sinusitis, rhinosinusitis, allergy-like consult |
| Throat + pain/infection | ENT | `needs_clarification` | Tonsillitis, throat infection, voice/vocal cord |
| Snoring/sleep + breathing issue | ENT | `needs_confirmation` or `doctor_fallback` if severe breathing | Snoring/sleep apnea consult |
| Abdomen/stomach + pain | General surgery / gastro | `needs_clarification` | Gallstone, appendicitis, hernia, acidity/endoscopy, doctor consult |
| Abdomen + severe pain/fever/vomiting | General surgery / emergency | `doctor_fallback` | Urgent clinical evaluation |
| Abdomen/groin/navel + swelling/lump | General surgery | `needs_confirmation` | Hernia variants, lipoma/cyst if superficial |
| Gallbladder/kidney unspecified `pathri` | Urology or general surgery | `needs_clarification` | Kidney/urinary stone vs gallbladder stone |
| Knee/joint/bone + pain | Orthopedics | `needs_clarification` | Knee pain, ligament injury, arthritis, replacement |
| Knee/joint/bone + swelling/injury | Orthopedics | `needs_clarification` | Ligament tear, sprain, fracture/injury consult |
| Spine/back/kamar + pain/weakness | Orthopedics / spine | `needs_clarification` | Slip disc, spine surgery, sciatica-like consult |
| Chest + pain | Emergency / doctor | `doctor_fallback` | Bypass retrieval |
| Chest + breathing issue | Emergency / doctor | `doctor_fallback` | Bypass retrieval |
| Eye + vision issue | Ophthalmology | `needs_confirmation` | Cataract, LASIK, retina, glaucoma depending terms |
| Eye + pain/redness/sudden vision loss | Ophthalmology / emergency | `doctor_fallback` for sudden/severe | Urgent eye evaluation |
| Skin + itching/rash/allergy | Dermatology | `needs_confirmation` | Urticaria, skin allergy, infection, doctor consult |
| Skin + lump/cyst | Dermatology / general surgery | `needs_clarification` | Cyst, sebaceous cyst, lipoma, infected cyst |
| Hair + hair fall/loss | Hair / aesthetics | `needs_confirmation` | Hair fall PRP, hair transplant |
| Teeth/dental + pain/gap/bite | Dental | `needs_confirmation` | Teeth straightening, clips, bite correction |
| Veins/leg + swelling/pain | Vascular | `needs_clarification` | Varicose veins, DVT, edema, vascular consult |
| Veins/blood vessel + clot/blockage | Vascular | `doctor_fallback` if acute/severe | DVT/thrombectomy/angioplasty only after clinical context |
| Weight/obesity + weight loss intent | Bariatrics | `needs_confirmation` | Weight loss surgery, injections, pills, gastric balloon |
| Breast/nipple + lump/pain/discharge | Breast surgery / doctor | `doctor_fallback` or `needs_clarification` | Conservative due cancer/pregnancy/infection possibilities |
| No body context + bleeding | Unknown | `doctor_fallback` or `needs_clarification` | Ask source of bleeding: stool, urine, vaginal/period, nose, wound |
| No body context + pain | Unknown | `needs_clarification` | Ask location: chest, abdomen, urine/kidney, joints, back, ear, eye |
| No body context + swelling/lump | Unknown | `needs_clarification` | Ask location: skin, breast, anus, joint, leg/vein, abdomen/groin |
| No body context + weakness/fever | Unknown | `doctor_fallback` | Too broad for treatment routing |

## 5. Safety Precedence

Safety rules should run before normal retrieval confidence thresholds. If a safety pattern is detected, the router should not show a specific treatment card as the primary recommendation.

Conservative safety fallback combinations:

| Pattern | Recommended state | Reason |
|---|---|---|
| Chest pain, seene me dard, chest tightness | `doctor_fallback` | Possible cardiac/emergency symptom |
| Breathing difficulty, saans lene me dikkat, breathlessness, choking | `doctor_fallback` | Possible emergency symptom |
| Severe bleeding, bahut bleeding, bleeding ruk nahi rahi, heavy blood loss | `doctor_fallback` | Needs clinical triage |
| Pregnancy + bleeding or severe pain | `doctor_fallback` | Pregnancy complications need immediate evaluation |
| Fainting, behoshi, unconscious, chakkar with severe symptoms | `doctor_fallback` | Potential emergency |
| Severe abdominal pain, pet me bahut dard, abdomen pain with fever/vomiting | `doctor_fallback` | Appendicitis, obstruction, ectopic, gallbladder, etc. |
| Unable to pass urine, peshab bilkul nahi aa raha | `doctor_fallback` | Acute urinary retention can be urgent |
| Testicular severe pain/swelling, andkosh me achanak dard | `doctor_fallback` | Possible torsion or acute condition |
| Sudden vision loss, aankh ki roshni achanak kam, eye injury | `doctor_fallback` | Urgent eye evaluation |
| Severe allergic reaction, swelling of face/lips/tongue, breathing with rash | `doctor_fallback` | Possible anaphylaxis |
| Leg swelling with breathlessness/chest pain | `doctor_fallback` | Possible clot-related emergency |
| Blood in stool/urine with severe pain, dizziness, or heavy bleeding | `doctor_fallback` | Needs clinical evaluation before product routing |
| Child/infant + severe fever/breathing/bleeding | `doctor_fallback` | Higher-risk group |
| Emergency words: emergency, urgent, bahut zyada, unbearable, cannot walk, accident | `doctor_fallback` | User is asking for urgent care |

Safety precedence should be additive: a body-system match can still be useful for the fallback message, but it should not override fallback.

## 6. Catalog Enrichment Needs

The current catalog has sparse patient-language coverage for many body systems. Enrichment should add high-signal body context terms to the appropriate specialty pages and avoid adding generic symptoms alone.

### Proctology / anorectal

Add to piles/colorectal/fissure/fistula/abscess/rectal pages as appropriate:

- tatti, potty, latrine, lettering, motion, stool, mal, bowel movement
- rectal, anus, anal, gudha, gudhe, pichwada, pichwade
- tatti me khoon, tatti mei khoon aana, potty me blood, latrine me khoon, motion me blood, blood in stool, stool blood, rectal bleeding, anal bleeding, mal me khoon
- motion karte waqt dard, potty me dard, latrine me dard
- gudha se pus, anus se pus, pichwade se paani, anal discharge
- gudha me sujan, anus lump, bawasir ke masse

### Urology / kidney / bladder

Add to kidney stone, urinary tract stone, bladder, prostate, urethral pages:

- peshab, pesab, pisab, urine, urinary, bladder, kidney, gurda, gurde
- peshab me khoon, urine me blood, blood in urine, hematuria
- peshab me jalan, urine burning, burning urination
- peshab rukna, urine rukna, urine nahi aa raha, urine flow kam
- kidney pain, kamar ke side dard, flank pain, gurde me dard
- peshab me pathri, kidney pathri, bladder stone, urinary stone

### Male genital / scrotal

Add to phimosis, balanitis, circumcision, hydrocele, varicocele, torsion pages:

- ling, penis, foreskin, chamdi tight, foreskin tight, khatna
- ling me sujan, penis swelling, penis pain, ling me jalan
- foreskin infection, foreskin me jalan, foreskin me pus
- andkosh, testicle, scrotum, testicular pain, andkosh me dard, andkosh me sujan
- hydrocele, varicocele, nas me sujan, andkosh latakna

### Gynecology / vaginal / menstrual

Add to vaginal bleeding/infection/itching/swelling, irregular periods, fibroid, ovarian cyst, uterus pages:

- yoni, vaginal, vagina, uterus, bachhedani, garbhashay
- period, periods, mahavari, maasik, monthly bleeding
- period me zyada bleeding, periods irregular, periods late, periods nahi aaye
- yoni se khoon, vaginal bleeding, spotting, period ke alawa bleeding
- white discharge, safed pani, yoni se paani, vaginal discharge
- yoni me jalan, yoni me khujli, vaginal itching, vaginal burning
- pelvic pain, pet ke niche dard, uterus pain
- rasoli, fibroid, bachhedani me ganth, ovarian cyst

### Pregnancy / miscarriage / abortion

Add with safety-aware routing:

- pregnant, pregnancy, garbh, garbhwati, garbhavastha
- pregnancy me bleeding, pregnancy me pain, pregnancy me pet dard
- miscarriage, garbhpat, pregnancy loss, spotting during pregnancy
- ectopic pregnancy, pregnancy me severe pain
- abortion, MTP, pregnancy terminate, garbhpat ki goli

### Fertility / IVF

Add to infertility/IVF/IUI/male infertility/female infertility pages:

- bacha nahi ho raha, bachcha nahi ho raha, conceive nahi ho raha
- pregnancy nahi ho rahi, garbh nahi thahar raha, santan nahi
- sperm count, sperm problem, semen problem
- egg problem, AMH low, ovulation problem
- tube blocked, fallopian tube blocked, IVF, IUI, test tube baby

### ENT - ear

Add to ear infection, eardrum, tinnitus, hearing pages:

- kaan, kan, ear, kaan dard, ear pain
- kaan se paani, ear discharge, kaan se pus
- kaan band, sunai kam, hearing loss, sunai nahi dena
- kaan me awaaz, kaan me shor, tinnitus
- kaan ka parda, eardrum hole, parda phatna

### ENT - nose / sinus / throat

Add to sinus, septoplasty, nasal polyps, tonsil, throat, snoring pages:

- naak, nose, nasal, nathuna, naak band, nose blocked
- naak se paani, naak behna, sinus, sinus pain
- naak ki haddi tedhi, deviated septum
- gala, throat, gale me dard, tonsil, tonsils, gale me sujan
- kharrate, kharate, snoring, sote waqt saans rukna
- awaaz baithna, voice problem, vocal cord

### Ophthalmology

Add to eye/vision pages:

- aankh, ankh, aankhon, eye, vision, roshni
- chashma hatana, number hatana, LASIK, eye laser
- motiyabind, cataract, lens
- aankh me dard, aankh me jalan, aankh lal
- dhundla dikhna, blurry vision, double vision
- retina, glaucoma, kala motia

### Orthopedics / spine

Add to joint and spine pages:

- ghutna, ghutne, knee, knee pain, ghutne me dard
- joint pain, jodo ka dard, haddi dard, bone pain
- ligament tear, moch, sprain, chot, injury
- shoulder, kandha, hip, kulha, elbow, ankle, foot, hand, wrist
- back pain, kamar dard, spine pain, slip disc, sciatica
- swelling after injury, ghutne me sujan

### General surgery / gastro / abdomen

Add to hernia/gallstone/appendix/endoscopy pages:

- pet, stomach, abdomen, pait, pet dard
- pet me sujan, nabhi me sujan, groin swelling
- hernia, aant utarna, nabhi hernia
- appendix, appendicitis, right side pet dard
- gall bladder, pit ki thaili, pitt ki thaili, gallstone
- acidity, endoscopy, pet me jalan

### Vascular

Add to varicose/DVT/edema/artery pages:

- nas, nasen, vein, artery, blood vessel
- pair ki nasen, pair me sujan, pair me dard
- varicose veins, spider veins, nas phoolna
- blood clot, khoon ka thakka, DVT
- blood flow kam, artery blockage, nas band

### Dermatology / skin / cysts

Add to skin/cyst/rash pages:

- skin, twacha, rash, daane, dane, allergy, hives
- khujli, itching, skin itching, fungal infection
- daag, pigmentation, safed daag, vitiligo
- cyst, ganth, gath, lipoma, sebaceous cyst
- infected cyst, pus, skin me sujan, redness

### Aesthetics / hair

Add to hair/cosmetic pages:

- baal jhadna, baal girna, hair fall, hair loss
- ganjapan, baldness, baal patle, hair thinning
- beard transplant, moustache transplant, eyebrow transplant
- face fat, double chin, charbi, liposuction, tummy tuck
- breast size, male breast, gynecomastia, cosmetic surgery

### Bariatrics / weight loss

Add to weight-loss pages:

- motaapa, motapa, obesity, weight gain
- vajan kam, weight loss, charbi kam, fat loss
- weight loss surgery, bariatric surgery, gastric balloon
- weight loss injection, Ozempic, weight loss pills

### Dental

Add to dental pages:

- daant, dant, teeth, tooth, dental
- daant tedhe, teeth straightening, braces, clips
- teeth gaps, daant me gap
- overbite, underbite, open bite, crossbite

## 7. Query Normalization Needs

`query_normalizer.py` should remain conservative. It should solve deterministic text cleanup and high-confidence variants before retrieval/routing, not clinical classification.

Good normalizer responsibilities:

- Whitespace cleanup: repeated spaces, leading/trailing spaces.
- Missing spaces in common compounds: `bodypain` -> `body pain`, `chestpain` -> `chest pain`, `kidneystone` -> `kidney stone`.
- Common romanization variants: `mei` -> `me` only if product accepts this broad transliteration normalization; `kharate` -> `kharrate`; `pattari`/`patthri` -> `pathri`.
- Common English variants: `bleed`/`bleeding`, `swollen`/`swelling`, `blocked`/`blockage` where safe.
- Singular/plural where not clinical: `period`/`periods`, `stone`/`stones`, `tonsil`/`tonsils`, `vein`/`veins`.
- High-confidence typo fixes: `bawaseer`/`bavasir`/`bawasir`, `peshab`/`pesab`, `motiyabind` variants, `chashma` variants.
- Script and punctuation normalization if needed later: remove duplicate punctuation, normalize hyphen/slash boundaries.

Not normalizer responsibilities:

- Do not turn `khoon` into `vaginal bleeding`, `blood in stool`, or `blood in urine` without body context.
- Do not choose a specialty from generic symptom terms.
- Do not convert broad `pet dard` into a specific treatment.
- Do not bypass safety rules.

## 8. Router Rules vs Catalog Enrichment

| Improvement | Classification | Why |
|---|---|---|
| Add exact patient terms like `tatti`, `potty`, `latrine`, `peshab`, `yoni`, `kaan`, `naak`, `aankh` to appropriate pages | Catalog enrichment | Improves semantic and BM25 evidence at the source |
| Add body-system synonym dictionaries independent of catalog | Synonym dictionary | Lets router detect body context even if retrieval misses it |
| Normalize `mei` to `me`, common spelling variants, missing spaces | Query normalizer | Deterministic text cleanup before matching |
| Detect generic symptom groups such as bleeding/pain/swelling/discharge | Router guard / synonym dictionary | Needed before trusting retrieval score |
| Detect body-system context groups | Router guard / synonym dictionary | Prevents generic symptom words from choosing wrong specialty |
| Safety precedence for chest pain, breathing difficulty, severe bleeding, pregnancy bleeding | Safety fallback | Must bypass treatment routing |
| If one body system + generic symptom is present, constrain alternatives to same specialty | Router guard | Avoids vaginal/vascular results for stool-blood queries |
| If generic symptom is present with no body context, ask source/location | UI clarification | User must provide missing context |
| If multiple body systems are present, ask clarification unless one is safety-critical | UI clarification / safety fallback | Avoids overconfident routing |
| Import raw `meta_keywords` into catalog searchable text | Catalog enrichment | Raw scrape contains useful SEO patient language missing from current catalog |
| Add `specialty` metadata to each catalog item | Catalog enrichment / data model | Enables retrieval filtering and specialty-aware alternatives |
| Score boost when result specialty matches detected body system | Router guard or search reranking | Keeps retrieval flexible but prevents cross-specialty symptom matches |
| Score penalty when result specialty conflicts with detected body system | Router guard or search reranking | Prevents high `khoon`/`bleeding` matches from wrong specialty |

Recommended layer order:

1. Normalize query text.
2. Detect safety signals.
3. Detect generic symptom groups.
4. Detect body-system context groups.
5. If safety signal present, return `doctor_fallback`.
6. If generic symptom present and no body context, return `needs_clarification`.
7. If generic symptom plus body context, constrain/confirm within matching specialty.
8. Run retrieval or rerank retrieval with specialty alignment.
9. Use retrieval confidence only after body-system/safety checks.

## 9. Implementation Priority

Priority ranking uses patient safety risk, wrong-specialty likelihood, demo importance, and implementation risk.

### P0 - Safety fallbacks

1. Chest pain and breathing difficulty fallback.
2. Severe bleeding fallback.
3. Pregnancy plus bleeding/pain fallback.
4. Severe abdominal pain fallback.
5. Urinary retention and testicular severe pain fallback.
6. Sudden vision loss fallback.

Reason: highest patient-safety risk and low implementation risk because these are conservative fallbacks.

### P1 - Generic symptom plus body-system router guard

1. Stool/rectal/anus plus bleeding/pain/discharge/swelling -> proctology clarification.
2. Urine/kidney/bladder plus blood/burning/blockage -> urology clarification/fallback.
3. Vaginal/period/uterus plus bleeding/discharge/itching/swelling -> gynecology confirmation.
4. Ear/nose/throat plus discharge/blockage/hearing/pain -> ENT clarification.
5. Eye plus vision/pain/redness -> ophthalmology confirmation/fallback.
6. Joint/bone/spine plus pain/swelling/injury -> orthopedics clarification.

Reason: directly addresses the observed failure class while remaining general.

### P2 - Catalog specialty metadata and enrichment

1. Add or generate `specialty` metadata for every catalog item.
2. Add body-system terms to each specialty group.
3. Include raw `meta_keywords` selectively or through a curated extraction process.
4. Add specialty-specific Hinglish terms to high-risk pages first: proctology, urology, gynecology, ENT, ophthalmology, orthopedics.

Reason: improves retrieval quality and reduces dependence on hard router rules.

### P3 - Reranking / specialty filtering

1. If body-system context is detected, rerank matching-specialty results above cross-specialty generic-symptom matches.
2. Penalize results that match only generic symptoms and conflict with detected body system.
3. Preserve retrieval alternatives but group them by specialty if uncertainty remains.

Reason: stronger relevance, moderate implementation risk.

### P4 - Query normalization expansion

1. Add safe spelling variants and missing-space fixes.
2. Add romanization variants after tests prove no harmful conflation.
3. Keep clinical interpretation out of normalizer.

Reason: helpful but should not carry the safety burden.

### P5 - UI clarification improvements

1. For no-context bleeding, ask "Where is the bleeding from?" with stool/urine/vaginal/nose/wound/not sure.
2. For no-context pain, ask location.
3. For lump/swelling, ask location and urgency.
4. For body-system plus generic symptom, show same-specialty chips, not global generic chips.

Reason: improves user journey after router guard exists.

## 10. Do Not Implement Code

This document is only a design plan.

Files that should remain unchanged for this task:

- `app.py`
- `search.py`
- `catalog.py`
- `intent_router.py`
- `query_normalizer.py`

Suggested next implementation artifact, when approved: a small `body_system_router.py` or equivalent data-driven module containing:

- `GENERIC_SYMPTOM_GROUPS`
- `BODY_SYSTEM_CONTEXT_GROUPS`
- `SAFETY_PATTERNS`
- `SPECIALTY_TO_SLUGS`
- a `classify_body_system_intent(query)` function
- tests for high-risk query matrices before integration with `intent_router.py`
