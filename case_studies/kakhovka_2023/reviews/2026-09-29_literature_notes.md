
\\wsl.localhost\Ubuntu-24.04\home\niko\repo\floodstate-eo\case_studies\kakhovka_2023\publication\floodstate_eo_scientific_code_review_2026-09-28.md
Так. Я перевірив літературу саме під зауваження з аудиту. Важливий результат: **основні методологічні претензії рецензента добре підкріплюються науковою літературою**. Частина F01–F20 — це конкретні програмні дефекти, які доводяться безпосередньо кодом і синтетичними тестами, а література пояснює, **чому такі дефекти науково суттєві**. У самому аудиті F01–F04 саме так і сформульовані: як перевірені реалізаційні проблеми uncertainty propagation. :chatgpt-content-reference{index="0"}

Я б побудував наукову основу рецензії так:

| Що у твоєму аудиті | На чому це стоїть у літературі | Ключове джерело |
|---|---|---|
| F01 — спільні/корельовані похибки Monte Carlo | Просторові похибки не можна автоматично робити незалежними; MC має відтворювати spatial auto-/cross-correlation | Heuvelink et al.; Hawker et al. |
| F02 — неправильне поле DEM noise | DEM errors просторово корельовані; stochastic DEM має відтворювати і variance, і spatial structure | Hawker et al. 2018; Hengl et al. 2010 |
| F03 — offset двічі | Це безпосередній code defect; література потрібна лише для загального error-propagation framework | Heuvelink et al. |
| F04 — total-water CI не з total ensemble | Невизначеність вихідної величини треба отримувати пропагацією повної uncertainty model | Heuvelink; Monte-Carlo UQ literature |
| F05 — interpolation ≠ observation | Інтерпольовані дані мають власну uncertainty; gaps і support мають враховуватися | uncertainty propagation literature |
| F06/F07 — terrain reconstruction ≠ hydrodynamics | HAND/GeoFlood/FwDET — terrain-based approaches, відмінні від hydraulic routing | Nobre 2011; Zheng 2018; FwDET 2019 |
| F08 — spatial leakage | Звичайний CV при spatial autocorrelation може бути оптимістичним; spatial separation потрібна для transfer claims | Roberts et al. 2017 |
| F09 — threshold на training | calibration/validation мають бути відокремлені від fit | стандартний ML validation framework |
| F10 — weak labels ≠ ground truth | noisy/weak labels несуть похибки teacher procedure; agreement із ними ≠ незалежна accuracy | Algan & Ulusoy 2021 |
| F11 — TEST використано при прийнятті рішень | адаптивне повторне використання holdout/test може спричинити overfitting до test | Dwork et al. 2015; Feldman et al. 2019 |
| F12 — ICESat-2 calibration + validation | reference data для accuracy assessment мають бути незалежними/вищої якості; reuse треба явно враховувати | Olofsson et al. 2014 |
| F13 — hypsometry поза діапазоном | екстраполяція area–elevation/storage curve за межі спостережень має більшу/невизначену похибку | сучасні lake/reservoir studies |
| F14 — balance | \(\Delta S\) — зміна запасу між межами інтервалу; mass balance вимагає узгоджених inflow/outflow/storage | USGS continuity equation |
| F16/F17 — reproducibility | повний workflow, версії, параметри та provenance мають бути збережені | Sandve et al. 2013 |
| F20 — лише 40 draws | Monte-Carlo prediction intervals самі мають sampling uncertainty; convergence треба перевіряти | Environmental Modelling & Software 2021 |

## 1. Найсильніше джерело для F01–F03: DEM і просторово корельована невизначеність

**Hawker, Bates, Neal & Rougier (2018), Frontiers in Earth Science — “Perspectives on Digital Elevation Model (DEM) Simulation for Flood Modeling…”**

Це майже ідеальне джерело для твоєї статті. Автори прямо наголошують, що DEM error є **просторово автокорельованим**, а простого глобального RMSE/σ недостатньо для реалістичного stochastic DEM. Для flood modelling вони рекомендують stochastic/geostatistical simulation, яка враховує spatial error structure. :chatgpt-content-reference{index="1"}

Це безпосередньо підтримує зауваження аудиту:

> не можна просто згенерувати coarse white noise → `zoom()` → помножити на NMAD і вважати, що отримано правильне поле DEM uncertainty.

Сам аудит показав конкретніше: заявлене \(\sigma=1.60\) м після інтерполяції фактично стало близько \(1.06\) м. Це вже **твій конкретний computational finding**, а Hawker et al. дають наукове обґрунтування, чому variance і spatial covariance поля треба перевіряти. :chatgpt-content-reference{index="2"}

[Hawker et al. 2018 — full article](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2018.00233/full?utm_source=chatgpt.com)

Ще сильніше — **Hengl, Heuvelink & van Loon (2010), HESS**. Вони саме використовують **geostatistical simulations для propagation DEM error** у гідрологічно залежний продукт — stream networks. :chatgpt-content-reference{index="4"}

[Hengl et al. 2010 — HESS](https://hess.copernicus.org/articles/14/1153/2010/hess-14-1153-2010.html?utm_source=chatgpt.com)

---

## 2. Для F01: чому covariance між зонами справді важлива

Тут хороша фундаментальна робота:

**Heuvelink, Brown & van Loon — “A probabilistic framework for representing and simulating uncertain environmental variables”.**

Їхня схема прямо дозволяє statistical dependence між невизначеностями в різних spatial locations. Тобто в spatial Monte Carlo не достатньо задати правильну σ окремо в кожній клітині: треба правильно задати **залежність між клітинами/зонами**. :chatgpt-content-reference{index="6"}

Це прямо підкріплює логіку F01:

> якщо datum/closure error є одним загальним систематичним offset для всього домену, один Monte Carlo draw повинен нести той самий realization цього offset через усі зони.

У твоєму коді рецензент встановив протилежне: realization генерується заново всередині zone loop. :chatgpt-content-reference{index="7"}

Тобто тут можна дуже сильну фразу написати в Methods:

> *Spatially shared error components were propagated jointly across the complete domain rather than independently by computational tile, thereby preserving their prescribed cross-zone covariance.*

---

## 3. F20 — 40 Monte Carlo draws справді треба обґрунтовувати

Тут я знайшов дуже влучну роботу:

**“How certain are our uncertainty bounds? Accounting for sample variability in Monte Carlo-based uncertainty estimates”, Environmental Modelling & Software, 2021.**

Автори показують, що prediction intervals, отримані Monte Carlo, **самі мають sampling uncertainty**, а при недостатній кількості realizations їх ширина може бути суттєво неправильно оцінена. :chatgpt-content-reference{index="8"}

Це практично пряме теоретичне підкріплення F20.

Тобто проблема не в тому, що:

> «40 — це магічно заборонене число».

Так говорити не треба.

Правильно:

> **кількість draws не повинна вибиратися довільно; треба показати convergence потрібних output statistics.**

Наприклад:

```text
N = 40
N = 100
N = 250
N = 500
N = 1000
```

і дивитися, чи стабілізуються:

\[
P05,\quad P50,\quad P95
\]

та peak date.

Ще одна робота з *Environmental Modelling & Software* прямо ставить питання convergence Monte-Carlo analyses і рекомендує контролювати його, а не просто задавати число simulations. :chatgpt-content-reference{index="9"}

Це дуже сильна наукова опора під вимогу:

> **не просто збільшити 40 до 1000, а продемонструвати convergence.**

---

## 4. F06–F07: твоя реконструкція — науково нормальна, але це не гідродинамічна модель

Тут література навіть працює **на твою користь**.

**Nobre et al. (2011), Journal of Hydrology** ввели HAND — Height Above Nearest Drainage. Це terrain-based representation, яка нормалізує топографію відносно drainage network. :chatgpt-content-reference{index="10"}

**Zheng et al. (2018), Water Resources Research — GeoFlood** використовують high-resolution terrain + HAND + synthetic rating curves для швидкого inundation mapping. :chatgpt-content-reference{index="11"}

**FwDET v2.0 (2019), NHESS** теж визначає flood-water elevation і depth через DEM та геометрію inundation domain, а автори окремо наголошують на впливі DEM resolution та vertical accuracy. :chatgpt-content-reference{index="12"}

Тобто сама твоя ідея:

```text
WSE
    ↓
DEM comparison
    ↓
connectivity
    ↓
possible inundation
```

є абсолютно науковим класом методів.

Проблема тільки в термінології.

Це не:

> hydraulic simulation.

Це щось ближче до:

> **observation-constrained terrain-based/geometric inundation reconstruction.**

Сам аудит саме це й говорить. :chatgpt-content-reference{index="13"}

І я вважаю, що ця назва навіть **краща для статті**, бо чітко визначає твою реальну новизну.

---

## 5. І тут є дуже сильне сучасне джерело саме по Каховці

**Lehnigk, Pavelsky & Lang (2026), Geophysical Research Letters: “SWOT Satellite Observations of the Kakhovka Dam Break Flood Highlight Limitations of Outburst Flood Models.”**

Це обов'язково треба мати в статті.

Вони використали SWOT для Каховської повені й порівняли спостережені WSE із 2-D hydraulic simulations. Навіть після покращення bathymetry моделі не змогли одночасно добре відтворити **і flood stage, і timing**. :chatgpt-content-reference{index="14"}

Це для тебе дуже корисно.

Бо твій продукт можна позиціонувати не як:

> «ще одна гідродинамічна модель Каховської повені»,

а як:

> **спостереженнями обмежена геометрична реконструкція, яка не намагається відтворити повну flood-wave dynamics.**

І це чітко відділяє твою роботу від Lehnigk et al.

[Lehnigk, Pavelsky & Lang 2026 — GRL](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025GL120832?utm_source=chatgpt.com)

---

# 6. F08 — spatial leakage у RF20

Тут є майже канонічна робота:

**Roberts et al. (2017), Ecography — “Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure.”**

Вона має понад дві тисячі citations і спеціально розглядає ситуації, коли observations мають spatial dependence. Ідея проста: якщо spatially близькі observations розкинути між train/test, validation може оцінювати не реальну transferability, а здатність моделі інтерполювати біля вже побачених даних. :chatgpt-content-reference{index="16"}

[Roberts et al. 2017](https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.02881?utm_source=chatgpt.com)

Свіжіший огляд у *Nature Communications* прямо зазначає, що ігнорування spatial autocorrelation може створювати optimistic bias, а spatial blocking/buffering використовується для географічного відділення validation від training. :chatgpt-content-reference{index="18"}

Це саме твоя F08:

```text
фізична територія X
        ↓
      overlap
      ↙     ↘
    B1       B2

train       test
```

Тому зауваження рецензента:

> block ID повинен визначатися в **глобальному географічному просторі**, а не окремо в координатах кожного raster frame,

має дуже сильне методологічне підґрунтя. :chatgpt-content-reference{index="19"}

Тут лише одна тонкість: spatial CV не є універсальним способом оцінити будь-яку «map accuracy». Існує окрема дискусія про design-based accuracy assessment. Наприклад, Wadoux et al. застерігають, що spatial CV і statistically rigorous map accuracy assessment — не одне й те саме. :chatgpt-content-reference{index="20"}

Це навіть корисно для твоєї статті: **RF20 spatial CV треба називати оцінкою spatial generalization/agreement, а не незалежною area-wide map accuracy.**

---

# 7. F11 — після перегляду TEST він уже не untouched test

Це не моя думка і не смак рецензента.

**Dwork et al. — “Generalization in Adaptive Data Analysis and Holdout Reuse”** формально розглядають ситуацію, коли результати holdout використовуються для подальших рішень. Автори показують, що adaptive reuse може призводити до overfitting до самого holdout. :chatgpt-content-reference{index="21"}

Ще пряміше:

**Feldman, Frostig & Hardt (2019), ICML — “The advantages of multiple classes for reducing overfitting from test set reuse.”**

Перша теза роботи буквально така: excessive reuse of holdout data can lead to overfitting. :chatgpt-content-reference{index="22"}

У тебе ситуація не означає, що модель «підглянула labels TEST під час gradient descent».

Проблема тонша:

```text
TEST
 ↓
побачили failure 22/78
 ↓
змінили ontology/rules
 ↓
знову оцінили на TEST
```

Це **adaptive research decision**.

Тому рецензент дуже правильно рекомендує називати цей етап:

> exploratory,

а для confirmatory claim мати новий event/region або sealed holdout. :chatgpt-content-reference{index="23"}

---

# 8. F10 — weak labels не можна називати ground truth

Для цього є велика ML-література.

**Algan & Ulusoy (2021), Knowledge-Based Systems — survey on deep learning with noisy labels.**

Основна теза: label noise є реальною проблемою; deep neural networks здатні навіть memorise noise, тому структура та якість labels мають прямо враховуватися в інтерпретації результату. :chatgpt-content-reference{index="24"}

Для remote sensing є окрема література з weak supervision; сучасний огляд прямо розрізняє incomplete, inexact та inaccurate supervision. :chatgpt-content-reference{index="25"}

Тому якщо target у тебе створено через:

```text
S1
+
M2
+
reference-water rules
```

то:

\[
F1(U\!-\!Net,\ weak\ labels)
\]

означає перш за все:

> agreement with the weak-label procedure.

Не автоматично:

\[
F1(U\!-\!Net,\ true\ flood)
\]

Саме це сформульовано в F10. :chatgpt-content-reference{index="26"}

І твоя нинішня термінологія `agreement`, а не `accuracy`, тут науково значно безпечніша.

---

# 9. Для справжньої accuracy/area validation у remote sensing є дуже сильний стандарт

Я б обов'язково додав:

**Olofsson et al. (2014), Remote Sensing of Environment — “Good practices for estimating area and assessing accuracy of land change.”**

Це фундаментальна стаття для area estimation з remote sensing.

Вони розділяють:

- sampling design;
- response/reference design;
- statistical analysis;
- uncertainty;
- area estimation.

Ключова вимога: reference classification повинна бути істотно якіснішою за карту, яку перевіряють; uncertainty площ також треба оцінювати статистично. :chatgpt-content-reference{index="27"}

Це дуже важливо для твоєї роботи, тому що дає правильну межу між:

> **model-derived flood area**

і

> **statistically validated estimate of true flood area**.

Поки твій `247 km²` є насамперед model reconstruction.

Щоб заявляти його як independently validated true flood area, потрібна відповідна reference-sampling framework.

[Olofsson et al. 2014](https://www.sciencedirect.com/science/article/pii/S0034425714000704?utm_source=chatgpt.com)

---

# 10. F12 — ICESat-2 не може одночасно бути повністю calibration і повністю independent validation

Це випливає з тієї ж логіки validation.

Якщо:

```text
ICESat tracks
     ↓
DEM bias calibration
```

а потім ті ж observations використовуються:

```text
corrected DEM
     ↓
comparison with same ICESat
```

то це consistency check, але не повністю independent validation.

Правильна схема:

```text
ICESat tracks A
        ↓
    calibration

ICESat tracks B
        ↓
    validation
```

або spatial/pass/epoch holdout.

Olofsson et al. дають загальний принцип незалежного reference design. :chatgpt-content-reference{index="29"}

А дослідження reservoir/bathymetry також демонструють нормальну практику validation на **independent in-situ depth data**. :chatgpt-content-reference{index="30"}

Це дуже хороший precedent для твоєї конструкції.

---

# 11. F13 — історична hypsometry не повинна мовчки продовжуватись нижче 10 м

Тут також є література саме по reservoir/lake remote sensing.

У дослідженні area–volume reconstruction прямо зазначається, що hypsometric relationships побудовані для певного observed elevation range і **accuracy is not guaranteed when extrapolating beyond it**. :chatgpt-content-reference{index="31"}

Ще одна сучасна робота спеціально розділяє uncertainty для рівнів **всередині** і **поза elevation scope** hypsometric data та показує, що outside-range estimates мають більшу uncertainty. :chatgpt-content-reference{index="32"}

Тому твоя проблема з:

```python
np.interp()
```

дуже реальна.

Якщо таблиця починається з 10 м, а Python для 5 м мовчки повертає endpoint:

```text
10 m → 6.95 km³
9 m  → 6.95
8 m  → 6.95
...
5 m  → 6.95
```

це **не наукова екстраполяція**.

Це software behaviour.

Сам аудит зафіксував саме такий штучний plateau. :chatgpt-content-reference{index="33"}

Тому `NaN/out-of-domain` тут науково правильніший варіант, якщо окремої екстраполяційної моделі немає.

---

# 12. F14 — water balance: тут все дуже класично

USGS формулює reservoir water balance:

\[
\mathrm{Inflow}
=
\mathrm{Outflow}
+
\Delta S
\]

а в розгорнутому вигляді додаються precipitation, evaporation, groundwater тощо. :chatgpt-content-reference{index="34"}

Для routing USGS прямо записує:

\[
\frac{dS}{dt}=I-Q.
\] :chatgpt-content-reference{index="35"}


Тому якщо ти хочеш баланс за тиждень:

\[
\Delta S_{week}
\]

має відповідати зміні storage **між початком та кінцем відповідного інтервалу**.

Не просто:

\[
mean(S_{week2})-mean(S_{week1}).
\]

Особливо якщо integrated inflow визначений за іншими temporal boundaries.

І рецензент тут не просто теоретизує: він отримав розбіжність до **0.757 km³** між двома способами розрахунку. :chatgpt-content-reference{index="36"}

Ще важливіше: якщо на 6 червня ти переходиш з Rozumivka на outlet, стрибок storage може містити:

```text
фізичну зміну
+
різницю між джерелами
```

а це вже не чистий \(dS\).

---

# 13. І нарешті reproducibility

Тут твій репозиторій насправді вже сильніший за багато наукових робіт.

**Sandve et al. (2013), PLOS Computational Biology — “Ten Simple Rules for Reproducible Computational Research.”**

Перше правило: для кожного результату треба знати, **як саме він був отриманий**, з точними inputs, parameters, software versions та workflow. :chatgpt-content-reference{index="37"}

Саме тому твої:

```text
manifests
SHA
tables
runs
provenance
generated figures
```

— це реально сильна частина роботи.

Але є важлива різниця:

\[
\boxed{\text{reproducible} \neq \text{scientifically valid}}
\]

Reproducibility відповідає:

> Чи можу я повторити обчислення?

Validation відповідає:

> Чи правильно це обчислення представляє явище, яке ми досліджуємо?

І саме це є центральною думкою всього аудиту: repository provenance сильний, але він не може сам виправити помилкову uncertainty model. :chatgpt-content-reference{index="38"}

---

## Яке «ядро» літератури я б реально поставив у твою статтю

Не треба засипати manuscript 40 посиланнями. Для методологічного каркаса достатньо приблизно **10 ключових робіт**:

**Hawker et al., 2018** — DEM uncertainty + spatial structure + stochastic simulation. :chatgpt-content-reference{index="39"}  
**Hengl, Heuvelink & van Loon, 2010** — DEM error propagation in hydrology. :chatgpt-content-reference{index="40"}  
**Nobre et al., 2011** — HAND / terrain-based hydrologic representation. :chatgpt-content-reference{index="41"}  
**Zheng et al., 2018** — GeoFlood / terrain-driven inundation mapping. :chatgpt-content-reference{index="42"}  
**Cohen et al./FwDET v2, 2019** — DEM/WSE geometric flood-depth estimation. :chatgpt-content-reference{index="43"}  
**Roberts et al., 2017** — spatial CV. :chatgpt-content-reference{index="44"}  
**Olofsson et al., 2014** — independent reference data, map accuracy and area estimation. :chatgpt-content-reference{index="45"}  
**Dwork et al., 2015 / Feldman et al., 2019** — adaptive holdout/test reuse. :chatgpt-content-reference{index="46"}  
**Lehnigk et al., 2026** — SWOT + Kakhovka + limitations of flood modelling. :chatgpt-content-reference{index="47"}  
**“How certain are our uncertainty bounds?”, 2021** — Monte Carlo interval convergence/sample uncertainty. :chatgpt-content-reference{index="48"}  
**Sandve et al., 2013** — reproducible computational research. :chatgpt-content-reference{index="49"}

Тобто після цього пошуку я б сказав сильніше: **F01–F14 аудиту можна перетворити з “code review” на цілком нормальну methodological scientific review, де майже кожному принциповому зауваженню є опора в peer-reviewed literature.**

Найкращий наступний крок — не просто додати ці DOI у bibliography. Треба зробити для твого `manuscript.md` **таблицю “claim → finding Fxx → scientific source → що змінити в Methods/Discussion”**. Тоді ми фактично перетворимо цей аудит у план наукової ревізії статті.
Оця стаття для тебе дуже важлива, бо вона одночасно **закриває одну можливу заяву про новизну і відкриває сильнішу нішу**.

З її тексту випливає три речі. По-перше, вони вже зробили **SWOT-based analysis Каховської повені** і прямо називають свої дані першими високодетальними 2D спостереженнями великого outburst flood. Тобто заяву на кшталт *“first use of SWOT for the Kakhovka flood”* тобі використовувати не можна.

По-друге, їхня центральна задача інша за твою. Вони питають:

> Чи може 2D гідродинамічна модель GeoClaw відтворити SWOT-observed flood stage і timing?

Їхній ланцюг приблизно такий:

```text
bathymetry
   ↓
GeoClaw 2D simulation
   ↓
modeled WSE + timing
   ↓
comparison with SWOT
```

Їхній головний висновок: навіть після покращення батиметрії вони не змогли одночасно добре відтворити **і висоту хвилі, і час її проходження**. Це для тебе важливо, бо показує: навіть серйозна 2D hydraulic simulation не є автоматично «істинною картою повені».

Твоя конструкція принципово інша:

```text
SWOT / gauges / terrain / EO
            ↓
observationally constrained WSE
            ↓
DEM + connectivity
            ↓
daily possible inundation geometry
            ↓
comparison of flood-state definitions
            ↓
sensor disagreement / uncertainty
```

Тобто ти не намагаєшся сказати:

> «я правильно змоделював фізику хвилі».

Ти кажеш:

> **«я реконструюю просторовий стан затоплення з опорою на спостережуваний WSE і досліджую, як різні визначення води, рельєф і сенсорні обмеження змінюють оцінку площі».**

І це набагато краще узгоджується з тим, що ми вже побачили в аудиті твого репозиторію.

Є ще одна дуже цікава річ. Вони самі використовують **ICESat-2 ATL08 після осушення резервуара** для перевірки батиметрії. Але зверни увагу, що в них ICESat-2 використовується не як доказ «де була вода 8 червня», а як **перевірка геометрії оголеного дна**. Це якраз підтримує зауваження нашого аудиту: ATL08 2019–2025 або post-event elevation не можна автоматично трактувати як незалежне спостереження water state конкретного дня. Його сила — у перевірці terrain/bathymetry, а не event-water truth.

Ще важливіше: ця стаття дуже добре підкріплює твою ідею **не називати terrain reconstruction гідродинамічним моделюванням**. Самі Lehnigk et al. показують, наскільки складно відтворити peak stage і timing навіть повною 2D моделлю. Тому твоя чесна назва на кшталт:

> **observation-constrained daily geometric inundation reconstruction**

виглядає методологічно сильніше, ніж спроба подавати її як flood model у класичному hydraulic sense.

І я бачу тут можливу центральну наукову історію твоєї статті.

Lehnigk et al. показують:

```text
Observed SWOT WSE
        ≠
2D simulated flood dynamics
```

Ти можеш поставити наступне питання:

```text
Навіть якщо WSE спостерігається,
чи однозначно ми отримуємо flood extent?
```

І твоя відповідь, схоже:

> **ні**, тому що flood extent ще залежить від DEM, connectivity, baseline water definition, reed/wetland state, sensor visibility, temporal interpolation і того, що саме ми називаємо «new flood» та «total water».

Оце вже дуже цікава наукова лінія.

Фактично дві роботи можна поставити поруч так:

| Lehnigk et al. 2026 | Твоя робота |
|---|---|
| Чи відтворює hydraulic model SWOT WSE? | Що можна відновити, якщо WSE уже обмежений observations? |
| GeoClaw | terrain/connectivity reconstruction |
| flood stage | flood extent/state |
| timing | daily reconstructed geometry |
| bathymetry sensitivity | DEM/WSE/baseline/connectivity uncertainty |
| SWOT як validation hydrodynamics | SWOT як constraint reconstruction |
| hydraulic-model limitations | observation-to-inundation limitations |

І це вже не конкуренція з ними.

Це майже **наступний методологічний крок** після їхньої роботи.

Але є один важливий нюанс: щоб цю нішу реально захистити, треба виправити саме ті речі, які знайшов аудит — особливо F01–F04. Бо якщо твоя центральна теза буде про uncertainty від WSE → inundation, то **сам uncertainty engine повинен бути бездоганним**.

Я б після прочитання цієї статті навіть змінив позиціонування manuscript. Не робив би центром «ми reconstructed 247 km²». Сильніша історія:

> **Навіть за безпрецедентного SWOT constraint перехід від спостережуваної water-surface elevation до flood extent не є однозначним. Ми кількісно показуємо, як terrain representation, baseline-water ontology, sensor observability та uncertainty propagation визначають reconstructed inundation.**

Оце вже звучить як справді окрема стаття від Lehnigk et al., а не як ще одна карта Каховської повені.

Якщо хочеш, я наступним кроком можу **переписати твою novelty statement + Introduction gap на 5–7 абзаців так, щоб Lehnigk et al. стали не конкурентом, а головною відправною точкою твоєї статті**.
Так — ця стаття Roberts et al. (2017) дуже добре підкріплює саме F08 у твоєму аудиті. І тут зв’язок набагато пряміший, ніж просто «десь написано про cross-validation».
Їхня головна теза дуже проста: якщо сусідні у просторі точки схожі одна на одну, то випадково розкидати їх між train і test небезпечно. Модель може виглядати дуже точною просто тому, що тестові точки знаходяться поруч із навчальними.
У тебе проблема ще конкретніша. Є два перекривні кадри, умовно B1 і B2. Одна й та сама фізична місцевість може мати різні локальні block ID:
одна територія на місцевості
│
┌──────┴──────┐
↓             ↓
B1            B2
block 17      block 1000017
↓             ↓
TRAIN          TEST
Для коду це ніби два різні блоки.
Для Землі — це практично те саме місце.
Саме проти такого типу не-незалежності Roberts et al. і будують свою аргументацію.
Що саме з цієї статті підтримує твій F08
Перша ключова теза авторів:
training і evaluation data повинні бути незалежними.
Якщо вони просторово близькі або належать одній просторовій структурі, оцінка помилки стає занадто оптимістичною.
Тобто якщо твій RF20 показує, наприклад:
OA = 0.94
до виправлення overlap leakage, правильна інтерпретація не:
«RF20 має 94% реальної просторової точності».
А:
«RF20 отримав 0.94 agreement за поточної схеми cross-validation».
Бо ми ще не знаємо, наскільки ця цифра знизиться після справді незалежного spatial split.
Є особливо сильна фраза з логіки Roberts et al.:
nearby observations
↓
similar conditions
↓
train ≈ test
↓
prediction task becomes easier
↓
error appears too small
Це саме те, що рецензент називає spatial leakage.
І вони показують це не лише теоретично. У своїх симуляціях з Random Forest автори порівнювали:
random CV
vs
spatial block CV
vs
buffered CV
і побачили, що random split давав штучно малу помилку, тоді як spatial blocking був ближчим до помилки на справді незалежних просторових даних.
Те, що в них у прикладі теж використовується Random Forest, для твоєї статті навіть зручно.
Але тут є дуже важливий нюанс
Roberts et al. не говорять:
«чим більший spatial block, тим краще».
Навпаки.
Вони прямо пояснюють, що надто великі блоки можуть створити іншу проблему:
train:
vegetation A + low terrain

test:
vegetation B + high terrain
Тоді модель уже не просто перевіряється на новому місці — вона змушена екстраполювати в новий predictor space.
І performance може стати надто низькою не через погану модель, а через те, що test став зовсім іншим середовищем.
Тому для твоїх:
7.5 km
10 km
15 km
20 km
не можна сказати:
«20 km — науково правильніше за 10 km».
Треба питати:
який spatial scale відповідає масштабу просторової залежності наших даних і нашій prediction objective?
Оце вже серйозна наукова постановка.
Як це перекладається конкретно на RF20
Я б тепер вимагав таку процедуру.
Спочатку всі B1/B2 pixels переводимо в одну глобальну координатну систему.
Не:
block_id = row // block_size
окремо для B1 і B2.
А приблизно концептуально:
UTM Easting
UTM Northing
↓
global spatial grid
↓
global block ID
Тоді одна точка Землі:
E = 412000
N = 5183000
незалежно від того, прийшла вона з B1 чи B2, отримує один spatial block.
Після цього overlap треба або:
deduplicate
або використати ownership так, щоб одна фізична location існувала в sampling лише один раз.
І тоді:
TRAIN BLOCKS

████ ████

     spatial separation

□□□□ □□□□

TEST BLOCKS
стають справді географічно розділеними.
Ще сильніше: Roberts підказує тобі, як вибрати block size
Не просто:
«ми спробували 7.5, 10, 15, 20 км».
А спочатку дослідити spatial dependence.
Наприклад:
distance → similarity/error correlation

0 km     █████████
2 km     ███████
5 km     █████
8 km     ██
10 km    ≈ 0
Якщо spatial dependence фактично зникає приблизно біля 8–10 км, тоді 10 км можна науково аргументувати.
Roberts прямо рекомендують використовувати autocorrelation analysis як орієнтир для масштабу blocking.
Для тебе це може бути:
variogram;
correlogram;
Moran's I по distance bins;
residual spatial autocorrelation.
Але я б ще перевірив raw label/class structure, тому що Roberts окремо попереджають: дивитися лише на residuals недостатньо — модель уже могла частково «з’їсти» spatial structure.
І це ще цікаво для твого F11
У тебе в аудиті було:
при block size 15–20 км залишилося лише кілька test blocks.
І Roberts фактично пояснюють, чому це проблема.
Надто великий block:
краща незалежність
↑

але

менше блоків
менше test support
більша variance
більше extrapolation
Отже ти маєш trade-off:
малий block
→ leakage / optimistic accuracy

дуже великий block
→ мало незалежних test units / extrapolation

середній обґрунтований block
→ компроміс
Саме тому твоя нинішня sensitivity:
7.5
10
15
20 km
насправді корисна.
Тільки її треба трактувати не як:
«я знайшов найкращий block size».
А як:
sensitivity of evaluation to the assumed spatial independence scale.
Це значно науковіше.
Найголовніше для твоєї статті
Після Roberts я б узагалі трохи змінив формулювання результату RF20.
Не:
“RF20 achieved 0.9404 accuracy.”
А приблизно:
“RF20 achieved an agreement of 0.9404 under the original spatial-block evaluation; because overlapping acquisition frames can assign the same physical area to different local blocks, this estimate is treated as provisional pending globally defined, overlap-deduplicated spatial cross-validation.”
А після виправлення вже можна буде написати нормальний результат.
І ще одна дуже сильна фраза для Discussion:
Spatial cross-validation in this study is intended to quantify geographic generalization rather than pixel-level interpolation performance.
Оце вже дуже близько до логіки Roberts et al.
Якщо зовсім просто
Roberts кажуть:
Не можна посадити студента на іспит поруч із його конспектом і потім дивуватися, що він отримав 95%.
У твоєму RF20:
train pixel
↓
кілька сотень метрів / overlap
↓
test pixel
можуть бути майже тим самим «конспектом».
Тому F08 з аудиту після цієї статті я б вважав дуже добре науково обґрунтованим.
Але Roberts не доводить, що твій RF20 поганий або що 0.9404 обов'язково сильно впаде. Він доводить інше: до spatially independent rerun ми не маємо права трактувати цю цифру як надійну оцінку spatial generalization.
Це саме той рівень обережності, який потрібен у статті.
Так. **Це дуже сильне джерело саме для F20**, але його треба використати акуратно. Воно не доводить, що твій Monte Carlo «неправильний через 40 прогонів». Воно доводить інше: **квантилі, отримані з малого Monte Carlo ensemble, самі мають значну вибіркову невизначеність**.

Roy & Gupta прямо пишуть, що Monte Carlo prediction intervals можуть суттєво недооцінювати ширину невизначеності, якщо sample size недостатній. :chatgpt-content-reference{index="0"}

### Що це означає зовсім просто

У тебе є 40 реалізацій:

```text
draw 1
draw 2
...
draw 40
```

і ти хочеш знайти, наприклад:

```text
P05
P50
P95
```

Для `P50` ситуація ще більш-менш стабільна, бо це середина розподілу.

А `P05` і `P95` лежать на краях.

При 40 реалізаціях:

\[
40\times0.05=2
\]

Тобто твій `P05` фактично визначається приблизно **другою найменшою реалізацією**, а `P95` — приблизно другою найбільшою.

Умовно:

```text
40 результатів

↓
1  2  3 ............... 38 39 40
   ↑                     ↑
  P05                   P95
```

Поміняй випадковий seed — і саме ці дві-три крайні реалізації можуть суттєво змінитися.

Оце і є головна проблема.

---

## Що показують Roy & Gupta

Автори спеціально досліджували, наскільки стабільні quantiles при різному Monte Carlo sample size.

Вони показують, що зі збільшенням \(N\):

- CDF стає стабільнішою;
- variance estimated quantiles падає;
- особливо сильно покращуються **tails**, тобто крайні квантилі. :chatgpt-content-reference{index="1"}

На їхній Figure 2 дуже добре видно різницю між:

```text
N = 100
```

і

```text
N = 1000
```

Саме крайні `2.5%` та `97.5%` quantiles при малому N мають великий розкид. :chatgpt-content-reference{index="2"}

---

## А тепер найцікавіше число

Для **95% prediction interval**, тобто:

\[
P_{2.5}-P_{97.5},
\]

вони пишуть, що формально потрібно щонайменше приблизно:

\[
N=39
\]

лише щоб узагалі мати достатньо точок для оцінювання цих двох хвостів без штучної екстраполяції. :chatgpt-content-reference{index="3"}

Тобто:

> **39 — це не “добра кількість Monte Carlo runs”. Це практично математичний мінімум для 95% interval.**

Це дуже важлива різниця.

---

# Але у тебе P05–P95

У твоєму аудиті, наскільки я бачу, використовувався:

\[
P05-P95
\]

тобто **90% interval**, а не 95%.

І тут треба бути науково чесним.

Roy & Gupta прямо зазначають, що для 90% interval теоретичний мінімум нижчий — приблизно:

\[
N=19.
\]

:chatgpt-content-reference{index="4"}

Тому не можна написати:

> «Roy & Gupta доводять, що 40 draws недостатньо для P05–P95».

Це буде занадто сильне твердження.

Правильніше:

> **Roy & Gupta demonstrate that tail quantiles estimated from finite Monte Carlo ensembles have substantial sampling uncertainty, particularly for small ensembles; therefore, the stability of P05–P95 obtained from only 40 realizations should be explicitly assessed by convergence analysis.**

Оце вже науково бездоганно.

---

# І вони дають ще сильніший результат

Для 95% prediction interval автори отримали:

- при `N=100` uncertainty у ширині PI може бути близько **38%**;
- навіть при `N=1000` — близько **13%**.

:chatgpt-content-reference{index="5"}

Тобто уяви, що навіть 100 simulations вони вже вважають досить мало для надійної оцінки хвостів.

А в тебе:

```text
N = 40
```

Тому питання:

> «А чи стабільні мої P05 і P95?»

абсолютно обґрунтоване.

---

# Висновки самої статті ще жорсткіші

У Discussion вони пишуть, що 95% prediction intervals можуть бути досить неточними при:

\[
N<1000,
\]

а для дуже precise estimates у їхніх одновимірних прикладах можуть знадобитися порядки:

\[
N\sim10\,000.
\]

Водночас вони вважають \(N>1000\) потенційно прийнятним для одновимірних PDF. :chatgpt-content-reference{index="6"}

Але тут **не треба механічно робити висновок**:

> «значить мені треба 10 000 повних flood simulations».

Це було б неправильно.

Тому що необхідне \(N\) залежить від:

- форми твого distribution;
- нелінійності connectivity;
- того, яку величину ти оцінюєш;
- desired quantile;
- обчислювальної вартості;
- стабільності саме твоїх P05/P95.

---

# Що тоді правильно зробити у твоєму дослідженні

Я б не написав у коді:

```python
N_DRAWS = 1000
```

просто тому, що так сказав Roy.

Я б зробив **convergence experiment**.

Наприклад:

```text
N = 40
N = 100
N = 250
N = 500
N = 1000
```

І для кожного N дивився:

```text
P05 area
P50 area
P95 area
P95 - P05
peak date
```

Наприклад:

| N | P05 | P50 | P95 | Width |
|---:|---:|---:|---:|---:|
| 40 | 238 | 247 | 255 | 17 |
| 100 | ? | ? | ? | ? |
| 250 | ? | ? | ? | ? |
| 500 | ? | ? | ? | ? |
| 1000 | ? | ? | ? | ? |

І дивимося:

```text
40 → сильно рухається
100 → ще рухається
250 → трохи
500 → майже стабільно
1000 → стабільно
```

Тоді ти можеш **на своїх власних даних** сказати:

> “The ensemble size was increased until the P05, P50 and P95 inundation-area estimates reached numerical convergence.”

Оце буде набагато сильніше, ніж просто послатися на Roy.

---

# Але тут є ще важливіша річ

Roy & Gupta мають дуже сильний caveat.

Їхній підхід припускає, що Monte Carlo samples:

> **independent, equally likely draws from the same underlying stationary probability distribution.**

:chatgpt-content-reference{index="7"}

І вони прямо кажуть:

> якщо ця умова не виконується, виникають **інші серйозні проблеми**, які не можна виправити просто збільшенням sample size. :chatgpt-content-reference{index="8"}

Оце надзвичайно важливо для твого аудиту.

Бо це буквально означає:

```text
F01–F04 неправильні
        ↓
збільшити
40 → 1000 draws
        ↓
НЕ виправить модель
```

Ти просто 1000 разів запустиш неправильну uncertainty model.

Тому порядок має бути:

```text
F01
правильна covariance
       ↓
F02
правильний DEM error field
       ↓
F03
правильний offset
       ↓
F04
total area прямо з ensemble
       ↓
і ЛИШЕ ТОДІ
       ↓
40 / 100 / 250 / 500 / 1000
       ↓
convergence
```

---

# Тобто ця стаття фактично підтверджує F20 майже ідеально

Але я б переписав F20 трохи точніше.

Не:

> **“40 draws недостатньо.”**

А:

> **“Forty stochastic realizations are insufficiently justified for stable estimation of tail quantiles. Because finite Monte Carlo ensembles introduce sampling uncertainty into estimated prediction bounds, convergence of P05/P95 and peak-date statistics should be demonstrated empirically after correction of the underlying uncertainty model.”**

І далі citation:

**Roy, T., & Gupta, H. (2021). How certain are our uncertainty bounds? Accounting for sample variability in Monte Carlo-based uncertainty estimates. Environmental Modelling & Software. DOI: 10.1016/j.envsoft.2020.104931.** :chatgpt-content-reference{index="9"}

Це буде значно сильніше за просто «40 мало».

### Одним реченням

Roy & Gupta кажуть тобі:

> **Monte Carlo uncertainty теж має uncertainty.**

А для твоїх 40 draws це означає: **247 км² як median може бути відносно стабільним, а от межі на кшталт 238–255 км² можуть значно сильніше залежати від конкретних 40 випадкових реалізацій.**

Саме тому після виправлення F01–F04 треба перевірити **convergence P05/P95**, а не просто збільшити число прогонів навмання.
Так. І тепер є важлива знахідка: **окремі частини твоєї моделі вже робили раніше, а один старий підхід дуже близький до неї концептуально.** Але в цільовому пошуку я поки не знайшов роботи, де була б саме вся твоя комбінація: **просторово змінний WSE із SWOT + gauges → DEM → connectivity → daily reconstruction → pre-event baseline → new/total water → Monte Carlo uncertainty → cross-sensor disagreement**.

Найближчі роботи такі.

| Робота | Що робили | Наскільки близько до тебе |
|---|---|---|
| **Penton & Overton, 2007, RiM-FIM** | Landsat + high-resolution DEM + gauges → water-height surfaces → extent/depth → щоденна floodplain dynamics | **Дуже близько концептуально** |
| **c-HAND, 2024** | `DEM < gauge WSE` + обов'язкова connectivity до моря → inundation + depth | **Майже той самий базовий алгоритм**, але coastal |
| **USGS Tar River, 2007** | WSE profile − LiDAR DEM + hydraulic connectivity → inundation maps, прив'язані до gauge stage | Дуже близько |
| **Hou et al., 2022** | Landsat + LiDAR + hydraulic connectivity → 16-day extent, depth, volume | Дуже близько за продуктами |
| **FLEXTH, 2024** | satellite flood mask + terrain → оцінка WSE → connectivity propagation → depth/extent enhancement | Схожа логіка, але напрямок обернений |
| **Dale et al., 2026** | спостережений WSE → DTM flood-fill + connectivity → time series inundation/depth | **Алгоритмічно дуже близько** |
| **Lehnigk et al., 2026** | daily SWOT WSE Каховської повені + GeoClaw | Той самий event/WSE, але зовсім інший тип моделі |

### 1. Найнебезпечніша для заяви «ми придумали новий принцип» — Penton & Overton, 2007

Я знайшов їхню роботу **“Spatial modelling of floodplain inundation combining satellite imagery and elevation models”**.

Вони прямо пишуть, що створили техніку для **щоденного прогнозування/відновлення глибини води на заплаві**, поєднуючи high-resolution DEM, Landsat і gauge data. Їхній RiM-FIM поєднував spatial flood maps з історичними gauge flows, щоб показувати daily inundation floodplain. Вони також перевіряли connectivity і прибирали затоплені області, не пов'язані з реально спостережуваною водою. :chatgpt-content-reference{index="0"}

Це означає, що не можна заявляти:

> «Ми першими запропонували поєднувати DEM, супутникову воду, gauges і connectivity для щоденної реконструкції заплави».

Це вже було.

Але різниця серйозна.

Вони приблизно роблять:

```text
Landsat flood masks
      +
DEM
      +
gauge flow
      ↓
water-height surfaces
      ↓
daily floodplain state
```

Ти:

```text
SWOT WSE nodes + gauges
          ↓
spatial WSE field
          ↓
corrected DEM
          ↓
elevation + connectivity
          ↓
daily potential inundation
          ↓
pre-event baseline
       ↙       ↘
 new water   total water
          ↓
Monte Carlo uncertainty
          ↓
S1/S2/ICESat/ML disagreement analysis
```

Тобто **принцип DEM+water level+connectivity не новий**, але конкретна observational architecture може бути новою.

---

## 2. c-HAND — це майже твоя формула одним рядком

У 2024 році c-HAND для coastal flooding визначає затоплену клітину так:

```text
DEM elevation < observed gauge elevation
AND
connected to ocean
```

А depth:

```text
gauge WSE − DEM
```

Автори спеціально показують, що просто `DEM < WSE` затоплює ізольовані западини, тому додають connectivity і залишають тільки область, фізично пов'язану з ocean seed. :chatgpt-content-reference{index="1"}

Це майже буквально ядро твоєї моделі:

```text
zDEM < H
AND
Connected(seed)
```

Різниця:

**c-HAND**

```text
один coastal forcing / gauge level
→ static equilibrium
→ ocean connectivity
```

**у тебе**

```text
багато WSE observations уздовж ~великих річкових ділянок
→ spatially variable WSE
→ кожен день
→ river/floodplain connectivity
```

Тобто твоя новизна точно **не в операторі connectivity**.

---

## 3. USGS робив дуже схожу річ ще у 2007 році

Для Tar River Basin вони брали water-surface profiles, накладали їх на LiDAR DEM і залишали лише inundated cells, які були **hydraulically connected** із downstream gauge/model domain. Карти були прив'язані до реального gauge level і могли використовуватися майже в real time. :chatgpt-content-reference{index="2"}

Логіка:

```text
WSE profile
    ↓
WSE − DEM
    ↓
depth > 0 ?
    ↓
hydraulic connectivity?
    ↓
flood map
```

Знову дуже близько.

Але ключова відмінність: їхній WSE profile походив із calibrated hydraulic models для різних stage levels.

У тебе:

> **WSE значною мірою задається Earth observation, насамперед SWOT.**

Оце суттєва різниця.

---

# 4. Hou et al. 2022 — дуже важливий конкурент/попередник

**Hou, Van Dijk & Renzullo, Journal of Hydrology 2022**

Вони створили **16-day floodplain water dynamics**:

- extent;
- depth;
- volume;
- hydraulic connectivity;

на основі Landsat + airborne LiDAR DEM. Причому time series іде з 1987 року. :chatgpt-content-reference{index="3"}

Автори прямо кажуть, що оцінювали hydraulic connectivity на **кожному timestep**, після чого обчислювали spatial water depth і floodplain volume. :chatgpt-content-reference{index="4"}

Це вже дуже близько до твоїх:

```text
daily extent
daily depth
daily volume
```

Але в них основне спостереження:

```text
Landsat WATER EXTENT
```

і вони топографічно його downscale.

У тебе основне фізичне constraint:

```text
SWOT WATER SURFACE ELEVATION
```

і з нього ти реконструюєш можливий extent.

Оце принципово різні напрямки inference.

---

# 5. FLEXTH, 2024 — дуже цікава робота для тебе

Стаття в NHESS:

**“Water depth estimate and flood extent enhancement for satellite-based inundation maps”**.

Вони беруть satellite-derived wet/dry boundary, використовують DTM для оцінки water level, а потім **поширюють воду в contiguous low-lying no-data regions**, гарантуючи hydraulic connectivity. Після цього:

\[
depth = WSE-terrain.
\] :chatgpt-content-reference{index="5"}


Це майже дзеркальне відображення твоєї логіки.

Вони:

```text
observed EXTENT
       ↓
infer WSE
       ↓
terrain + connectivity
       ↓
complete extent/depth
```

Ти:

```text
observed WSE
       ↓
terrain + connectivity
       ↓
infer EXTENT/depth
```

Це дуже хороший paper для Introduction.

Бо дозволяє сказати:

> попередні методи часто починають із satellite-derived inundation boundary та використовують terrain для відновлення water levels/depth; ми розглядаємо complementary problem, де спостережуваний WSE є primary constraint для реконструкції inundation geometry.

Це вже виглядає цікаво.

---

# 6. А ось робота 2026 року, яка алгоритмічно ще ближча

**Dale et al., 2026, HESS — Community-scale urban flood monitoring...**

Вони отримують **спостережений WSE**, а потім запускають iterative flood-fill по DTM:

```text
observed WSE
    ↓
seed
    ↓
сусідня клітина нижче WSE?
    ↓ yes
затопити
    ↓
продовжувати connectivity
```

Потім:

\[
depth=WSE-DTM.
\]

І повторюють це **для кожного timestamp**, отримуючи time series inundation maps. :chatgpt-content-reference{index="6"}

Оце треба дуже уважно читати.

Тому що базовий computational principle:

> **observed WSE → DEM → connected flood-fill → extent/depth → temporal sequence**

у 2026 році вже точно існує.

Але їхня область приблизно сотні метрів, urban depression, WSE отриманий із camera/LiDAR observations, і вони фактично використовують майже planar WSE для локальної connected basin. Вони самі наголошують на припущеннях instantaneous propagation/no resistance. :chatgpt-content-reference{index="7"}

У тебе задача зовсім іншого масштабу:

```text
~великий річковий corridor
+
просторово змінний WSE
+
SWOT nodes
+
гідропости
+
daily gaps
+
дуже велика dam-break flood
```

---

# 7. І, звичайно, Lehnigk et al. 2026

Вони працюють **саме з Каховкою**, **саме з daily SWOT WSE** downstream.

Але використовують SWOT для перевірки:

```text
GeoClaw hydraulic simulation
            ↕
         SWOT WSE
```

а не для DEM-connected reconstruction inundation extent. :chatgpt-content-reference{index="8"}

Тому вони забирають у тебе:

> ❌ «перше використання SWOT для Kakhovka flood»

і:

> ❌ «перша daily SWOT analysis Kakhovka».

Але вони **не забирають автоматично**:

> observation-constrained WSE-to-inundation reconstruction.

---

# Отже, де реально може бути твоя новизна

Після цього пошуку я б **не захищав** такі claims:

> ❌ новий принцип `WSE > DEM`

> ❌ перше використання connectivity

> ❌ перша terrain-based reconstruction

> ❌ перша temporal inundation reconstruction

> ❌ перше використання SWOT для Каховської повені.

А ось це вже виглядає значно цікавіше:

> **A daily, observation-constrained reconstruction of the Kakhovka outburst-flood inundation geometry using spatially distributed SWOT/gauge WSE, terrain connectivity, explicit pre-event water-state semantics, and propagated uncertainty.**

Особливо я бачу **три компоненти**, поєднання яких поки не знайшов у попередниках:

**SWOT WSE як forcing**, а не просто flood mask або validation hydraulic model;

**explicit `new inundation` vs `total water` ontology через multi-date baseline**;

**повний аналіз того, як S1/S2/terrain/ICESat-2/weak-label definitions дають різні відповіді на питання «скільки було затоплено».**

Тобто новизна, схоже, не:

\[
\boxed{\text{новий алгоритм flood-fill}}
\]

а:

\[
\boxed{
\text{нова observation-constrained experimental framework}
}
\]

для дуже рідкісного великого outburst flood.

І це, на мою думку, **краща й захищуваніша наукова позиція**.

Найбільшу увагу я б зараз приділив **Penton & Overton 2007, Hou et al. 2022, FLEXTH 2024 і Dale et al. 2026**. Саме вони визначають, де закінчується «відомий метод» і де може починатися твоя справжня новизна.
Так. Я звірив **твою фактичну реалізацію `p95_hand_daily_inundation.py`** у зафіксованому commit із методом Dale et al. Важливе уточнення: Zenodo показує, що їхній flood-fill реалізований у `depth_mapping.py` (19.7 kB), але внутрішній Python-файл лежить у ZIP і в цьому середовищі не розпаковується як текст. Тому це не буквальний diff «рядок Dale → рядок Nikoriak», а **точне зіставлення їхнього опублікованого алгоритму з твоїм реальним кодом**. Zenodo прямо підтверджує призначення `depth_mapping.py` як коду topographic flood fill. :chatgpt-content-reference{index="0"}

## Ключова знахідка

Твій `connected_ceiling` і flood-fill Dale **математично роблять майже одну й ту саму базову операцію**.

Dale:

```text
WSE
 ↓
DTM < WSE ?
 ↓
так
 ↓
чи можна дійти до клітини від seed через сусідні
низькі клітини?
 ↓
так
 ↓
FLOODED
```

У статті це сформульовано буквально: вони починають із seed, послідовно додають сусідні клітини нижче target WSE і продовжують, доки нових клітин більше немає. Connectivity потрібна, щоб простий elevation threshold не затоплював ізольовані западини. :chatgpt-content-reference{index="1"}

У тебе:

```python
cand = base & (L["dem"] < w)

lab, n = ndimage.label(
    cand,
    structure=np.ones((3, 3), bool)
)

keep = np.zeros(n + 1, bool)
keep[np.unique(lab[cand & L["seed"]])] = True

return keep[lab], w
```

По суті:

```text
DEM < WSE
     ↓
усі 8-connected компоненти
     ↓
залишити лише ті,
що торкаються seed
```

### Це дві реалізації тієї самої математичної ідеї

Dale йде **від seed назовні**.

Ти спочатку знаходиш **усі компоненти**, а потім питаєш, які з них містять seed.

Для однакової маски допустимих клітин це еквівалентно:

\[
P =
\operatorname{Connected}_{S}
\{x:z(x)<H(x)\}.
\]

Саме так твій аудит і записав центральний оператор. :chatgpt-content-reference{index="2"}

---

## Але далі ваші моделі сильно розходяться

| Компонент | Dale et al. | Твоя `p95` |
|---|---|---|
| Звідки береться WSE | Camera flood boundary + terrestrial lidar | SWOT WSE nodes + Kherson gauge |
| WSE у просторі | Один майже горизонтальний WSE для локальної depression | Просторово змінне поле WSE |
| Просторовий масштаб | приблизно 500 × 250 м | великий коридор нижнього Дніпра |
| Terrain | 0.5 м lidar DTM | 20 м seamless DEM |
| Seed | локальна спостережена flood area / lowest observed point | pre-event optical water network |
| Connectivity | iterative flood-fill | 8-connected component labeling |
| Depth | `WSE − DTM` | `WSE − DEM` |
| Час | кожні 30 хв, коли є camera image | daily 26.05–10.07 |
| Між спостереженнями | camera observations | temporal interpolation SWOT nodes |
| Baseline | немає твоєї конструкції | multi-day pre-event baseline |
| New flood | не центральна величина | `potential AND NOT baseline` |
| Total/potential water | flood extent | окрема quantity |
| Volume | не центральний результат | `Σ depth × pixel area` |
| MC uncertainty | не повний MC у цій роботі | окремий `p95e` |
| Cross-sensor comparison | cameras vs HEC-RAS | S1/S2/ICESat/ML/terrain |

Оце вже принципово.

---

# 1. Найсильніша відмінність — WSE

Dale спочатку бачить flood boundary камерою.

З lidar вони витягують elevations краю води й беруть `WSE90` / `WSE95`. Потім припускають майже плоску поверхню води. :chatgpt-content-reference{index="3"}

У них це приблизно:

\[
H(x,y)=126.01\ m
\]

для всього маленького локального басейну.

І для їхнього severe event це навіть підтримується HEC-RAS: після з'єднання двох flood patches різниця модельного WSE між sites була лише близько **0.5 см**. :chatgpt-content-reference{index="4"}

Ти такого на 100+ км Дніпра зробити не можеш.

Тому у тебе значно складніше:

```text
SWOT node 1 ─ 9.8 m
SWOT node 2 ─ 8.5 m
SWOT node 3 ─ 7.4 m
...
Kherson ───── 5.x m
```

і для кожної клітини формується:

\[
H(x,y,t).
\]

Тобто це вже не звичайний bathtub із однією відміткою.

Це **spatially distributed observation-constrained water surface**.

Оце важлива методологічна відмінність.

---

# 2. Твій WSE engine набагато складніший

У твоєму коді кожна клітина отримує median до п'яти найближчих SWOT nodes в межах 3 км.

Якщо їх немає — використовується nearest node.

Крім того:

```text
>15 km from node + downstream condition
               ↓
Kherson gauge cap
```

А кожен SWOT node ще й інтерполюється в часі.

Тобто твоя модель:

\[
H=H(x,y,t)
\]

тоді як Dale переважно має для конкретного site/time:

\[
H=H(t).
\]

Це вже серйозна відмінність.

---

# 3. Твій `baseline` — того у Dale фактично немає

Це, на мою думку, ще важливіше для твоєї новизни.

Dale питає:

> «Де вода при WSE = 126.01 м?»

Ти питаєш два різні питання.

Спочатку:

\[
P_t =
\text{усе, що модель дозволяє бути водою сьогодні}.
\]

А потім:

\[
B =
\bigcup P_{pre}
+
\text{observed pre-event water}.
\]

І:

\[
N_t=P_t\setminus B.
\]

Тобто:

```text
Potential/total water
         ↓
мінус
pre-event normal water state
         ↓
NEW INUNDATION
```

Саме тому в тебе `790 km² total` і `247 km² new` — різні quantities, а не дві версії однієї площі. Аудит це прямо відзначає. :chatgpt-content-reference{index="5"}

У Dale такого ontology problem практично немає, бо вони досліджують локальне pluvial flooding.

---

# 4. У тебе є ще один рівень, якого Dale не має: normally wet

У твоєму коді:

```python
normally_wet |= potential(pre_event_day)[0]

normally_wet &= ~L["pre"]

baseline = L["pre"] | normally_wet
```

Тобто ти кажеш:

> Тут Sentinel міг не бачити відкриту воду, але terrain + normal WSE показують, що це нормальний wet state.

Наприклад:

```text
очерет
низька заплава
мілководдя
```

Тоді коли S1 після прориву стає dark-water, ти не автоматично кажеш:

> «це нове затоплення».

Можливо, це:

> **збільшення depth над normally-wet terrain.**

Це вже зовсім не Dale.

І це одна з тих речей, які аудит вважає сильними у твоїй роботі: розділення різних семантик води. :chatgpt-content-reference{index="6"}

---

# 5. Depth у вас абсолютно однаковий за принципом

Dale:

\[
D=H_{WSE}-z_{DTM}.
\] :chatgpt-content-reference{index="7"}


Ти:

```python
depth = np.where(
    pot,
    w - L["dem"],
    0
)
```

тобто:

\[
D(x,t)=H(x,t)-z_{DEM}(x).
\]

Тут ніякої новизни немає.

І не треба її шукати.

---

# 6. А ось ця частина Dale для тебе надзвичайно важлива

Вони отримали дуже сильний результат.

У їхньому flood-fill:

\[
WSE=125.99\,m
\]

→ одна площа.

Піднімаємо воду всього на:

\[
+0.02\,m.
\]

Отримуємо:

\[
126.01\,m.
\]

І flood area стрибає:

**+390%** для Site A  
і **+270%** для Site B. :chatgpt-content-reference{index="8"}

Чому?

Бо вода перетнула **spill point**:

```text
       бар'єр
         ▲
         │ 126.00
         │
~~~~~~~  │        depression
         │        __________
_________│_______/          \____
```

На 125.99:

```text
ліва частина wet
права dry
```

На 126.01:

```text
ліва + права CONNECTED
```

І площа вибухає.

---

# Це прямо стосується твоєї F01–F04 uncertainty

Ти можеш мати WSE error:

\[
\pm 5\,cm
\]

або DEM error:

\[
\pm0.5-1.5\,m.
\]

А результат не змінюється плавно:

```text
+5 cm WSE
≠
+5% area
```

Може бути:

```text
+5 cm
↓
перейшли spill threshold
↓
+100 km²
```

або майже нічого.

Саме тому Monte Carlo у твоїй роботі настільки важливий.

---

# 7. Ще сильніший результат Dale: DEM сам може пересунути connectivity threshold

Вони змінили спосіб interpolation DEM:

```text
TIN
→
IDW
```

і connectivity threshold змінився на **4 см**. :chatgpt-content-reference{index="9"}

Зверни увагу:

у них **0.5 м lidar DTM**.

І вже там 4 см DEM-processing difference вплинуло на момент з'єднання flood patches.

У тебе:

```text
20 m DEM
+
FABDEM
+
bathymetry
+
bias correction
+
zone seams
```

Тому питання:

> «як DEM uncertainty впливає на connectivity transitions?»

для твоєї моделі взагалі центральне.

Це дуже сильне незалежне обґрунтування, чому F02 і F06/F07 аудиту не можна просто відмахнути.

---

# 8. Dale сам називає це фактично bathtub model

І це важливо для правильного позиціонування твоєї моделі.

Вони прямо пишуть, що flood-fill припускає:

> zero flow resistance та instantaneous water propagation. :chatgpt-content-reference{index="10"}

Тобто модель знає:

```text
геометрія + рівень + connectivity
```

але не знає:

```text
швидкість
тертя
інерцію
час заповнення
час осушення
```

Це **точно те саме принципове обмеження**, яке має твій `connected_ceiling`.

Тому в manuscript дуже добре можна послатися на Dale:

> Similar to topographic flood-fill approaches, the reconstruction represents hydraulically admissible connectivity under the imposed water surface rather than dynamic flood-wave routing.

Це дуже сильне формулювання.

---

# 9. Але Dale знайшов ще одну річ, яку тобі треба серйозно врахувати

Їхня elevation-based model іноді сказала:

```text
CONNECTED
```

а дві реальні камери показали:

```text
DISCONNECTED
```

Чому?

Вони називають:

- unresolved microtopographic barriers;
- infiltration;
- stormwater infrastructure;
- drainage;
- pumping. :chatgpt-content-reference{index="11"}


Тобто:

\[
\text{DEM connectivity}
\neq
\text{necessarily hydraulic connectivity}.
\]

Це дуже важливо і для тебе.

У твоєму випадку причини інші:

```text
levees
embankments
roads
channels
vegetation
unresolved drainage
ponding
breach-created morphology
DEM errors
```

Тому твоє слово:

> `terrain-allowed`

насправді дуже правильне.

Краще, ніж:

> `physically flooded`.

---

# 10. Але твоя модель вже на один крок розумніша за простий Dale flood-fill

Бо ти не використовуєш один WSE на весь domain.

У Dale:

```text
126.01 m
────────────────────────────
```

У тебе приблизно:

```text
near dam       10 m
                 \
                  \
                   8 m
                    \
                     \
Kherson               5 m
```

Тобто ти враховуєш longitudinal/spatial WSE gradient через observations.

Це дуже суттєва адаптація для fluvial/outburst environment.

---

# 11. І тут я знайшов одну проблему вже у твоєму коді

У docstring написано:

> `connected_ceiling` — **recommended primary variant**.

А argparse зараз має:

```python
ap.add_argument(
    "--rule",
    default="hand_and_ceiling",
    choices=[
        "hand_and_ceiling",
        "ceiling_only",
        "connected_ceiling"
    ]
)
```

Тобто фактичний default:

```text
hand_and_ceiling
```

а документація всередині того самого файла каже:

```text
recommended primary = connected_ceiling
```

Це треба виправити.

Не обов'язково змінювати default — але **один canonical primary method має бути визначений однозначно**.

---

# Що після Dale я вважаю справжньою новизною твоєї моделі

Не це:

> ❌ `DEM < WSE`

Не це:

> ❌ connected flood-fill

Не це:

> ❌ `depth = WSE - DEM`

Не це:

> ❌ time series flood maps.

Все це вже існує.

Твоя потенційно сильна конструкція тепер виглядає так:

\[
\boxed{
\text{distributed satellite WSE}
\rightarrow
\text{terrain-connected daily reconstruction}
\rightarrow
\text{explicit pre-event state}
\rightarrow
\text{new vs total water}
\rightarrow
\text{uncertainty propagation}
\rightarrow
\text{cross-sensor disagreement}
}
\]

І особливо:

**SWOT observations є forcing для extent reconstruction**, а не просто validation hydraulic model.

Це вже значно цікавіше.

---

## Що я б додав у твій pipeline прямо після прочитання Dale

Не нову нейромережу.

А **spill-threshold sensitivity analysis**.

Для кожного важливого дня:

```text
WSE - 0.20 m
WSE - 0.10
WSE - 0.05
WSE
WSE + 0.05
WSE + 0.10
WSE + 0.20
```

і рахувати:

\[
A(H).
\]

Потім:

\[
\frac{\Delta A}{\Delta H}.
\]

Ти побачиш місця типу:

```text
WSE

     AREA
      │                █████████
      │                █
      │                █
      │      ██████████
      │      █
      │███████
      └──────────────────── WSE
             ↑
        spill threshold
```

І тоді Monte Carlo стане фізично зрозумілим:

> чому саме ±5–10 см у конкретному місці може дати десятки км² uncertainty.

Dale et al. показали такий ефект емпірично — всього **2 см WSE дали 270–390% зміни площі** в їхньому локальному basin. :chatgpt-content-reference{index="12"}

Це, я думаю, може стати **одним із найсильніших нових diagnostic plots у твоїй статті**.

І головний висновок після порівняння такий: **Dale не “вбиває” твою новизну. Він забирає новизну самого flood-fill алгоритму, але водночас дає дуже сильне літературне обґрунтування твоєму підходу й показує, чому uncertainty DEM/WSE/connectivity у твоїй набагато більшій системі треба досліджувати особливо ретельно.**

Так. І я знайшов саме той напрям літератури, який тобі потрібен.

Але важливий момент: у наукових статтях це зазвичай **не називають “додати гравітаційний потенціал \(gz\)”**. Для DEM/flood-fill задач використовують інші терміни:

> **spill elevation**, **depression hierarchy**, **fill–spill–merge**, **hydraulic connectivity**, **hydraulic head**, **path-based attenuation**.

Тобто твоя ідея має хорошу наукову основу, просто її треба правильно назвати.

Найближчі до того, що ми обговорювали, такі роботи:

| Робота | Що дає тобі |
|---|---|
| **Barnes et al., 2014 — Priority-Flood** | алгоритм, де depressions заповнюються відповідно до висоти рельєфу; базова логіка “вода піднімається до найнижчого виходу” |
| **Barnes et al., 2020 — Depression hierarchy** | прямо будує ієрархію западин та їхніх **spill points / spill elevations** |
| **Barnes et al., 2021 — Fill–Spill–Merge** | вода наповнює depression → доходить до spill elevation → переливається в сусідню → depressions зливаються |
| **Kasmalkar et al., 2024 — Flow-Tub** | bathtub + connectivity + **path-based attenuation**, тобто ще й наближення втрат/тертя вздовж шляху |
| **Dale et al., 2026** | WSE + DEM + connected flood-fill; показує нелінійні переходи через spill thresholds |

### 1. Найважливіша для твоєї ідеї — Fill–Spill–Merge

**Barnes, Callaghan & Wickert (2021), Earth Surface Dynamics**

Вони буквально описують те, про що ми говорили:

> коли depression заповнюється, поверхня води доходить до **spill elevation**, після чого вода переливається в сусідню depression; коли обидві заповнені, вони об'єднуються. :chatgpt-content-reference{index="0"}

Це вже не просто:

\[
z_{DEM}<H
\]

а структура:

```text
depression A
   ↓ fills
spill point
   ↓ overtops
depression B
   ↓
merge
```

Саме це ти хотів додати у свою модель.

Стаття:
**Barnes, R., Callaghan, K. L., & Wickert, A. D. (2021). Computing water flow through complex landscapes – Part 3: Fill–Spill–Merge: flow routing in depression hierarchies. Earth Surface Dynamics, 9, 105–121. DOI 10.5194/esurf-9-105-2021.** :chatgpt-content-reference{index="1"}

---

## 2. А перед нею є стаття, яка будує саме “карту потенційних бар'єрів”

**Barnes et al. (2020), Earth Surface Dynamics — Part 2: Finding hierarchies in depressions.**

Це ще ближче до моєї попередньої пропозиції з:

\[
z_{\text{spill}}(x).
\]

Вони будують **depression hierarchy**, яка зберігає топологію вкладених западин та місця, де вони з'єднуються/переливаються. Така структура може використовуватися для routing water та для dynamic models. :chatgpt-content-reference{index="2"}

Тобто замість твого:

```text
connected / not connected
```

можна мати:

```text
connected only after WSE crosses 5.42 m
connected to next depression after 5.67 m
connected to floodplain after 6.11 m
```

Оце вже набагато фізичніше.

---

## 3. Priority-Flood — фундаментальний алгоритм

**Barnes, Lehman & Mulla (2014), Computers & Geosciences.**

Priority-Flood розглядає DEM depressions як області, оточені вищим рельєфом, і заповнює їх так, як це робила б рідина на непроникній поверхні. Алгоритм працює через priority queue, починаючи від найнижчих доступних висот. :chatgpt-content-reference{index="3"}

Це важливо для тебе не як готова flood model, а як математична база для:

\[
\text{minimum elevation barrier between source and cell}.
\]

І є відкритий reference implementation. :chatgpt-content-reference{index="4"}

---

# 4. Дуже цікава робота саме для “трохи фізики без HEC-RAS”

**Kasmalkar et al. (2024), Flow-Tub**

Це, можливо, найближчий напрям до того, що я б радив тобі як наступну версію.

Вони почали зі звичайного bathtub:

\[
d=H-z.
\]

А потім додали дві речі:

1. **hydraulic connectivity** — вода повинна мати шлях від source;
2. **path-based attenuation** — рівень води зменшується вздовж шляху, щоб приблизно врахувати friction та обмежену тривалість flood event. :chatgpt-content-reference{index="5"}

Тобто вже:

```text
source WSE
    ↓
connected path
    ↓
attenuation along path
    ↓
local effective WSE
    ↓
effective WSE > DEM ?
```

Вони прямо пишуть, що стандартний bathtub переоцінює затоплення, бо не враховує connectivity і friction/time effects. :chatgpt-content-reference{index="6"}

Є навіть Python-код на Zenodo. :chatgpt-content-reference{index="7"}

---

# 5. Dale 2026 прямо показує spill threshold у реальній повені

Ти вже приніс цю статтю, але тепер вона стає ще важливішою.

Вони роблять:

\[
WSE + DTM + connectivity
\]

і прямо показують, що flood connectivity контролюється **spill-point thresholds**. :chatgpt-content-reference{index="8"}

Найсильніший приклад:

\[
125.99\rightarrow126.01\ \mathrm{m}
\]

тобто всього **+2 см WSE**, а flood extent збільшується на сотні відсотків через перехід топографічного порогу. :chatgpt-content-reference{index="9"}

Саме це демонструє, чому твоя модель не повинна просто дивитися на площу `DEM < WSE`, а має досліджувати **critical connectivity thresholds**.

---

# Тобто що я б робив у твоїй моделі

Не вводив би:

\[
\Phi=mgz
\]

як окремий raster.

Це нічого нового математично не дасть, бо \(g\) майже константа.

Я б ввів **spill-potential layer**:

\[
H_{\text{spill}}(x)
\]

— мінімальний рівень води, при якому клітина \(x\) стає доступною з річки.

Тоді:

\[
\boxed{
x\ \text{can flood at }t
\iff
H_t(x)\ge H_{\text{spill}}(x)
}
\]

і додатково:

\[
z(x)<H_t(x).
\]

Тобто твоя нова логіка:

```text
SWOT/gauge WSE
       ↓
spatial H(x,y,t)
       ↓
compare with spill-elevation surface
       ↓
which depressions become connected?
       ↓
DEM < WSE
       ↓
inundation
```

Це вже дуже добре спирається на Barnes 2020/2021.

---

## А ще сильніша версія

Після цього можна додати Flow-Tub-подібне attenuation:

\[
H_{\text{eff}}(x,t)
=
H_{\text{source}}(t)-L(x),
\]

де \(L(x)\) — втрати вздовж шляху.

Тоді:

\[
H_{\text{eff}}(x,t)>H_{\text{spill}}(x).
\]

Це ще не Saint-Venant і не HEC-RAS, але вже набагато фізичніше за простий bathtub.

---

### Для твоєї статті я б узяв чотири ключові посилання

**Barnes et al., 2014** — Priority-Flood. :chatgpt-content-reference{index="10"}  
**Barnes et al., 2020** — depression hierarchy. :chatgpt-content-reference{index="11"}  
**Barnes et al., 2021** — Fill–Spill–Merge. :chatgpt-content-reference{index="12"}  
**Kasmalkar et al., 2024** — Flow-Tub, connectivity + attenuation. :chatgpt-content-reference{index="13"}

І вже **Dale et al., 2026** як прямий сучасний flood example. :chatgpt-content-reference{index="14"}

Тобто відповідь: **так, і є ціла наукова гілка, яка фактично описує саме те, що ти інтуїтивно назвав “додати гравітаційний потенціал”. У правильній термінології це spill elevation + depression hierarchy + hydraulic connectivity, а наступний рівень — path-based attenuation.**

Так. Якщо відкинути весь складний код, **твоя основна модель дуже проста за ідеєю**.

Уяви, що весь нижній Дніпро після прориву — це величезна нерівна поверхня, а ти кожного дня намагаєшся відповісти:

> **де рівень води був вищий за поверхню землі і куди ця вода фізично могла бути зв’язана з уже відомою водою?**

Саме це і є ядро твоєї моделі. В аудиті воно формально записане як порівняння скоригованого DEM із полем рівня води та перевірка зв’язності. :chatgpt-content-reference{index="0"}

### Уяви ванну з дуже нерівним дном

DEM — це дно ванни:

```text
        пагорб
          /\
____     /  \____
    \___/        \____
```

А `WSE` — це висота поверхні води:

```text
--------------------  ← WSE
        /\
____   /  \____
    \_/        \____
```

Де земля нижче водної поверхні:

```text
DEM < WSE
```

там **теоретично може бути вода**.

Але ти не кажеш:

> «усе, що нижче WSE, затоплене».

Ти робиш ще одну важливу перевірку:

> **чи має ця низька ділянка зв’язок із уже відомою водою?**

Тому ізольована яма далеко від Дніпра не повинна автоматично ставати повінню.

---

## Звідки береться рівень води

Ти не задаєш одну горизонтальну лінію на весь Дніпро.

Ти маєш спостереження рівня води — насамперед SWOT і gauge — у різних місцях уздовж системи.

Умовно:

```text
дамба                           Херсон

SWOT      SWOT       SWOT        gauge
10.2 m    8.7 m      6.3 m       5.1 m
  ●---------●----------●-----------●
```

Між цими точками модель створює **просторове поле WSE**.

Тобто в кожному місці вона має приблизне:

```text
H(x, y, day)
```

— якою могла бути висота водної поверхні цього дня.

У коді використовується до кількох сусідніх WSE-вузлів, інтерполяція в часі та gauge як додаткове обмеження. Аудит підтвердив цю загальну конструкцію, хоча знайшов проблеми у fallback, extrapolation і uncertainty. :chatgpt-content-reference{index="1"}

---

## Потім модель дивиться на кожен піксель

Для конкретної клітини вона фактично питає:

```text
Яка тут висота землі?
        ↓
наприклад 6.4 м

Який тут розрахований рівень води?
        ↓
наприклад 7.1 м
```

Отже:

```text
7.1 - 6.4 = 0.7 м
```

Ця клітина може бути під водою приблизно на 0.7 м.

Якщо ж:

```text
земля = 7.5 м
WSE   = 7.1 м
```

то:

```text
7.5 > 7.1
```

і модель каже:

> сюди вода за цією геометрією не доходить.

---

# Але є ще connectivity

Це дуже важлива частина твоєї моделі.

Уяви дві западини:

```text
Дніпро ~~~~~~~~        окрема яма
~~~~~~~~~~~~~~~           ___
~~~~~~~~~~~~~~~          \___/
```

Обидві можуть лежати нижче розрахованого WSE.

Але друга яма може не мати фізичного шляху до річки.

Тому твій алгоритм шукає **connected components**.

У спрощеному вигляді:

```text
нижче WSE
   +
з'єднано з водним seed
   =
potential water
```

Це сильніше, ніж просто:

```text
DEM < WSE
```

бо ти додаєш елементарну гідрологічну логіку.

---

# А що таке seed?

Seed — це місце, де ми вже маємо підставу вважати, що вода існує.

Наприклад, передподієва вода.

Уяви:

```text
████████     ← відома вода Дніпра
   │
   │
░░░░░░░░     ← низька заплава
```

Якщо низька заплава з'єднана з цією водою і лежить нижче WSE:

```text
→ модель дозволяє її затоплення.
```

Саме тому модель називається по суті **геометричною реконструкцією зі зв'язністю**, а не просто threshold DEM. :chatgpt-content-reference{index="2"}

---

# Потім ти робиш дуже важливу річ — визначаєш baseline

І ось тут твоя робота цікавіша за просту flood map.

Ти кажеш:

> «Не вся вода після 6 червня є новою повінню».

Бо до події вже були:

- русло;
- затоки;
- постійна вода;
- normally-wet areas;
- частина очеретяних/заплавних територій.

Тому ти формуєш baseline:

```text
B = те, що вже було водою
    або модельно wet до події
```

А далі для кожного дня:

```text
Potential water today
        MINUS
Baseline water
        =
New inundation
```

У самому аудиті це записано як:

\[
N_t=P_t\setminus B
\]

:chatgpt-content-reference{index="3"}

Це одна з найважливіших ідей твоєї роботи.

---

# Тому в тебе є ДВІ різні площі

Це треба дуже добре відчути.

### Total water

Усе, що цього дня модель вважає водою:

```text
старе русло
+
старі водойми
+
нова повінь
=
TOTAL WATER
```

### New inundation

Тільки територія, яка не входила в baseline:

```text
TOTAL WATER
-
BASELINE
=
NEW FLOOD
```

Через це:

```text
790 км² total
```

і

```text
247 км² new
```

не суперечать одне одному.

І також тому не можна просто зробити:

```text
790 - площа води 5 червня
```

і очікувати точно 247, бо твій baseline — не одна карта одного дня, а об'єднання кількох передподієвих джерел/станів. Аудит це окремо підкреслює. :chatgpt-content-reference{index="4"}

---

# І ти можеш отримати не лише площу

Якщо ми знаємо:

```text
WSE = 7.1 м
DEM = 6.4 м
```

то:

```text
depth = 0.7 м
```

Отже по всій території можна отримати:

```text
карта затоплення
↓
карта глибин
↓
площа
↓
приблизний об'єм води
```

Тобто модель перетворює **точкові/смугові спостереження висоти води** на **просторову геометрію можливої водної поверхні**.

---

# А де тут Monte Carlo?

До цього ми поводилися так, ніби все знаємо точно.

А насправді:

```text
SWOT має похибку
DEM має похибку
gauge має похибку
vertical datum має похибку
інтерполяція має похибку
```

Тому модель має не один варіант світу:

```text
DEM точно такий
WSE точно такий
```

а багато:

```text
Світ 1 → площа 242 км²
Світ 2 → площа 249 км²
Світ 3 → площа 245 км²
...
```

Після цього можна сказати:

```text
median ≈ 247 км²
```

і дати interval.

Оце роль Monte Carlo.

Тобто Monte Carlo **не створює flood map**.

Він питає:

> «Наскільки зміниться наша flood map, якщо наші вхідні величини трохи помилкові?»

Саме тут аудит і знайшов головні проблеми F01–F04.

---

# А де в цій історії Sentinel-1, Sentinel-2 і U-Net?

Оце важливо: це вже **не саме ядро геометричної моделі**.

У тебе фактично є кілька паралельних ліній доказів.

Спрощено:

```text
                    FLOOD EVENT
                         │
          ┌──────────────┼───────────────┐
          ↓              ↓               ↓
       TERRAIN        SATELLITE         ML
     reconstruction   observations      analysis
          │              │               │
      DEM + WSE        S1/S2           U-Net/RF
          │              │               │
          └──────────────┼───────────────┘
                         ↓
                 compare disagreement
```

І це дуже важливо.

U-Net **не визначає твою головну геометричну flood reconstruction**.

Він допомагає дослідити:

> чи може ML відтворити event-flood signal за weak labels;

> як змінюється результат, якщо змінити ontology labels;

> де SAR, terrain і ML не погоджуються.

Саме тому рецензент вважає одним із сильних аспектів роботи розділення різних понять води, а не змішування їх в одну «істинну flood map». :chatgpt-content-reference{index="5"}

---

# Тепер найголовніше: чого твоя модель НЕ робить

Вона **не запускає воду від дамби вперед у часі**.

Тобто вона не рахує:

```text
швидкість води →
турбулентність →
імпульс →
тертя →
поширення хвилі →
час приходу →
витрату
```

Вона не розв'язує Saint-Venant / shallow-water equations.

Тому це не:

> «Я змоделював, як хвиля пішла від Каховської ГЕС».

А:

> **«Для кожного дня я відновив геометрично допустимий стан затоплення, використовуючи спостережуваний/інтерпольований рівень води, рельєф і умову зв'язності».**

Аудит прямо зазначає, що модель не розв'язує conservation of mass/momentum, не визначає propagation time і не моделює затримання води в ізольованих улоговинах. :chatgpt-content-reference{index="6"}

---

# Якщо сказати одним реченням

**Твоя модель бере спостереження рівня води, “натягує” з них водну поверхню над DEM і знаходить усі низькі території, куди ця вода геометрично могла дійти через зв'язний водний шлях; потім відділяє стару воду від нового затоплення і через Monte Carlo оцінює, наскільки невпевнений цей результат.**

А вже Sentinel-1/Sentinel-2, ICESat-2, RF і U-Net потрібні, щоб **перевіряти, пояснювати й розкладати розбіжності між різними способами бачити цю повінь**.

Це, на мою думку, і є найпростіше правильне пояснення твоєї моделі.
