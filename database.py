import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class MealDatabase:
    def __init__(self, db_path: str = "meal_balance.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 食品マスターテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS food_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                fiber REAL DEFAULT 0
            )
        """
        )

        # 食事記録テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS meal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                food_name TEXT NOT NULL,
                amount REAL NOT NULL,
                calories REAL NOT NULL,
                protein REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                fiber REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def add_food_to_master(
        self,
        name: str,
        calories: float,
        protein: float = 0,
        fat: float = 0,
        carbs: float = 0,
        fiber: float = 0,
    ):
        """食品マスターに食品を追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO food_master (name, calories, protein, fat, carbs, fiber)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (name, calories, protein, fat, carbs, fiber),
        )
        conn.commit()
        conn.close()

    def get_all_foods(self) -> List[Dict]:
        """全ての食品マスターを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM food_master ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        foods = []
        for row in rows:
            foods.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "calories": row[2],
                    "protein": row[3],
                    "fat": row[4],
                    "carbs": row[5],
                    "fiber": row[6],
                }
            )
        return foods

    def add_meal_record(
        self,
        date: str,
        meal_type: str,
        food_name: str,
        amount: float,
        calories: float,
        protein: float = 0,
        fat: float = 0,
        carbs: float = 0,
        fiber: float = 0,
    ):
        """食事記録を追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO meal_records 
            (date, meal_type, food_name, amount, calories, protein, fat, carbs, fiber)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (date, meal_type, food_name, amount, calories, protein, fat, carbs, fiber),
        )
        conn.commit()
        conn.close()

    def get_meals_by_date(self, date: str) -> pd.DataFrame:
        """指定日付の食事記録を取得"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT id, date, meal_type, food_name, amount, calories, 
                   protein, fat, carbs, fiber, created_at
            FROM meal_records
            WHERE date = ?
            ORDER BY created_at
        """
        df = pd.read_sql_query(query, conn, params=(date,))
        conn.close()
        return df

    def get_meals_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """期間内の食事記録を取得"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT id, date, meal_type, food_name, amount, calories,
                   protein, fat, carbs, fiber, created_at
            FROM meal_records
            WHERE date BETWEEN ? AND ?
            ORDER BY date, created_at
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df

    def delete_meal_record(self, record_id: int):
        """食事記録を削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meal_records WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()

    def update_meal_record(
        self,
        record_id: int,
        date: str,
        meal_type: str,
        food_name: str,
        amount: float,
        calories: float,
        protein: float = 0,
        fat: float = 0,
        carbs: float = 0,
        fiber: float = 0,
    ):
        """食事記録を更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE meal_records
            SET date = ?, meal_type = ?, food_name = ?, amount = ?,
                calories = ?, protein = ?, fat = ?, carbs = ?, fiber = ?
            WHERE id = ?
        """,
            (
                date,
                meal_type,
                food_name,
                amount,
                calories,
                protein,
                fat,
                carbs,
                fiber,
                record_id,
            ),
        )
        conn.commit()
        conn.close()

    def get_daily_summary(self, date: str) -> Dict:
        """日別サマリーを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                SUM(calories) as total_calories,
                SUM(protein) as total_protein,
                SUM(fat) as total_fat,
                SUM(carbs) as total_carbs,
                SUM(fiber) as total_fiber
            FROM meal_records
            WHERE date = ?
        """,
            (date,),
        )
        row = cursor.fetchone()
        conn.close()

        return {
            "calories": row[0] or 0,
            "protein": row[1] or 0,
            "fat": row[2] or 0,
            "carbs": row[3] or 0,
            "fiber": row[4] or 0,
        }

    def get_period_summary(self, start_date: str, end_date: str) -> pd.DataFrame:
        """期間内のサマリーを取得"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                date,
                SUM(calories) as total_calories,
                SUM(protein) as total_protein,
                SUM(fat) as total_fat,
                SUM(carbs) as total_carbs,
                SUM(fiber) as total_fiber
            FROM meal_records
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
