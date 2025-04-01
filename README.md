# Datasets
![Датасеты, использованные при обучении CRISPR-BERT](/images/datasets_info.bmp)
*Datasets used for CRISPR-BERT training* (*[Luo et al., 2024](https://www.sciencedirect.com/science/article/pii/S0010482524000167)*)

## K562 and HEK293t
The off-target profile dataset contained two different cell types: 293-related cell lines (18 sgRNAs) and K562 t (12 sgRNAs) [6, 22, 24,25,26,27, 44]. For all 30 sgRNAs, we obtained ~ 160,000 possible loci across the whole genome using bowtie2 [51], with a maximum of six nucleotide mismatches. The whole dataset was highly unbalanced, and nearly 1/250 loci was identified as an off-target site (one mismatch, 4; two mismatches, 31; three mismatches, 121; four mismatches, 236; five mismatches, 174; six mismatches, 75) with various whole genome off-target detection techniques [22,23,24,25,26,27] (Additional files 6 and 7). For the classification model, the off-target sites are labeled as “1” and the others are labeled as “0”. For the regression model, the off-target sites are labeled and normalized with the targeting cleavage frequency (indel frequency) detected by different off-target detection assays. (*Source: [G. Chuai et al. (2018) DeepCRISPR: optimized CRISPR guide RNA design by deep learning](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-018-1459-4)*)

Sample of K562 data (20319 rows):
| target | potential_off_target | is_off_target |
|----------|----------|----------|
| AAATGAGAAGAAGAGGCACAGGG | GCATGAGAAGAAGAGACATAGCC | 0 |
| AAATGAGAAGAAGAGGCACAGGG | GAAGAAGAAGAAGAGGAAGAGGA | 0 |
| CCTGCCTCCGCTCTACTCACTGG | CCTGGCTCCTCTCTCCTCACTGG | 1 |

*Dataset source: [S.W. Cho et al. (2014) Analysis of off-target effects of CRISPR/Cas-derived RNA-guided endonucleases and nickases](https://pmc.ncbi.nlm.nih.gov/articles/PMC3875854/)*

## Table_S8_machine_learning_input

26248 rows
The genomic sequence extending from 22 bases 5′ of the beginning of the PAM to 1 base 3′ of the end of the PAM

1. *key* - уникальное значение
2. *perfect_match_sgRNA* - гидРНК, полностью комплементарная таргетному участку ДНК (perfectly matched sgRNA, PMsgRNA)
3. *gene* - название гена
4. *sgRNA_sequence* - гидРНК с одним несовпадением к таргетному участку (mismatched sgRNA, MMsgRNA)
5. *mismatch_position* - позиция несовпадения 
6. *new_pairing* - содержание несовпадения. Например, *rA:dC*	значит, что нуклеотид G (комплементарный C) в РНК заменен на A.
7. *K562* - были ли проведены эксперименты на клетках линии K562
8. *Jurkat* - были ли проведены эксперименты на клетках линии Jurkat
9. *mean_relative_gamma* - активность MMsgRNA относительно PMsgRNA

*Dataset source: [M. Jost et al. (2020) Titrating gene expression using libraries of systematically attenuated CRISPR guide RNAs](https://pmc.ncbi.nlm.nih.gov/articles/PMC7065968/)*

### Описание целевой величины mean relative gamma
**Gamma (γ)** — это мера влияния конкретной sgRNA на рост клеток в пуле (популяции). Определяется по следующей формуле:

<img src="./images/gamma_formula.png" style="height: 80px;">

𝑁 initial,sgRNA, 𝑁 final,sgRNA — количество клеток с определенной sgRNA в начале и конце эксперимента.

Аналогично для non-targeting sgRNA (контрольные sgRNA, которые не действуют на целевой ген).

Таким образом, 𝛾 отражает, насколько клетка с конкретной sgRNA растет лучше (𝛾 > 0) или хуже (𝛾 < 0), чем клетки с контрольными (non-targeting) sgRNA. Чем больше отрицательное 𝛾, тем сильнее негативный эффект sgRNA на рост клеток.

**Relative gamma** — это нормализованное значение γ, показывающее активность sgRNA с несовпадениями (mis-matched sgRNA) относительно идеально совпадающей sgRNA (perfect match sgRNA):

<img src="./images/relative_gamma_formula.png" style="height: 70px;">

sgRNA_variant — это sgRNA с несовпадением (мисматчем).

sgRNA_perfect — идеально совпадающая sgRNA (полное совпадение с целевой последовательностью).

- Значение 1 означает, что sgRNA с несовпадением действует так же, как идеально совпадающая sgRNA.
- Значение 0 означает, что sgRNA с несовпадением не имеет влияния на рост (то есть её активность отсутствует или равна контрольной).

Показатель **Mean Relative Gamma** получается путём усреднения relative gamma по результатам нескольких экспериментов (в статье использовали клетки K562 и Jurkat):

<img src="./images/mean_relative_gamma_formula.png" style="height: 50px;">

Это усреднение делает метрику более устойчивой и менее чувствительной к шуму.

| Диапазон значений | Интерпретация |
|----------|----------|
| <0 | Несовпадающая sgRNA оказывает противоположный эффект на рост клеток, чем идеально совпадающая (например, вместо ингибирования, стимулирует рост). |
| 0 | Полностью неактивная sgRNA с несовпадением (не влияет на рост) |
| 0,1-0,9 | Частичная активность sgRNA (умеренное подавление экспрессии гена и влияния на рост клеток). |
| ~1 | 	Несовпадающая sgRNA почти так же эффективна, как идеально совпадающая. |
| >1 | Несовпадающая sgRNA неожиданно более эффективна в подавлении экспрессии гена, чем идеально совпадающая ИЛИ perfectRNA усилила рост клеток, а mismatched усилила его еще больше |

## 4 cell lines

Made from the datasets used for the study of sgRNA on-target efficacy prediction. Includes data for four cell lines: *hct116, hek293t, hela, hl60*

Sample (16749 rows):
| Chromosome | Start | End | Strand | sgRNA | Normalized efficacy | cell_line |
|----------|----------|----------|----------|----------|----------|----------|
| chr17 | 33469132 | 33469154 | - | CTTGCTCGCGCAGGACGAGGCGG | 0.16401994504229 | hct116 |
| chr1 | 12316394 | 12316416 | - | ACTCTCCATGCTCCTGGCCATGG | 0.00942528735632599 | hela |

## Data augmented dataset for on-target prediction
This dataset was generated from ~15,000 sgRNAs across 1071 genes with known knockout efficacies in a data augmentation manner (see the [“On-target data sources”](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-018-1459-4#Sec24) section).

Previous studies have shown that PAM-distal region has a high tolerance for sequence mismatches (Kim et al., 2016; Kleinstiver et al., 2016). To be specific, gRNAs with two mismatches in the first two positions from the 5’ end has little influence on cleavage efficiency (Doench et al., 2014; Doench et al., 2016). Inspired by these studies, Chuai et al. applied a data augmentation procedure by changing each gRNA into a new one with two mismatches in the PAM distal region (Chuai et al., 2018). Consequently, a 23-nt gRNA sequence can be expanded into 16 gRNAs with identical cleavage efficacy. The augmented dataset was generated from  15,000 gRNAs with known on-target cleavage efficacy. By adopting this data augmentation strategy, they obtained 180,512 non-redundant gRNAs. Each observation in the data contains a 23-nt gRNA sequence and its corresponding cleavage efficiency (*Source: [A. F. Abbasi et al. (2025) Transitioning from wet lab to artificial intelligence: a systematic review of AI predictors in CRISPR](https://pmc.ncbi.nlm.nih.gov/articles/PMC11796103/)*)

Sample (180513 rows):

| sgRNA | Efficacy | 
|----------|----------|
| AAACCGCCTCCAAGTCGCCGAGG | 1 |
| AAGTGGCTTCCGTGGTGGCCGGG | 0 |

*Dataset source: [G. Chuai et al. (2018) DeepCRISPR: optimized CRISPR guide RNA design by deep learning](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-018-1459-4)*

# Embeddings

## Попробовать
mRNABERT, RNABERT, DNABERT, DNABERT-2, RNAGPT, HyenaDNA, IsoFormer 

## SeQuant
[GitHub](https://github.com/GenerativeMolMachines/SeQuant)

-----------------------------------------------------------------------

## Описание проекта

Этот проект представляет собой пайплайн для обработки данных. Основная цель пайплайна — загрузка, валидация, трансформация данных и их сохранение в базу данных SQLite. Процесс включает следующие шаги:

1. Скачивание исходного файла данных.
2. Преобразование текста в DataFrame.
3. Загрузка сырых данных в базу данных.
4. Валидация и добавление новых признаков.
5. Сохранение очищенных данных в отдельную таблицу БД.

Работа выполнялась как часть проекта "Созданием инструмента для оценки эффективности направляющих РНК в CRISPR-Cas системах" (более подробное описание проекта и его ценность можно посмотреть в презентации). В дальнейшем эти данные будут использованы для обучения алгоритмов МО и/или нейросетей для предсказания таргетной величины. 

## Создание новых признаков
В датасет добавлены пять новых признаков, три из них - это закодированные с помощью различных схем кодирования пары РНК-ДНК (длины N): 
1. *encoded_or* - матрица 4xN. Сначала ДНК и РНК one-hot кодируются по четырем каналам (ATGC), затем между ними выполняется операция ИЛИ. Подробнее в [статье](https://pmc.ncbi.nlm.nih.gov/articles/PMC6129261/)
2. *encoded_stacked* - матрица 8xN. Сначала ДНК и РНК one-hot кодируются по четырем каналам (ATGC), затем они "стекаются". Подробнее в [статье](https://academic.oup.com/bioinformatics/article/37/16/2299/6143578)
3. *encoded_7channels* - матрица 7xN. Позволяет работать с лишними или недостающими нуклеотидами в РНК (относительно таргетного участка ДНК), а также учитывает различные функциональные участки РНК (PAM или собственно направляющая РНК). Подробнее в [статье](https://www.sciencedirect.com/science/article/pii/S2001037022000137)
4. *gc_content* (гуанин-цитозиновый состав, ГЦ-состав) - доля гуанина (G) и цитозина (C) среди всех нуклеотидов последовательности. ГЦ-состав направляющей РНК влияет на ее эффективность, оптимальным считается значение 40-60% ([V. Konstantakos et al. 2022, CRISPR–Cas9 gRNA efficiency prediction: an overview of predictive tools and the role of deep learning ](https://academic.oup.com/nar/article/50/7/3616/6555429))
5. *pam* (protospacer adjacent motif; мотив, смежный с протоспейсером) - короткая последовательность ДНК (обычно длиной 2-6 пар оснований), она следует за таргетным участком ДНК и служит "сигналом" к разрезу. Данные в нашем датасете собраны для энзима Sp.Cas9, а ему соответствует PAM вида 5'-NGG-3', где N-любой нуклеотид. [Подробнее](https://www.addgene.org/guides/crispr/)

## EDA
Исследовательский анализ данных представлен в файле EDA.ipynb

## Метрики качества данных
### Содержание данных

**Валидность** - соответствие многочисленным атрибутам, связанных с элементом данных: тип, точность, формат, диапазоны допустимых значений и так далее.

1. *key* - текст, только уникальные значения
1. *perfect match sgRNA* - текст
2. *gene* - текст
3. *sgRNA sequence*, *genome input*, *sgRNA input* - текстовые, содержат последовательности только из букв ATGC
4. *mismatch position* - отрицательное целое число
5. *new pairing* - текст
6. *K562*, *Jurkat* - логический тип
7. *mean relative gamma* - число с плавающей точкой

### Согласованность

**Уникальность** - ни один объект не существует в наборе данных более одного раза. Наличие дублей может приводить к несогласованности и противоречиям вследствие отсутствия единой версии правды.

**Согласованность** - соответствие данных друг другу и их логическая непротиворечивость.

1. Значения *mismatch position* и *new pairing* должны соответствовать реальному различию нуклеотидов между *genome input* и *sgRNA input*

## Разработка БД
Для хранения данных была выбрана СУБД SQLite. Данные из txt-файла и из датафрейма переносятся в базу посредством скрипта, использующего встроенный модуль sqlite3.
### Структура таблицы clean_data
| Название поля         | Тип данных | Ограничения                           |
|-----------------------|------------|---------------------------------------|
| `key`                 | TEXT       | PRIMARY KEY                           |
| `perfect_match_sgRNA` | TEXT       | NOT NULL                              |
| `gene`                | TEXT       |                                       |
| `sgRNA_sequence`      | TEXT       |                                       |
| `mismatch_position`   | INTEGER    | NOT NULL, CHECK(mismatch_position < 0)|
| `new_pairing`         | TEXT       |                                       |
| `K562`                | INTEGER    | NOT NULL, CHECK(K562 IN (0,1))        |
| `Jurkat`              | INTEGER    | NOT NULL, CHECK(Jurkat IN (0,1))      |
| `mean_relative_gamma` | REAL       | NOT NULL                              |
| `genome_input`        | TEXT       |                                       |
| `sgRNA_input`         | TEXT       |                                       |
| `encoded_or`          | TEXT       |                                       |
| `encoded_stacked`     | TEXT       |                                       |
| `encoded_7channels`   | TEXT       |                                       |
| `gc_content`          | REAL       |                                       |
| `pam`                 | TEXT       |                                       |

## Дашборд
Интерактивный дашборд формируется с помощью билиотеки Streamlit (см. п. Запуск дашборда)

### Источники
1. Критерии качества данных / Loginom https://loginom.ru/blog/data-quality-criteria
2. Оценка качества данных / Яндекс Образование https://education.yandex.ru/handbook/data-analysis/article/ocenka-kachestva-dannyh

## Запуск

### Предварительные требования

- **Python 3.7** или выше.
- **Доступ в интернет** для скачивания данных.

### Установка

1. **Клонируйте репозиторий** (если применимо):

    ```bash
    git clone https://github.com/ваш_репозиторий.git
    cd ваш_репозиторий
    ```

2. **Создайте и активируйте виртуальное окружение** (рекомендуется):

    ```bash
    python -m venv venv
    source venv/bin/activate  # Для Linux/macOS
    venv\Scripts\activate     # Для Windows
    ```

3. **Установите необходимые зависимости**:

    ```bash
    pip install -r requirements.txt
    ```

### Запуск пайплайна

**Использование стандартных значений**
```bash
python main.py
```
**Использование пользовательских значений**
```bash
python main.py --url "https://example.com/data.txt" --local_filename "data.txt" --db_name "my_database.db"
```

#### Описание параметров
+ `--url`:
  + *Описание*: Ссылка на исходный файл данных, который необходимо скачать.
  + *Тип*: str
  + *По умолчанию*: https://raw.githubusercontent.com/ew314/sgRNA_seq2seq/main/relative_activity_predictor/data/Table_S8_machine_learning_input.txt

+ `--local_filename`:
  + *Описание*: Имя локального файла, в который будут сохранены скачанные данные.
  + *Тип*: str
  + *По умолчанию*: Table_S8_machine_learning_input.txt

+ `--db_name`:
  + *Описание*: Имя базы данных SQLite, в которую будут загружены и сохранены данные.
  + *Тип*: str
  + *По умолчанию*: crispr_sgRNA.db

### Запуск дашборда
**Использование стандартных значений**

```bash
streamlit run streamlit_app.py
```
**Использование пользовательских значений**
```bash
streamlit run streamlit_app.py -- --db_name=new_db.db
```

#### Описание параметров
+ `--db_name`:
  + *Описание*: Имя базы данных SQLite, из которой будут выгружены данные.
  + *Тип*: str
  + *По умолчанию*: crispr_sgRNA.db