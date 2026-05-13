"""
DATA COLLECTION LAYER
=====================
Pobieranie danych giełdowych z różnych giełd (GPW, NASDAQ, NYSE, AMEX)
Zapis do bazy danych - 1 rekord na dzień na spółkę
"""

import psycopg2
from psycopg2 import extras
from datetime import date, timedelta
import time
import random
from typing import Dict, List, Optional, Tuple

class StockDataCollector:
    """
    Klasa do pobierania i zapisywania danych giełdowych.
    Projektuje architekturę modularną z możliwością dodawania nowych źródeł danych.
    """
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.consolidated_list = []  # Lista spółek ze wszystkich giełd
        self.tickers_cache = {}  # Cache tickerów
        
    def connect(self):
        """Łączenie z bazą danych."""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config.get('host', 'localhost'),
                user=self.db_config.get('user', 'root'),
                password=self.db_config.get('password', ''),
                database='stock_analysis_db',
                charset='utf8mb4'
            )
            print("✅ Połączono z bazą danych")
        except mysql.connector.Error as err:
            print(f"❌ Błąd połączenia: {err}")
            return False
        return True
    
    def fetch_from_gpws(self, end_date: date) -> List[Dict]:
        """
        Pobieranie danych z GPW i NewConnect.
        W prawdziwym systemie: API GPW, web scraping (gdzie dozwolone), lub podłączenie do dystrybutorów.
        
        Dla symulacji - generowanie reprezentatywnych danych:
        """
        print("📥 Pobieranie danych z GPW/NewConnect...")
        records = []
        
        # Lista spółek GPW (przykładowe)
        gpw_tickers = [
            ('GEW', 'Grupa Energetyczna W', 'Energy'),
            ('KAP', 'Kapitalistyczne Towarzystwo', 'Insurance'),
            ('JADEN', 'Jadhen Pharma', 'Pharmaceuticals'),
            ('CDR', 'Centrum Danych Rządowych', 'IT'),
            ('TME', 'Telefonia Polska', 'Telecommunications'),
        ]
        
        # Lista spółek NewConnect (technologiczne)
        newconnect_tickers = [
            ('INTEO', 'Inteo Technologies', 'Technology - AI'),
            ('DRONES', 'Dronex Solutions', 'Drones'),
            ('SILVER', 'SilverTech Mining Corp', 'Silver Mining'),
            ('GOLDX', 'Gold Extraction Ltd', 'Gold Mining'),
        ]
        
        current_date = date.today() - timedelta(days=random.randint(30, 182))
        
        while current_date <= end_date:
            # Symulacja pobierania danych dla GPW
            for ticker_symbol, full_name, sector in gpw_tickers:
                record = self._generate_price_record(
                    'GPW', ticker_symbol, full_name, sector,
                    current_date
                )
                records.append(record)
            
            # Symulacja pobierania danych z NewConnect
            for ticker_symbol, full_name, category in newconnect_tickers:
                record = self._generate_price_record(
                    'GC', ticker_symbol, full_name, category,
                    current_date
                )
                records.append(record)
            
            # Symulacja opóźnienia sieci
            time.sleep(random.uniform(0.1, 0.3))
            current_date += timedelta(days=1)
        
        return records
    
    def fetch_from_nasdaq(self, end_date: date) -> List[Dict]:
        """
        Pobieranie danych z NASDAQ.
        W prawdziwym systemie: API Nasdaq Data Link, IEX Cloud, Alpha Vantage
        """
        print("📥 Pobieranie danych z NASDAQ...")
        records = []
        
        # Przykładowe spółki technologiczne z NASDAQ
        nasdaq_tickers = [
            ('NVDA', 'NVIDIA Corporation', 'Semiconductors - AI'),
            ('AAPL', 'Apple Inc.', 'Technology - Consumer Electronics'),
            ('MSFT', 'Microsoft Corporation', 'Software & Services - AI'),
            ('AMD', 'Advanced Micro Devices', 'Semiconductors'),
            ('AVGO', 'Broadcom Inc.', 'Semiconductors'),
        ]
        
        current_date = date.today() - timedelta(days=random.randint(30, 182))
        
        while current_date <= end_date:
            for ticker_symbol, full_name, category in nasdaq_tickers:
                record = self._generate_price_record(
                    'NASDAQ', ticker_symbol, full_name, category,
                    current_date
                )
                records.append(record)
            
            time.sleep(random.uniform(0.1, 0.3))
            current_date += timedelta(days=1)
        
        return records
    
    def fetch_from_nyse(self, end_date: date) -> List[Dict]:
        """
        Pobieranie danych z NYSE.
        W prawdziwym systemie: API NYSE (przez IEX, Alpha Vantage)
        """
        print("📥 Pobieranie danych z NYSE...")
        records = []
        
        # Przykładowe spółki przemysłowe i inne
        nyse_tickers = [
            ('JPM', 'JPMorgan Chase & Co.', 'Banks'),
            ('XOM', 'Exxon Mobil Corporation', 'Oil & Gas'),
            ('GS', 'Goldman Sachs Group', 'Securities'),
            ('BA', 'Boeing Company', 'Aerospace - Space Industry'),
            ('HON', 'Honeywell International', 'Industrial Conglomerates'),
        ]
        
        current_date = date.today() - timedelta(days=random.randint(30, 182))
        
        while current_date <= end_date:
            for ticker_symbol, full_name, category in nyse_tickers:
                record = self._generate_price_record(
                    'NYSE', ticker_symbol, full_name, category,
                    current_date
                )
                records.append(record)
            
            time.sleep(random.uniform(0.1, 0.3))
            current_date += timedelta(days=1)
        
        return records
    
    def fetch_from_amex(self, end_date: date) -> List[Dict]:
        """
        Pobieranie danych z AMEX (NYSE American).
        W prawdziwym systemie: API przez IEX lub podległość do NYSE
        """
        print("📥 Pobieranie danych z AMEX...")
        records = []
        
        # Przykładowe spółki surowcowe, metalurgiczne
        amex_tickers = [
            ('SLV', 'iShares Silver Trust', 'Silver Mining'),
            ('GDXJ', 'VanEck Junior Gold Miners ETF', 'Gold Mining'),
            ('ALB', 'Albemarle Corporation', 'Lithium Mining'),
            ('FCX', 'Freeport-McMoRan Inc.', 'Copper Mining'),
        ]
        
        current_date = date.today() - timedelta(days=random.randint(30, 182))
        
        while current_date <= end_date:
            for ticker_symbol, full_name, category in amex_tickers:
                record = self._generate_price_record(
                    'AMEX', ticker_symbol, full_name, category,
                    current_date
                )
                records.append(record)
            
            time.sleep(random.uniform(0.1, 0.3))
            current_date += timedelta(days=1)
        
        return records
    
    def _generate_price_record(
        self,
        exchange_code: str,
        ticker_symbol: str,
        full_name: str,
        category: str,
        calc_date: date
    ) -> Dict:
        """
        Generuje reprezentatywny rekord cenowy.
        W prawdziwej implementacji - pobieranie z API/scrapersa.
        
        Modelowanie realistycznych ruchów cenowych:
        - Trend z małą zmiennością (random walk)
        - Realistyczne relacje OHLCV
        """
        # Pobierz ostatnią cenę
        cursor = self.connection.cursor(dictionary=True)
         # Resolve exchange_id from code
         cursor.execute("SELECT exchange_id FROM exchanges WHERE code = %s", (exchange_code,))
         exch_row = cursor.fetchone()
         exchange_id = exch_row['exchange_id'] if exch_row else None
         query = """
             SELECT close, open 
             FROM raw_price_data 
             WHERE ticker_id = %s AND exchange_id = %s
             ORDER BY date DESC LIMIT 1
         """
         cursor.execute(query, (None, exchange_id))
        last_record = cursor.fetchone()
        
        # Jeśli brak danych, generuj losowy start
        if not last_record:
            base_price = random.uniform(50.0, 500.0)
            current_close = base_price
            prev_close = base_price
        else:
            current_close = last_record['close']
            prev_close = last_record.get('open', current_close)
        
        # Parametry modelu random walk
        drift = 0.0002  # Lekki wzrost długoterminowy
        volatility = 0.015  # Zmienność dzienna (ok 1.5%)
        
        # Generuj ruch ceny
        daily_return = (drift + random.gauss(0, volatility))
        new_close = current_close * (1 + daily_return)
        
        # Oblicz pozostałe wartości OHLCV
        open_price = prev_close * (1 + random.gauss(-0.0005, 0.003))  # Mała luka otwarcia
        high = max(new_close, open_price) * (1 + abs(random.gauss(0, 0.01)))
        low = min(new_close, open_price) * (1 - abs(random.gauss(0, 0.01)))
        volume = int(abs(daily_return) * new_close * random.uniform(1e6, 1e8))  # Wolumen zależny od ruchu
        
        # Utwórz rekord
        record = {
            'ticker_id': None,  # Ustawione później przez upsert
            'exchange_id': exchange_map.get(exchange_code, 0),
            'date': calc_date,
            'open': round(open_price, 6),
            'high': round(high, 6),
            'low': round(low, 6),
            'close': round(new_close, 6),
            'volume': max(0, volume)
        }
        
        return record
    
    def upsert_raw_price_data(
        self,
        records: List[Dict],
        tickers_cache: Dict[str, Tuple[int, str]]
    ) -> int:
        """
        Batchowy zapis danych do tabeli raw_price_data.
        Upsert - jeśli ticker nie istnieje, dodaj go.
        """
        inserted = 0
        cursor = self.connection.cursor(dictionary=True)
        
        # Bulk insert dla tickerów (upsert)
        tickers_insert_query = """
            INSERT IGNORE INTO tickers (exchange_id, symbol, full_name, sector)
            VALUES (%s, %s, %s, %s)
        """
        
        exchange_map = {
            'GPW': 1,
            'GC': 2,
            'NASDAQ': 3,
            'NYSE': 4,
            'AMEX': 5
        }
        
        # Zbierz unikalne tickery i wstaw do bazy
        unique_tickers = {}
        for record in records:
            key = (record['exchange_code'], record['symbol'])
            if key not in unique_tickers:
                exchange_id = exchange_map.get(record['exchange_code'], 0)
                unique_tickers[key] = (
                    exchange_id,
                    record['symbol'],
                    record['full_name'],
                    record['category']
                )
        
        # Wstaw tickery
        cursor.executemany(tickers_insert_query, [list(unique_tickers.values())])
        self.connection.commit()
        print(f"   ➜ Dodano {len(unique_tickers)} unikalnych tickerów")
        
        # Upsert z danymi cenowymi
        upsert_query = """
            INSERT INTO raw_price_data 
                (ticker_id, exchange_id, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume)
        """
        
        for record in records:
            # Pobierz ticker_id
            cursor.execute("""
                SELECT ticker_id FROM tickers
                WHERE exchange_id = %s AND symbol = %s
""", (unique_tickers[(record['exchange_id'], record['symbol'])][0],
                    record['symbol']))
            result = cursor.fetchone()
            ticker_id = result[0] if result else None
            
            if ticker_id:
                values = (
                    ticker_id,
                    exchange_map.get(record['exchange_code'], 0),
                    record['date'],
                    record['open'],
                    record['high'],
                    record['low'],
                    record['close'],
                    record['volume']
                )
                cursor.execute(upsert_query, values)
                inserted += 1
        
        self.connection.commit()
        print(f"   ➜ Zapisano {inserted} rekordów cenowych")
        return inserted
    
    def collect_all_exchanges(self, start_date: date, end_date: date) -> Dict[str, List[Dict]]:
        """
        Główna metoda kolekcji danych ze wszystkich giełd.
        Zwraca słownik z danymi z każdej giełdy.
        """
        print(f"\n📊 Kolekcja danych: {start_date} do {end_date}")
        print("=" * 50)
        
        all_records = {}
        
        # Pobierz dane z każdej giełdy
        all_records['GPW/NewConnect'] = self.fetch_from_gpws(end_date)
        all_records['NASDAQ'] = self.fetch_from_nasdaq(end_date)
        all_records['NYSE'] = self.fetch_from_nyse(end_date)
        all_records['AMEX'] = self.fetch_from_amex(end_date)
        
        # Zsumuj wszystkie rekordy
        total_records = sum(len(v) for v in all_records.values())
        print(f"\n📈 Łączna liczba rekordów: {total_records}")
        return all_records
    
    def save_tick_to_db(
        self,
        records: List[Dict],
        tickers_cache: Dict[str, Tuple[int, str]] = None
    ) -> int:
        """
        Zapis danych z pojedynczego źródła do bazy.
        """
        if not self.connection:
            print("❌ Brak połączenia z bazą")
            return 0
        
        if tickers_cache is None:
            tickers_cache = {}
        
        return self.upsert_raw_price_data(records, tickers_cache)
    
    def close_connection(self):
        """Zamykanie połączenia z bazą."""
        if self.connection:
            self.connection.close()
            print("🔌 Połączenie z bazą zamknięte")


# =============================================
# KLASA: DataLoader - Orkiestrator kolekcji danych
# =============================================

class DataLoader:
    """
    Klasa orkiestrująca proces zbierania i zapisywania danych.
    Obsługuje logowanie, retry logic, walidację.
    """
    
    def __init__(self, db_config: Dict[str, str]):
        self.collector = StockDataCollector(db_config)
        self.start_date = None
        self.end_date = None
        self.log_file = None
    
    def set_dates(self, start: date, end: date):
        """
        Ustawia zakres dat do kolekcji.
        """
        self.start_date = start
        self.end_date = end
        print(f"📅 Zakres danych: {start} → {end}")
    
    def load_data(self) -> Dict[str, List[Dict]]:
        """
        Główna metoda ładowania danych.
        Zwraca wszystkie dane lub pusty słownik w przypadku błędu.
        """
        try:
            if not self.collector.connect():
                return {}
            
            # Pobierz surowe dane
            raw_data = self.collector.collect_all_exchanges(self.start_date, self.end_date)
            
            # Zapisz do bazy
            total_inserted = 0
            for exchange_name, records in raw_data.items():
                inserted = self.collector.save_tick_to_db(records)
                total_inserted += inserted
            
            print(f"\n✅ Dane załadowane pomyślnie. Zapisano: {total_inserted} rekordów")
            return raw_data
            
        except Exception as e:
            print(f"❌ Błąd podczas ładowania danych: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def load_historical(self, years: int = 4):
        """
        Ładuje dane historyczne od roku X do teraźniejszości.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=years * 365)
        return self.load_data()
    

# =============================================
# GŁÓWNA FUNKCJA: Ładowanie danych
# =============================================

def load_stock_data(
    db_host: str = 'localhost',
    start_year: int = 2020,
    years_back: int = 4,
    **db_config
):
    """
    Główna funkcja do ładowania danych giełdowych.
    
    Args:
        db_host: Host bazy danych (default: localhost)
        start_year: Rok początkowy danych
        years_back: Ile lat danych od końca
        **db_config: Dodatkowe konfiguracje DB (user, password)
    """
    # Ustaw daty
    end_date = date.today()
    start_date = date(year=start_year, month=1, day=1)
    
    print(f"\n{'='*60}")
    print("📦 DATA LOADER - System Giełdowy")
    print('=' * 60)
    print(f"Start: {start_date} | Koniec: {end_date}")
    
    # Twórcza instancja
    loader = DataLoader({
        'host': db_host,
        **db_config
    })
    
    # Ładuj dane
    raw_data = loader.load_historical(
        years_back=years_back if start_year == 2020 else 4
    )
    
    return {
        'raw_data': raw_data,
        'start_date': start_date,
        'end_date': end_date
    }


if __name__ == "__main__":
    # Przykładowe użycie
    result = load_stock_data(
        db_host='localhost',  # Zmień na właściwy host
        start_year=2020,
        user='root',  # Dodaj swoje dane logowania
        password=''   # Dodaj hasło
    )
    
    print(f"\n📊 Ładowane rekordy: {sum(len(v) for v in result['raw_data'].values())}")