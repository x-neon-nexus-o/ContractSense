"""Persistence adapters. SQLite is the zero-configuration local default; MongoDB is optional."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_json(value: str | None, fallback: Any = None) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


class SQLiteRepository:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA journal_mode=WAL")
        self.initialize()

    def initialize(self) -> None:
        with self._lock:
            self._db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contracts (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename TEXT NOT NULL, stored_path TEXT NOT NULL, contract_type TEXT NOT NULL,
                jurisdiction_state TEXT NOT NULL DEFAULT '', governing_law TEXT NOT NULL DEFAULT '',
                msme_supplier INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'uploaded',
                extracted_text TEXT NOT NULL DEFAULT '', page_count INTEGER NOT NULL DEFAULT 0,
                page_ranges_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_contract_user_created ON contracts(user_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                result_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_analysis_contract ON analyses(contract_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL, content TEXT NOT NULL, evidence_json TEXT NOT NULL DEFAULT '[]',
                legal_sources_json TEXT NOT NULL DEFAULT '[]', provider TEXT NOT NULL DEFAULT '',
                limitations TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_contract ON messages(contract_id, created_at);
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, chunk_index INTEGER NOT NULL,
                page INTEGER NOT NULL DEFAULT 0, text TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_contract ON chunks(contract_id, chunk_index);
            """)
            contract_columns = {row["name"] for row in self._db.execute("PRAGMA table_info(contracts)")}
            if "page_ranges_json" not in contract_columns:
                self._db.execute("ALTER TABLE contracts ADD COLUMN page_ranges_json TEXT NOT NULL DEFAULT '[]'")
            message_columns = {row["name"] for row in self._db.execute("PRAGMA table_info(messages)")}
            message_migrations = {
                "legal_sources_json": "TEXT NOT NULL DEFAULT '[]'",
                "provider": "TEXT NOT NULL DEFAULT ''",
                "limitations": "TEXT NOT NULL DEFAULT ''",
            }
            for column, declaration in message_migrations.items():
                if column not in message_columns:
                    self._db.execute(f"ALTER TABLE messages ADD COLUMN {column} {declaration}")
            self._db.commit()

    def _one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(sql, params).fetchone()
        return dict(row) if row else None

    def _all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def create_user(self, email: str, full_name: str, password_hash: str) -> dict[str, Any]:
        user = {"id": uuid.uuid4().hex, "email": email.lower().strip(), "full_name": full_name.strip(),
                "password_hash": password_hash, "created_at": utc_now()}
        with self._lock:
            self._db.execute("INSERT INTO users(id,email,full_name,password_hash,created_at) VALUES(?,?,?,?,?)",
                             (user["id"], user["email"], user["full_name"], user["password_hash"], user["created_at"]))
            self._db.commit()
        return user

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE email=?", (email.lower().strip(),))

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE id=?", (user_id,))

    def create_contract(self, user_id: str, filename: str, stored_path: str, contract_type: str,
                        jurisdiction_state: str = "", governing_law: str = "", msme_supplier: bool = False) -> dict[str, Any]:
        now = utc_now()
        contract = {"id": uuid.uuid4().hex, "user_id": user_id, "filename": filename,
                    "stored_path": stored_path, "contract_type": contract_type,
                    "jurisdiction_state": jurisdiction_state, "governing_law": governing_law,
                    "msme_supplier": bool(msme_supplier), "status": "uploaded", "extracted_text": "",
                    "page_count": 0, "page_ranges": [], "created_at": now, "updated_at": now}
        with self._lock:
            self._db.execute("""INSERT INTO contracts(id,user_id,filename,stored_path,contract_type,jurisdiction_state,
                governing_law,msme_supplier,status,extracted_text,page_count,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (contract["id"], user_id, filename, stored_path, contract_type,
                jurisdiction_state, governing_law, int(bool(msme_supplier)), "uploaded", "", 0, now, now))
            self._db.commit()
        return contract

    def get_contract(self, contract_id: str, user_id: str) -> dict[str, Any] | None:
        c = self._one("SELECT * FROM contracts WHERE id=? AND user_id=?", (contract_id, user_id))
        if c:
            c["msme_supplier"] = bool(c["msme_supplier"])
            c["page_ranges"] = _decode_json(c.pop("page_ranges_json", None), [])
        return c

    def list_contracts(self, user_id: str) -> list[dict[str, Any]]:
        rows = self._all("SELECT * FROM contracts WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        for c in rows:
            c["msme_supplier"] = bool(c["msme_supplier"])
        return rows

    def update_contract(self, contract_id: str, user_id: str, **fields: Any) -> None:
        allowed = {"status", "extracted_text", "page_count", "page_ranges", "jurisdiction_state", "governing_law", "msme_supplier"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if "page_ranges" in updates:
            updates["page_ranges_json"] = json.dumps(updates.pop("page_ranges"), ensure_ascii=False)
        if not updates:
            return
        updates["updated_at"] = utc_now()
        if "msme_supplier" in updates:
            updates["msme_supplier"] = int(bool(updates["msme_supplier"]))
        sql = ",".join(f"{k}=?" for k in updates)
        with self._lock:
            self._db.execute(f"UPDATE contracts SET {sql} WHERE id=? AND user_id=?",
                             (*updates.values(), contract_id, user_id))
            self._db.commit()

    def delete_contract(self, contract_id: str, user_id: str) -> bool:
        with self._lock:
            cur = self._db.execute("DELETE FROM contracts WHERE id=? AND user_id=?", (contract_id, user_id))
            self._db.commit()
            return cur.rowcount > 0

    def save_analysis(self, contract_id: str, user_id: str, result: dict[str, Any]) -> dict[str, Any]:
        item = {"id": uuid.uuid4().hex, "contract_id": contract_id, "user_id": user_id,
                "result": result, "created_at": utc_now()}
        with self._lock:
            self._db.execute("INSERT INTO analyses(id,contract_id,user_id,result_json,created_at) VALUES(?,?,?,?,?)",
                             (item["id"], contract_id, user_id, json.dumps(result, ensure_ascii=False), item["created_at"]))
            self._db.commit()
        return item

    def get_latest_analysis(self, contract_id: str, user_id: str) -> dict[str, Any] | None:
        item = self._one("SELECT * FROM analyses WHERE contract_id=? AND user_id=? ORDER BY created_at DESC LIMIT 1",
                         (contract_id, user_id))
        if item:
            item["result"] = _decode_json(item.pop("result_json"), {})
        return item

    def save_chunks(self, contract_id: str, user_id: str, chunks: list[dict[str, Any]]) -> None:
        now = utc_now()
        with self._lock:
            self._db.execute("DELETE FROM chunks WHERE contract_id=? AND user_id=?", (contract_id, user_id))
            self._db.executemany("INSERT INTO chunks(id,contract_id,user_id,chunk_index,page,text,created_at) VALUES(?,?,?,?,?,?,?)",
                [(uuid.uuid4().hex, contract_id, user_id, int(c.get("index", i)), int(c.get("page", 0)), str(c.get("text", "")), now)
                 for i, c in enumerate(chunks)])
            self._db.commit()

    def get_chunks(self, contract_id: str, user_id: str) -> list[dict[str, Any]]:
        return self._all("SELECT id,contract_id,user_id,chunk_index AS `index`,page,text,created_at FROM chunks WHERE contract_id=? AND user_id=? ORDER BY chunk_index",
                         (contract_id, user_id))

    def save_message(self, contract_id: str, user_id: str, role: str, content: str,
                     evidence: list[dict[str, Any]] | None = None,
                     legal_sources: list[dict[str, Any]] | None = None,
                     provider: str = "", limitations: str = "") -> dict[str, Any]:
        item = {"id": uuid.uuid4().hex, "contract_id": contract_id, "user_id": user_id,
                "role": role, "content": content, "evidence": evidence or [],
                "legal_sources": legal_sources or [], "provider": provider,
                "limitations": limitations, "created_at": utc_now()}
        with self._lock:
            self._db.execute("""INSERT INTO messages(
                id,contract_id,user_id,role,content,evidence_json,legal_sources_json,provider,limitations,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (item["id"], contract_id, user_id, role, content,
                 json.dumps(item["evidence"], ensure_ascii=False),
                 json.dumps(item["legal_sources"], ensure_ascii=False), provider, limitations, item["created_at"]))
            self._db.commit()
        return item

    def get_messages(self, contract_id: str, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._all("SELECT * FROM messages WHERE contract_id=? AND user_id=? ORDER BY created_at DESC LIMIT ?",
                         (contract_id, user_id, limit))
        for row in rows:
            row["evidence"] = _decode_json(row.pop("evidence_json"), [])
            row["legal_sources"] = _decode_json(row.pop("legal_sources_json", None), [])
        return list(reversed(rows))

    def dashboard_stats(self, user_id: str) -> dict[str, Any]:
        rows = self._all("SELECT a.result_json FROM analyses a JOIN contracts c ON c.id=a.contract_id WHERE a.user_id=? AND a.id IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY contract_id ORDER BY created_at DESC) AS rn FROM analyses WHERE user_id=?) WHERE rn=1)", (user_id, user_id))
        scores = []
        high = 0
        for row in rows:
            result = _decode_json(row["result_json"], {})
            scores.append(int(result.get("overall_risk_score", 0)))
            high += 1 if result.get("overall_risk_level") == "high" else 0
        total = self._one("SELECT COUNT(*) AS n FROM contracts WHERE user_id=?", (user_id,)) or {"n": 0}
        return {"contracts_total": total["n"], "analyzed_total": len(rows), "high_priority_total": high,
                "average_risk_score": round(sum(scores) / len(scores)) if scores else 0}

    def close(self) -> None:
        with self._lock:
            self._db.close()


class MongoRepository:
    """MongoDB adapter with the same public methods as SQLiteRepository."""
    def __init__(self, uri: str, database_name: str):
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise RuntimeError("MongoDB mode requires pymongo; install backend/requirements.txt") from exc
        self.client = MongoClient(uri, serverSelectionTimeoutMS=2500)
        self.db = self.client[database_name]
        self.users, self.contracts = self.db.users, self.db.contracts
        self.analyses, self.messages, self.chunks = self.db.analyses, self.db.messages, self.db.chunks
        self.initialize()

    def initialize(self):
        self.client.admin.command("ping")
        self.users.create_index("email", unique=True)
        self.contracts.create_index([("user_id", 1), ("created_at", -1)])
        self.analyses.create_index([("contract_id", 1), ("created_at", -1)])
        self.messages.create_index([("contract_id", 1), ("created_at", 1)])

    def create_user(self, email, full_name, password_hash):
        obj = {"id": uuid.uuid4().hex, "email": email.lower().strip(), "full_name": full_name.strip(),
               "password_hash": password_hash, "created_at": utc_now()}
        self.users.insert_one(obj.copy()); return obj
    def get_user_by_email(self, email): return self.users.find_one({"email": email.lower().strip()}, {"_id": 0})
    def get_user(self, user_id): return self.users.find_one({"id": user_id}, {"_id": 0})
    def create_contract(self, user_id, filename, stored_path, contract_type, jurisdiction_state="", governing_law="", msme_supplier=False):
        now = utc_now(); obj = {"id": uuid.uuid4().hex, "user_id": user_id, "filename": filename, "stored_path": stored_path,
            "contract_type": contract_type, "jurisdiction_state": jurisdiction_state, "governing_law": governing_law,
            "msme_supplier": bool(msme_supplier), "status": "uploaded", "extracted_text": "", "page_count": 0,
            "page_ranges": [], "created_at": now, "updated_at": now}; self.contracts.insert_one(obj.copy()); return obj
    def get_contract(self, contract_id, user_id): return self.contracts.find_one({"id": contract_id, "user_id": user_id}, {"_id": 0})
    def list_contracts(self, user_id): return list(self.contracts.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1))
    def update_contract(self, contract_id, user_id, **fields):
        allowed = {k:v for k,v in fields.items() if k in {"status","extracted_text","page_count","page_ranges","jurisdiction_state","governing_law","msme_supplier"}}
        if allowed: allowed["updated_at"] = utc_now(); self.contracts.update_one({"id": contract_id,"user_id": user_id},{"$set":allowed})
    def delete_contract(self, contract_id, user_id):
        result = self.contracts.delete_one({"id":contract_id,"user_id":user_id})
        if result.deleted_count:
            self.analyses.delete_many({"contract_id":contract_id,"user_id":user_id}); self.messages.delete_many({"contract_id":contract_id,"user_id":user_id}); self.chunks.delete_many({"contract_id":contract_id,"user_id":user_id})
        return bool(result.deleted_count)
    def save_analysis(self, contract_id, user_id, result):
        obj={"id":uuid.uuid4().hex,"contract_id":contract_id,"user_id":user_id,"result":result,"created_at":utc_now()}; self.analyses.insert_one(obj.copy()); return obj
    def get_latest_analysis(self, contract_id, user_id): return self.analyses.find_one({"contract_id":contract_id,"user_id":user_id},{"_id":0},sort=[("created_at",-1)])
    def save_chunks(self, contract_id, user_id, chunks):
        self.chunks.delete_many({"contract_id":contract_id,"user_id":user_id})
        if chunks: self.chunks.insert_many([{"id":uuid.uuid4().hex,"contract_id":contract_id,"user_id":user_id,"index":i,"page":int(c.get("page",0)),"text":c.get("text",""),"created_at":utc_now()} for i,c in enumerate(chunks)])
    def get_chunks(self, contract_id, user_id): return list(self.chunks.find({"contract_id":contract_id,"user_id":user_id},{"_id":0}).sort("index",1))
    def save_message(self, contract_id, user_id, role, content, evidence=None, legal_sources=None,
                     provider="", limitations=""):
        obj = {"id": uuid.uuid4().hex, "contract_id": contract_id, "user_id": user_id,
               "role": role, "content": content, "evidence": evidence or [],
               "legal_sources": legal_sources or [], "provider": provider,
               "limitations": limitations, "created_at": utc_now()}
        self.messages.insert_one(obj.copy())
        return obj

    def get_messages(self, contract_id, user_id, limit=100):
        rows = list(self.messages.find(
            {"contract_id": contract_id, "user_id": user_id}, {"_id": 0}
        ).sort("created_at", 1).limit(limit))
        for row in rows:
            row.setdefault("evidence", [])
            row.setdefault("legal_sources", [])
            row.setdefault("provider", "")
            row.setdefault("limitations", "")
        return rows
    def dashboard_stats(self, user_id):
        contracts=self.list_contracts(user_id); scores=[]; high=0
        for c in contracts:
            a=self.get_latest_analysis(c["id"],user_id)
            if a:
                result=a.get("result",{}); scores.append(int(result.get("overall_risk_score",0))); high += result.get("overall_risk_level")=="high"
        return {"contracts_total":len(contracts),"analyzed_total":len(scores),"high_priority_total":high,"average_risk_score":round(sum(scores)/len(scores)) if scores else 0}
    def close(self): self.client.close()


def create_repository(settings):
    if settings.database_backend == "mongodb":
        return MongoRepository(settings.mongodb_uri, settings.mongodb_db)
    if settings.database_backend != "sqlite":
        raise ValueError("DB_BACKEND must be 'sqlite' or 'mongodb'.")
    return SQLiteRepository(settings.sqlite_path)
