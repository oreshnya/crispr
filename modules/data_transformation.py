import requests
import json
import time

import numpy as np
import pandas as pd
from sklearn.metrics import (mean_squared_error, mean_absolute_error, r2_score,
                             confusion_matrix, precision_score, recall_score, f1_score, fbeta_score)

def validate_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет базовую валидацию/очистку данных по критериям:
      1. 'key' — текст, уникальный
      2. 'sgRNA_sequence', 'genome_input', 'sgRNA_input' — содержат ТОЛЬКО символы A, T, G, C
      3. 'mismatch_position' — отрицательное целое (не 0)
      4. 'K562', 'Jurkat' — изначально True/False, но для БД должны быть 0/1
      5. 'mean_relative_gamma' — float

    Возвращает DataFrame, потенциально отфильтрованный/исправленный.
    """

    def to_zero_one(val):
        """
        Преобразует различные формы True/False или 0/1 в целые 0 или 1.
        Если значение не распознано, возвращает np.nan.
        """
        # Проверка на bool
        if isinstance(val, bool):
            return 1 if val else 0
        
        # Проверка на int
        if isinstance(val, int):
            # Считаем, что любое ненулевое число — 1, 
            # или вы можете разрешить только 0 и 1
            return 1 if val == 1 else 0
        
        # Проверка на строки 'True'/'False'/'0'/'1'
        if isinstance(val, str):
            lower_val = val.strip().lower()
            if lower_val in ['true', '1']:
                return 1
            if lower_val in ['false', '0']:
                return 0
        
        # Если ничего не подошло
        return np.nan

    original_count = len(df)  # Исходное количество строк

    # 1. Проверка уникальности 'key'
    if df['key'].nunique() != len(df):
        duplicates_count = len(df) - df['key'].nunique()
        print(f"[WARNING] Обнаружено {duplicates_count} дубликатов в 'key'. Удаляем дубликаты...")
        df = df.drop_duplicates(subset='key')

    # 2. Проверка, что в sgRNA sequence / genome_input / sgRNA_input только ATGC
    #    Вместо регулярок — поксимвольная проверка, чтобы исключить все невидимые символы и т.д.
    def only_acgt(seq) -> bool:
        if not isinstance(seq, str):
            return False
        return all(ch in "ATGC" for ch in seq)

    seq_columns = ["sgRNA_sequence", "genome_input", "sgRNA_input"]
    for col in seq_columns:
        mask_valid = df[col].apply(only_acgt)
        invalid_count = (~mask_valid).sum()
        if invalid_count > 0:
            print(f"[WARNING] В столбце '{col}' обнаружено {invalid_count} некорректных значений. Удаляем...")
            df = df[mask_valid]

    # 3. Проверка 'mismatch position' – отрицательное целое (не 0)
    #    Сначала пытаемся привести к int, потом проверяем < 0
    def mismatch_ok(x) -> bool:
        try:
            xi = int(x)  # возможно x= -17.0
            return xi < 0  # строго меньше 0
        except:
            return False

    mask_mismatch = df["mismatch_position"].apply(mismatch_ok)
    invalid_mismatch = (~mask_mismatch).sum()
    if invalid_mismatch > 0:
        print(f"[WARNING] 'mismatch_position' содержит {invalid_mismatch} некорректных значений. Удаляем...")
        df = df[mask_mismatch]

    # Приводим к int (после фильтрации)
    df["mismatch_position"] = df["mismatch_position"].astype(int)

    # 4. Проверка K562, Jurkat
    for col in ["K562", "Jurkat"]:
        df[col] = df[col].apply(to_zero_one)  # Превратим всё в {0,1} или np.nan

        # Удаляем строки, где остался np.nan (значит, значение нераспознано)
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            print(f"[WARNING] В столбце '{col}' обнаружено {nan_count} нераспознанных значений. Удаляем...")
            df = df[df[col].notna()]
        
        # Теперь это int-флаг
        df[col] = df[col].astype(int)

    # 5. Проверка 'mean relative gamma' (float)
    def is_float(x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    mask_gamma = df["mean_relative_gamma"].apply(is_float)
    invalid_gamma_count = (~mask_gamma).sum()
    if invalid_gamma_count > 0:
        print(f"[WARNING] 'mean_relative_gamma' содержит {invalid_gamma_count} некорректных значений. Удаляем...")
        df = df[mask_gamma]
    df["mean_relative_gamma"] = df["mean_relative_gamma"].astype(float)

    # Итоговое количество строк
    final_count = len(df)
    removed_rows = original_count - final_count
    print(f"\nВалидация завершена. Исходных строк было: {original_count}, осталось: {final_count}.")
    print(f"Удалено строк: {removed_rows}.\n")

    return df


def one_hot_atgc(sequence: str) -> np.ndarray:
    bases = "ATGC"
    encoding = np.zeros((4, len(sequence)), dtype=int)
    for i, base in enumerate(sequence):
        if base in bases:
            encoding[bases.index(base), i] = 1
    return encoding


def encode_or(dna: str, rna: str) -> np.ndarray:
    """
    Кодирует ДНК и РНК последовательности в матрицу one-hot и выполняет операцию ИЛИ между ними.

    :param dna: ДНК последовательность
    :param rna: РНК последовательность
    :return: 4-строчная матрица после операции ИЛИ
    """
    # Проверяем, что длины последовательностей совпадают
    if len(dna) != len(rna):
        raise ValueError("Длина ДНК и РНК последовательностей должна совпадать.")

    # Кодируем ДНК и РНК
    dna_encoded = one_hot_atgc(dna)
    rna_encoded = one_hot_atgc(rna)

    # Выполняем побитовую операцию ИЛИ
    combined_encoding = np.logical_or(dna_encoded, rna_encoded).astype(int)

    return combined_encoding


def encode_stacked(dna: str, rna: str) -> np.ndarray:
    """
    Кодирует ДНК и РНК последовательности в матрицу one-hot и стекает их в одну матрицу.

    :param dna: ДНК последовательность
    :param rna: РНК последовательность
    :return: 8-строчная матрица после стека кодировок
    """
    # Проверяем, что длины последовательностей совпадают
    if len(dna) != len(rna):
        raise ValueError("Длина ДНК и РНК последовательностей должна совпадать.")

    # Кодируем ДНК и РНК
    dna_encoded = one_hot_atgc(dna)
    rna_encoded = one_hot_atgc(rna)

    # Стек матриц
    stacked_encoding = np.vstack((dna_encoded, rna_encoded))

    return stacked_encoding


def encode_7channels(dna: str, rna: str, pam_location: str = "last", pam_length: int = 3) -> np.ndarray:
    """
    Кодирует ДНК и РНК последовательности с использованием 7 каналов: A, T, G, C, R, D, F.

    :param dna: ДНК последовательность
    :param rna: РНК последовательность
    :param pam_location: Расположение PAM ("first" или "last")
    :param pam_length: Длина PAM-области
    :return: Матрица 7 x N
    """
    if len(dna) != len(rna):
        raise ValueError("Длина ДНК и РНК последовательностей должна совпадать.")

    # Кодируем последовательности
    dna_encoded = one_hot_atgc(dna)
    rna_encoded = one_hot_atgc(rna)

    # ATGC каналы
    atgc_channels = np.zeros_like(dna_encoded)
    for i in range(4):
        match = (dna_encoded[i] == rna_encoded[i]) & (dna_encoded[i] == 1)
        mismatch = (dna_encoded[i] != rna_encoded[i]) & ((dna_encoded[i] == 1) | (rna_encoded[i] == 1))
        atgc_channels[i] = mismatch.astype(int) - match.astype(int)

    # R и D каналы
    r_channel = np.zeros(len(dna), dtype=int)
    d_channel = np.zeros(len(dna), dtype=int)
    priority = {"A": 0, "T": 1, "G": 2, "C": 3}
    for i, (d, r) in enumerate(zip(dna, rna)):
        if d != r:
            if priority[d] < priority[r]:
                d_channel[i] = 1
            else:
                r_channel[i] = 1

    # F канал (обозначает PAM-область)
    f_channel = np.zeros(len(dna), dtype=int)
    if pam_location == "last":
        f_channel[-pam_length:] = 1
    elif pam_location == "first":
        f_channel[:pam_length] = 1

    # Комбинируем все каналы
    combined_matrix = np.vstack((atgc_channels, r_channel, d_channel, f_channel))

    return combined_matrix


def count_mismatches(seq1: str, seq2: str) -> int:
    """
    Считает количество несовпадений (миссматчей) между двумя последовательностями нуклеотидов.
    
    :param seq1: Первая последовательность (строка).
    :param seq2: Вторая последовательность (строка).
    :return: Количество несовпадений (int).
    """
    if len(seq1) != len(seq2):
        raise ValueError("Последовательности должны быть одинаковой длины.")
    
    mismatches = sum(1 for a, b in zip(seq1, seq2) if a != b)
    return mismatches


def calc_gc_content(seq: str) -> float:
    if not seq:  # на случай, если строка пустая
        return 0.0
    seq = seq.upper()  # Для надёжности приводим к верхнему регистру
    gc_count = sum(ch in ('G', 'C') for ch in seq)
    return gc_count / len(seq)


def add_new_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет столбцы с новыми признаками:
      1. encode_or -> encoded_or
      2. encode_stacked -> encoded_stacked
      3. encode_7channels -> encoded_7channels
      4. gc_content -> gc_content
      5. pam -> pam (последние 3 символа reversed)

    Для "encoded_*" признаков 
    кодируем и сохраняем как "сплющенную" (flatten) numpy-матрицу.
    """

    # ---------------------
    # 1) encoded_or
    # ---------------------
    df['encoded_or'] = df.apply(
        lambda row: encode_or(
            row['genome_input'],  # DNA
            row['sgRNA_input']    # RNA
        ).flatten(), 
        axis=1
    )

    # ---------------------
    # 2) encoded_stacked
    # ---------------------
    df['encoded_stacked'] = df.apply(
        lambda row: encode_stacked(
            row['genome_input'],
            row['sgRNA_input']
        ).flatten(),
        axis=1
    )

    # ---------------------
    # 3) encoded_7channels
    # ---------------------
    df['encoded_7channels'] = df.apply(
        lambda row: encode_7channels(
            row['genome_input'],
            row['sgRNA_input'],
            pam_location="last",
            pam_length=3
        ).flatten(),
        axis=1
    )

    # ---------------------
    # 4) gc_content
    # ---------------------
    # Считаем долю нуклеотидов G и C в "sgRNA_input"
    df['gc_content'] = df['sgRNA_input'].apply(calc_gc_content)

    # ---------------------
    # 5) pam
    # ---------------------
    # Берём последние 3 символа из "sgRNA_input" и разворачиваем их
    # Пример: если последовательность заканчивается "GGT", 
    # то pam будет "TGG".

    df['pam'] = df['sgRNA_input'].apply(reverse_last_3)

    return df
    


def generate_embeddings(df, sequence_column, polymer_type='DNA', encoding_strategy='aptamer', batch_size=80):
    """
    Генерирует эмбеддинги для последовательностей из указанного столбца DataFrame.
    Сохраняет индексы для последующего объединения.

    :param df: Исходный DataFrame с последовательностями.
    :param sequence_column: Название столбца с последовательностями.
    :param polymer_type: Тип полимера ('DNA' для последовательностей ATGC).
    :param encoding_strategy: Стратегия кодирования ('aptamer').
    :param batch_size: Количество последовательностей в одном запросе.
    :return: DataFrame с эмбеддингами, индексами, совпадающими с исходным DataFrame.
    """
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    # Исходные последовательности + сохранение их индексов
    sequences = df[sequence_column].tolist()
    indices = df.index.tolist()  # Сохраняем индексы для правильного присоединения

    # Разбиваем на батчи по 80 последовательностей
    several_id_lists = np.array_split(np.asarray(sequences), int(len(sequences) / batch_size) + 1)
    index_splits = np.array_split(np.asarray(indices), int(len(sequences) / batch_size) + 1)

    embeddings = {}

    for i, (batch, index_batch) in enumerate(zip(several_id_lists, index_splits)):
        print(f"Обрабатываем батч {i + 1} из {len(several_id_lists)}...")
        params = {
            'sequences': ', '.join(list(batch)),
            'polymer_type': polymer_type,
            'encoding_strategy': encoding_strategy,
            'skip_unprocessable': 'true',
        }
        try:
            # Отправляем запрос
            response = requests.post('https://ai-chemistry.itmo.ru/api/encode_sequence', params=params, headers=headers)
            response.raise_for_status()

            # Преобразуем ответ в JSON
            data = json.loads(response.content)
            
            # Записываем эмбеддинги в словарь с сохранением индексов
            for seq, idx in zip(batch, index_batch):
                if seq in data:
                    embeddings[idx] = data[seq]
                else:
                    embeddings[idx] = None  # Если последовательность не обработалась, ставим None

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при обработке батча {i + 1}: {e}")

        # Задержка для предотвращения перегрузки API
        time.sleep(4)

    # Преобразуем словарь в DataFrame
    embeddings_df = pd.DataFrame.from_dict(embeddings, orient='index')

    # Добавляем имена столбцов
    embeddings_df.columns = [f"feature_{i}" for i in range(embeddings_df.shape[1])]

    # Убеждаемся, что индексы соответствуют исходному DataFrame
    embeddings_df = embeddings_df.reindex(df.index)

    return embeddings_df


def evaluate_classification_model(model, X_test, y_test, beta=2, threshold=0.5):
    """
    Оценивает Keras модель и выводит результаты: accuracy, confusion matrix, precision, recall, F1-score и F-beta score.

    :param model: Keras Model
    :param X_test: Тестовые данные (массив или список массивов для многовходных моделей)
    :param y_test: Истинные значения
    :param beta: Значение beta для F-beta score (по умолчанию 2)
    :param threshold: Порог классификации (по умолчанию 0.5)
    :return: Tuple (results_df, annotated_cm)
    """
    # Проверка размерностей данных
    if isinstance(X_test, list):
        for i, x in enumerate(X_test):
            if len(x) != len(y_test):
                raise ValueError(
                    f"Размер входного массива X_test[{i}] ({len(x)}) не совпадает с размером y_test ({len(y_test)})."
                )
    else:
        if len(X_test) != len(y_test):
            raise ValueError(
                f"Размер входного массива X_test ({len(X_test)}) не совпадает с размером y_test ({len(y_test)})."
            )

    # Оцениваем модель
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=1)
    print(f"Test Loss: {test_loss:.5f}")
    print(f"Test Accuracy: {test_accuracy:.5f}")

    # Предсказания вероятностей
    y_pred_proba = model.predict(X_test)

    # Применяем порог классификации
    y_pred = (y_pred_proba > threshold).astype(int).flatten()

    # Вычисление метрик
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    f_beta = fbeta_score(y_test, y_pred, beta=beta, zero_division=0)

    print("\nMetrics:")
    print(f"Precision: {precision:.5f}")
    print(f"Recall: {recall:.5f}")
    print(f"F1-score: {f1:.5f}")
    print(f"F-beta ({beta}): {f_beta:.5f}")
    print(f"Threshold used: {threshold}")

    # Создаем DataFrame с результатами
    results_df = pd.DataFrame({
        'y_test': y_test,
        'y_pred_proba': y_pred_proba.flatten(),  # Добавляем вероятности
        'y_pred': y_pred,
    })
    results_df['prediction_is_true'] = results_df.apply(
        lambda row: 'Yes' if row['y_test'] == row['y_pred'] else 'No',
        axis=1
    )

    # Выводим первые строки DataFrame
    print("\nResults DataFrame (first 5 rows):")
    print(results_df.head())

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    cm_df = pd.DataFrame(
        cm, 
        index=['Actual No (0)', 'Actual Yes (1)'], 
        columns=['Predicted No (0)', 'Predicted Yes (1)']
    )

    # Аннотированная confusion matrix
    annotations = [
        ['TN (True Negative)', 'FP (False Positive)'],
        ['FN (False Negative)', 'TP (True Positive)']
    ]
    annotated_cm = cm_df.astype(str)
    for i, row in enumerate(cm_df.index):
        for j, col in enumerate(cm_df.columns):
            annotated_cm.loc[row, col] = f"{annotations[i][j]}: {cm[i, j]}"

    # Выводим annotated confusion matrix
    print("\nAnnotated Confusion Matrix:")
    print(annotated_cm)

    return results_df, annotated_cm


def evaluate_regression_model(model, X_test, y_test):
    """
    Оценивает Keras модель для задачи регрессии.

    :param model: Keras Model
    :param X_test: Тестовые данные
    :param y_test: Истинные значения
    :return: results_df (с предсказаниями), метрики (MSE, MAE, R²)
    """
    # Оцениваем модель
    test_loss, test_mae = model.evaluate(X_test, y_test, verbose=1)
    print(f"Test Loss (MSE): {test_loss:.5f}")
    print(f"Test MAE: {test_mae:.5f}")

    # Предсказания модели
    y_pred = model.predict(X_test).flatten()

    # Вычисляем метрики
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\nRegression Metrics:")
    print(f"Mean Squared Error (MSE): {mse:.5f}")
    print(f"Mean Absolute Error (MAE): {mae:.5f}")
    print(f"R² Score: {r2:.5f}")

    # Создаем DataFrame с результатами
    results_df = pd.DataFrame({
        'y_test': y_test,
        'y_pred': y_pred
    })

    return results_df, mse, mae, r2