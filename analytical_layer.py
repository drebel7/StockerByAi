"""
ANALYTICAL LAYER
================
Warstwa analityczna do obliczania wskaźników technicznych.
Modułowa, wydajna, z obsługą batch processing.
"""

import mysql.connector
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import math

class TechnicalIndicators:
    """
    Klasa do obliczania wskaźników technicznych.
    Wymagane dane: OHLCV z raw_price_data
    Wyniki są zapisywane w technical_indicators tabela
    
    Warstwa jest projektowana do:
    - Batch processing (duże ilości danych)
    - Minimalnych operacji SQL
    - Efektywności pamięciowej
    """
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Łączenie z bazą danych."""
        if not self.connection:
            try:
                self.connection = mysql.connector.connect(
                    host=self.db_config.get('host', 'localhost'),
                    user=self.db_config.get('user', 'root'),
                    password=self.db_config.get('password', ''),
                    database='stock_analysis_db',
                    charset='utf8mb4'
                )
                self.cursor = self.connection.cursor(dictionary=True)
                print("✅ Połączono z bazą danych (Indicators Layer)")
            except mysql.connector.Error as err:
                print(f"❌ Błąd połączenia: {err}")
        return True
    
    # =============================================
    # WSKAŹNIKI TECHNICZNE
    # =============================================
    
    def calculate_sma(
        self,
        close_prices: List[float],
        period: int
    ) -> Optional[float]:
        """
        Simple Moving Average.
        SMA(n) = Σ(close) / n
        
        Args:
            close_prices: Lista cen zamknięcia (max length)
            period: Okres (10, 20, 50, 200)
        """
        if len(close_prices) < period:
            return None
        
        # Optymalizacja - sumowanie w pętli jest szybkie dla małych okresów
        window = close_prices[-period:]
        sma = sum(window) / period
        return round(sma, 6)
    
    def calculate_obv(
        self,
        current_volume: int,
        price_change_direction: str,  # 'up', 'down', 'flat'
        previous_obv: float
    ) -> float:
        """
        On Balance Volume.
        OBV(n) = OBV(n-1) + volume * direction_factor
        
        Args:
            current_volume: Wolumen bieżący dzień
            price_change_direction: 'up' jeśli close > open, 'down' jeśli close < open, 'flat' inaczej
            previous_obv: Poprzedni OBV
        """
        if price_change_direction == 'up':
            new_obv = previous_obv + current_volume
        elif price_change_direction == 'down':
            new_obv = previous_obv - current_volume
        else:
            new_obv = previous_obv  # Flat - brak zmiany
        
        return round(new_obv, 2)
    
    def calculate_atr(
        self,
        high: float,
        low: float,
        prev_close: float,
        current_date: date,
        atr_period: int = 30
    ) -> Optional[float]:
        """
        Average True Range.
        TR = max(|H-L|, |H-PrevClose|, |L-PrevClose|)
        ATR(n) = Σ(TR) / n
        
        Wymaga historyczne dane dla obliczenia TR.
        Dla nowego rekordu potrzebujemy: high, low, prev_close
        """
        # Oblicz True Range (wymaga historycznych danych)
        tr_range = max(
            abs(high - low),
            abs(high - prev_close) if prev_close else 0,
            abs(low - prev_close) if prev_close else 0
        )
        
        # Jeśli to pierwszy dzień po zresetowaniu ATR
        if not self._last_tr_sum or current_date != self._last_tr_date:
            # Resetuj dla nowego okresu (np. nowy rok)
            tr_sum = tr_range
        else:
            tr_sum = self._last_tr_sum + tr_range
        
        # Aktualizuj śledzenie daty
        self._last_tr_sum = tr_sum
        self._last_tr_date = current_date
        
        return round(tr_sum / atr_period, 6)
    
    def calculate_rsi(
        self,
        close_prices: List[float],
        period: int = 14
    ) -> Optional[float]:
        """
        Relative Strength Index.
        RSI = 100 - (100 / (1 + RS))
        RS = AvgGain / AvgLoss
        
        To implementacja uproszczona - pełna wersja wymaga historycznych danych.
        """
        if len(close_prices) < period:
            return None
        
        # Oblicz zmiany
        changes = [close_prices[i] - close_prices[i-1] for i in range(1, len(close_prices))]
        gains = max(0.0, c) for c in changes[-period:]
        losses = abs(min(0.0, c)) for c in changes[-period:]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    def calculate_drift(
        self,
        close_prices: List[float],
        period: int
    ) -> Optional[float]:
        """
        Drift (ADR - Average Daily Return).
        ADR = Σ(|close[i] - close[i-1]|) / n / 100
        Wyrażone jako %
        """
        if len(close_prices) < period:
            return None
        
        total_abs_return = sum(
            abs(close_prices[i] - close_prices[i-1]) 
            for i in range(period, len(close_prices))
        )
        adr = (total_abs_return / period) * 100
        return round(adr, 4)
    
    def calculate_turnover(
        self,
        volume: int,
        close_price: float
    ) -> float:
        """
        Turnover = Volume × Price
        Wyrażony w walucie (np. PLN/USD millions).
        """
        return round(volume * close_price, 2)
    
    def calculate_relative_strength(
        self,
        stock_return: float,
        benchmark_close: float,
        benchmark_period_start: date
    ) -> Optional[float]:
        """
        Relative Strength vs Indeks/Sektor.
        RS = (Stock_Return / Benchmark_Return)
        
        Args:
            stock_return: Zwrot spółki w % za okres
            benchmark_close: Cena zamknięcia indeksu/sektora
            benchmark_period_start: Data początku okresu
        """
        # W pełnej implementacji - potrzebne historyczne dane indeksu
        # To jest placeholder - realna implementacja wymaga:
        # 1. TABELA: benchmarks (indeksy, sektory)
        # 2. Zapis historii cen indeksów
        
        if benchmark_close == 0:
            return None
        
        # Przykładowa logika - w rzeczywistości potrzebujemy:
        # historical_index_data = fetch_benchmark_history(
        #     benchmark_code, period_start, date.today()
        # )
        # index_return = calculate_return(benchmark_close, historical_index_data)
        
        return None  # Placeholder
    
    def calculate_avg_volume(
        self,
        volumes: List[int],
        period: int
    ) -> Optional[int]:
        """
        Average Volume over N periods.
        """
        if len(volumes) < period:
            return None
        
        avg_vol = sum(volumes[-period:]) / period
        return round(avg_vol)
    
    # =============================================
    # BATCH CALCULATION METHODS
    # =============================================
    
    def calculate_all_indicators(
        self,
        records: List[Dict],
        tickers_cache: Dict[str, Tuple[int, str]] = None
    ) -> int:
        """
        Oblicza wszystkie wskaźniki techniczne dla zestawu rekordów.
        
        Args:
            records: Lista rekordów z raw_price_data (OHLCV)
            tickers_cache: Cache tickerów (opcjonalne)
            
        Returns:
            Liczba zaktualizowanych rekordów w technical_indicators
        """
        if not self.connection or not self.cursor:
            print("❌ Brak połączenia z bazą")
            return 0
        
        inserted = 0
        cursor = self.cursor
        
        # Grupa rekordów po ticker_id i exchange_code dla batch processing
        grouped_records: Dict[Tuple[int, str], List[Dict]] = {}
        
        for record in records:
            key = (record['ticker_id'], record['exchange_code'])
            if key not in grouped_records:
                grouped_records[key] = []
            grouped_records[key].append(record)
        
        # Przetwórz każdy ticker
        for (ticker_id, exchange_code), tick_records in grouped_records.items():n
                tick_records.sort(key=lambda x: x['date'])
                self._process_ticker_indicators(ticker_id, exchange_code, tick_records)
                inserted += len(tick_records)
        
        return inserted
    
    def _process_ticker_indicators(
        self,
        ticker_id: int,
        exchange_code: str,
        tick_records: List[Dict]
    ) -> None:
        """
        Oblicza wskaźniki dla pojedynczego tickera.
        """
        if not tick_records:
            return
        
        # Pobierz historyczne dane z bazy (dla ATR, RSI)
        historical_data = self._get_historical_for_atr(ticker_id, exchange_code)
        
        # Inicjalizacja
        current_close = tick_records[0]['close']
        prev_close = tick_records[0].get('open', current_close)
        prices_history = [current_close]
        volumes_history = []
        obv_sum = 0
        atr_sum = 0
        dr_sum = 0
        
        # Oblicz dla każdego dnia
        for record in tick_records:
            date_str = str(record['date'])
            close = record['close']
            open_price = record['open']
            high = record['high']
            low = record['low']
            volume = record['volume']
            
            # Zbierz historyczne dane
            prices_history.append(close)
            volumes_history.append(volume)
            
            # SMA
            sma_10 = self.calculate_sma(prices_history, 10)
            sma_20 = self.calculate_sma(prices_history, 20)
            sma_50 = self.calculate_sma(prices_history, 50)
            sma_200 = self.calculate_sma(prices_history, 200)
            
            # OBV
            direction = 'up' if close > open_price else ('down' if close < open_price else 'flat')
            obv_sum += (volume if direction == 'up' else -volume) if direction != 'flat' else 0
            obv_100 = round(obv_sum, 2)
            
            # ADR
            daily_return = abs(close - prev_close)
            dr_sum += daily_return
            adr_30 = (dr_sum / 30) * 100 if len(prices_history) >= 30 else None
            
            # ATR (wymaga historycznych danych z bazy)
            atr_30 = self._calculate_atr_with_history(
                high, low, prev_close, date_str,
                historical_data.get('tr_data', []),
                30
            )
            
            # Turnover
            turnover = volume * close
            avg_turnover_50 = (turnover / 50) if len(volumes_history) >= 50 else None
            avg_volume_50 = self.calculate_avg_volume(volumes_history, 50)
            
            # Zapis do bazy
            self._upsert_indicator_record(
                ticker_id,
                exchange_code,
                date_str,
                sma_10, sma_20, sma_50, sma_200,
                obv_100, adr_30, atr_30,
                avg_volume_50, avg_turnover_50
            )
            
            # Aktualizuj stan
            prev_close = close
        
    def _get_historical_for_atr(
        self,
        ticker_id: int,
        exchange_code: str
    ) -> Dict:
        """
        Pobiera historyczne dane TR z bazy do obliczenia ATR.
        Wymaga tabeli historycznego zakresu (TR dla każdego dnia).
        
        To jest uproszczenie - w pełnej implementacji:
        1. Tabela: historical_tr_data
        2. Zapis TR po każdym dniu handlowym
        """
        # Placeholder - realna implementacja wymaga:
        # SQL query fetch historycznych danych TR
        return {'tr_data': []}
    
    def _calculate_atr_with_history(
        self,
        high: float,
        low: float,
        prev_close: float,
        date_str: str,
        historical_tr_data: List[Tuple[date, float]],
        period: int = 30
    ) -> Optional[float]:
        """
        Oblicza ATR z historycznymi danymi TR.
        
        TR(n) = max(|H-L|, |H-PrevClose|, |L-PrevClose|)
        ATR(n) = Σ(TR) / n
        """
        if not historical_tr_data:
            # Jeśli brak danych historycznych - oblicz tylko obecny TR
            tr_current = max(
                abs(high - low),
                abs(high - prev_close),
                abs(low - prev_close)
            )
            atr = tr_current  # Pierwszy dzień
        else:
            # Pobierz historyczne TR
            current_date = date.fromisoformat(date_str)
            filtered_tr = [
                (d, t) for d, t in historical_tr_data 
                if d <= current_date
            ]
            
            if len(filtered_tr) < period:
                return None
            
            # Sumuj TR za ostatni okres
            tr_sum = sum(t for _, t in filtered_tr[-period:])
            atr = tr_sum / period
        
        return round(atr, 6)
    
    def _upsert_indicator_record(
        self,
        ticker_id: int,
        exchange_code: str,
        date_str: str,
        sma_10: Optional[float],
        sma_20: Optional[float],
        sma_50: Optional[float],
        sma_200: Optional[float],
        obv_100: Optional[float],
        adr_30: Optional[float],
        atr_30: Optional[float],
        avg_volume_50: Optional[int],
        avg_turnover_50: Optional[float]
    ) -> None:
        """
        Upsert rekordu wskaźników do bazy.
        """
        query = """
            INSERT INTO technical_indicators 
                (ticker_id, exchange_code, date,
                 sma_10, sma_20, sma_50, sma_200,
                 obv_100, adr_30, atr_30,
                 avg_volume_50, avg_turnover_50)
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                sma_10 = VALUES(sma_10),
                sma_20 = VALUES(sma_20),
                sma_50 = VALUES(sma_50),
                sma_200 = VALUES(sma_200),
                obv_100 = VALUES(obv_100),
                adr_30 = VALUES(adr_30),
                atr_30 = VALUES(atr_30),
                avg_volume_50 = VALUES(avg_volume_50),
                avg_turnover_50 = VALUES(avg_turnover_50)
        """
        
        values = (
            ticker_id,
            exchange_code,
            date_str,
            sma_10, sma_20, sma_50, sma_200,
            obv_100, adr_30, atr_30,
            avg_volume_50, avg_turnover_50
        )
        
        cursor.execute(query, values)
    
    # =============================================
    # METODY POMOCNICZE
    # =============================================
    
    def process_batch(
        self,
        batch_size: int = 10000
    ) -> Dict[str, Any]:
        """
        Przetwarzanie dużych partii danych.
        Podziela dane na partie i przetwarza każdy oddzielnie.
        
        Args:
            batch_size: Rozmiar partii (domyślnie 10000)
            
        Returns:
            Statystyki przetwarzania
        """
        total_processed = 0
        batches = 0
        
        # Pobierz dane z bazy do przetworzenia
        cursor = self.cursor
        end_date = date.today()
        start_offset = 30  # Domyślnie 30 dni danych
        
        while True:
            # Pobierz partię rekordów
            offset_query = """
                SELECT id, ticker_id, exchange_code, date,
                       open, high, low, close, volume
                FROM raw_price_data
                WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                  AND date <= CURDATE()
                ORDER BY ticker_id, date DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(offset_query, (batch_size, total_processed))
            batch_records = cursor.fetchall()
            
            if not batch_records:
                break
            
            # Przetwórz partię
            self.calculate_all_indicators(batch_records)
            total_processed += len(batch_records)
            batches += 1
        
        return {
            'batches': batches,
            'records_processed': total_processed
        }
    
    def calculate_for_date_range(
        self,
        start_date: date,
        end_date: date = None
    ) -> int:
        """
        Oblicza wskaźniki dla określonego zakresu dat.
        """
        if end_date is None:
            end_date = date.today()
        
        query = """
            SELECT id, ticker_id, exchange_code, date,
                   open, high, low, close, volume
            FROM raw_price_data
            WHERE date BETWEEN %s AND %s
              AND date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY ticker_id, date DESC
        """
        
        cursor = self.cursor
        cursor.execute(query, (str(start_date), str(end_date)))
        records = cursor.fetchall()
        
        if not records:
            print(f"   ⚠️ Brak danych w zakresie {start_date} - {end_date}")
            return 0
        
        self.calculate_all_indicators(records)
        return len(records)
    
    def close_connection(self):
        """Zamykanie połączenia z bazą."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


# =============================================
# KLASA: IndicatorsCalculator - Orkiestrator wskaźników
# =============================================

class IndicatorsCalculator:
    """
    Klasa orkiestrująca obliczenia wskaźników.
    Obsługuje planowanie, logowanie, retry logic.
    """
    
    def __init__(self, db_config: Dict[str, str]):
        self.indicators = TechnicalIndicators(db_config)
        self.start_date = None
        self.end_date = date.today()
    
    def set_date_range(self, start: date):
        """
        Ustawia zakres dat.
        """
        self.start_date = start
    
    def calculate_indicators(
        self,
        years_back: int = 4
    ) -> Dict[str, Any]:
        """
        Główna metoda obliczania wskaźników.
        
        Returns:
            Statystyki obliczeń
        """
        try:
            if not self.indicators.connect():
                return {}
            
            # Ustaw zakres dat
            current_date = date.today()
            start_date = current_date - timedelta(days=years_back * 365)
            
            print(f"\n📊 Obliczanie wskaźników: {start_date} → {current_date}")
            print("=" * 40)
            
            # Oblicz wskaźniki
            self.indicators.set_date_range(start_date)
            records_calculated = self.indicators.calculate_for_date_range(start_date)
            
            return {
                'records_calculated': records_calculated,
                'start_date': start_date,
                'end_date': current_date
            }
            
        except Exception as e:
            print(f"❌ Błąd podczas obliczania wskaźników: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def calculate_specific_ticker(
        self,
        ticker_id: int,
        exchange_code: str,
        start_date: date = None
    ) -> Optional[Dict]:
        """
        Oblicza wskaźniki dla konkretnego tickera.
        
        Args:
            ticker_id: ID tickera w tabeli tickers
            exchange_code: Kod giełdy
            start_date: Data początkowa (opcjonalne)
            
        Returns:
            Obliczone wskaźniki lub None
        """
        if not self.indicators.connect():
            return None
        
        cursor = self.indicators.cursor
        query = """
            SELECT id, date, open, high, low, close, volume
            FROM raw_price_data
            WHERE ticker_id = %s AND exchange_code = %s
              AND date >= COALESCE(%s, CURDATE() - INTERVAL 30 DAY)
            ORDER BY date DESC
        """
        
        start_str = str(start_date) if start_date else None
        cursor.execute(query, (ticker_id, exchange_code, start_str))
        records = cursor.fetchall()
        
        if not records:
            return None
        
        self.indicators._process_ticker_indicators(ticker_id, exchange_code, records)
        
        # Zwróć obliczone wskaźniki
        last_indicator = cursor.execute("""
            SELECT * FROM technical_indicators
            WHERE ticker_id = %s AND exchange_code = %s
            ORDER BY date DESC LIMIT 1
        """, (ticker_id, exchange_code)).fetchone()
        
        return {
            'records': records,
            'last_indicator': last_indicator
        }
    
    def close_connection(self):
        """Zamykanie połączenia z bazą."""
        self.indicators.close_connection()


# =============================================
# GŁÓWNA FUNKCJA: Obliczanie wskaźników
# =============================================

def calculate_technical_indicators(
    db_host: str = 'localhost',
    years_back: int = 4,
    **db_config
) -> Dict[str, Any]:
    """
    Główna funkcja do obliczania wskaźników technicznych.
    
    Args:
        db_host: Host bazy danych (default: localhost)
        years_back: Ile lat danych przetwarzać
        **db_config: Dodatkowe konfiguracje DB
    """
    print(f"\n{'='*60}")
    print("📊 TECHNICAL INDICATORS CALCULATOR")
    print('=' * 60)
    
    # Twórcza instancja
    calculator = IndicatorsCalculator({
        'host': db_host,
        **db_config
    })
    
    # Oblicz wskaźniki
    result = calculator.calculate_indicators(years_back=years_back)
    
    return {
        **result,
        'status': 'success' if result.get('records_calculated', 0) > 0 else 'no_data'
    }


if __name__ == "__main__":
    # Przykładowe użycie
    result = calculate_technical_indicators(
        db_host='localhost',
        user='root',  # Dodaj swoje dane logowania
        password='',   # Dodaj hasło
        years_back=4
    )
    
    print(f"\n📊 Obliczone rekordy: {result.get('records_calculated', 0)}")