import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pmg.capture import capture_candidates
from pmg.context_pack import build_recall_context_pack
from pmg.db import connect, init_db
from pmg.repository import create_decision, create_project, create_question
from pmg.relations import add_relation
from pmg.search import search


class ProjectMemoryGraphTests(unittest.TestCase):
    def test_db_initializes_core_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pmg.sqlite"
            init_db(db)
            with connect(db) as conn:
                tables = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
                    ).fetchall()
                }
            self.assertIn("projects", tables)
            self.assertIn("relations", tables)
            self.assertIn("search_index", tables)
            self.assertIn("source_materials", tables)
            self.assertIn("ai_call_logs", tables)

    def test_project_question_decision_search_and_recall(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pmg.sqlite"
            init_db(db)
            with connect(db) as conn:
                project = create_project(
                    conn,
                    "history-track",
                    goal="追踪 AI 项目中的问题、答案、产出物、决策和上下文",
                    stage="MVP planning",
                    hot_summary="本地优先，低 token 召回。",
                )
                question = create_question(
                    conn,
                    "history-track",
                    "项目庞大时如何控制 token 消耗？",
                    summary="通过 top-k 上下文包控制 token 消耗。",
                )
                decision = create_decision(
                    conn,
                    "history-track",
                    "大型项目不加载全量历史",
                    "只召回相关上下文包，而不是读取完整项目历史。",
                )
                add_relation(
                    conn,
                    "decision",
                    decision["id"],
                    "related_to",
                    "question",
                    question["id"],
                )
                rows = search(conn, "token", project["id"])
                self.assertTrue(any(row["entity_type"] == "question" for row in rows))
                pack = build_recall_context_pack(conn, "token", "history-track")
                matched = pack["context_pack"]["matched_items"]
                self.assertEqual(matched["questions"][0]["id"], question["id"])
                self.assertEqual(matched["decisions"][0]["id"], decision["id"])

    def test_capture_candidates_extracts_multiple_types(self):
        result = capture_candidates(
            "history-track",
            "这个 Skill 是否完全依赖用户手动打点？MVP 阶段先做本地数据库，需要实现搜索。",
        )
        candidates = result["candidates"]
        self.assertTrue(candidates["questions"])
        self.assertTrue(candidates["decisions"])
        self.assertTrue(candidates["contexts"])
        self.assertTrue(candidates["tasks"])

    def test_cli_full_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pmg.sqlite"
            env = {**os.environ, "TRACK_HOME": str(Path(tmp) / "home")}
            base = [sys.executable, "-m", "track.cli", "--db", str(db)]
            subprocess.run(base + ["init"], check=True, capture_output=True, text=True, env=env)
            subprocess.run(
                base + ["history-track"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            subprocess.run(
                base
                + [
                    "this",
                    "--project",
                    "history-track",
                    "--text",
                    "项目庞大时如何控制 token 消耗？应该只召回相关上下文包。",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            recall = subprocess.run(
                base + ["recall", "token", "--project", "history-track", "--format", "json"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            data = json.loads(recall.stdout)
            self.assertTrue(data["context_pack"]["matched_items"]["questions"])

    def test_import_and_backfill_auto_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "track.sqlite"
            env = {**os.environ, "TRACK_HOME": str(Path(tmp) / "home")}
            base = [sys.executable, "-m", "track.cli", "--db", str(db)]
            note = Path(tmp) / "old.md"
            note.write_text("MVP 阶段必须默认 0 token。下一步需要实现 backfill。", encoding="utf-8")
            subprocess.run(base + ["init"], check=True, capture_output=True, text=True, env=env)
            subprocess.run(base + ["old-project"], check=True, capture_output=True, text=True, env=env)
            subprocess.run(base + ["backfill"], check=True, capture_output=True, text=True, env=env)
            subprocess.run(base + ["import", "file", "--path", str(note)], check=True, capture_output=True, text=True, env=env)
            extracted = subprocess.run(base + ["backfill", "extract"], check=True, capture_output=True, text=True, env=env)
            data = json.loads(extracted.stdout)
            self.assertTrue(data["auto_saved"]["decisions"] or data["auto_saved"]["tasks"])
            pack = subprocess.run(base + ["pack"], check=True, capture_output=True, text=True, env=env)
            self.assertIn("Track Pack", pack.stdout)


if __name__ == "__main__":
    unittest.main()
