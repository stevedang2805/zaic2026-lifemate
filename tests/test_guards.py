"""Scripted-LLM tests of the agent guards (no GPU). Run: python tests/test_guards.py --root data"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lifemate.agent import run_agent  # noqa: E402
from lifemate.run import load_catalog_tools, make_transcriber  # noqa: E402


def tc(name, args):
    return f"<tool_call>{json.dumps({'name': name, 'arguments': args}, ensure_ascii=False)}</tool_call>"


def drive(item, env, cat, script):
    tr = make_transcriber("gold", {item["audio"]: item})
    g = run_agent(item, env, cat, tr)
    msgs = []
    try:
        m, _ = next(g)
        for out in script:
            m, _ = g.send(out)
            msgs.append(m[-1])
        g.send("Xong.")
    except StopIteration as e:
        return env.get_tool_calls(), e.value, msgs
    raise AssertionError("agent did not stop")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    root = Path(ap.parse_args().root).resolve()
    sys.path.insert(0, str(root / "train"))
    from zaic_tools import ToolEnv
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(root / "train/train.jsonl", encoding="utf-8")}
    cat = load_catalog_tools(root, "train")
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok &= bool(cond)

    # train_0030: banking transfer (get_balance, list_beneficiaries, transfer)
    it = rows["train_0030"]
    g = it["label"]["tool_calls"]
    env = ToolEnv("train", it["id"], root=root)
    amt = g[2]["arguments"]["amount"]
    script = [
        tc(g[0]["name"], {}),
        tc(g[0]["name"], {}),                                   # duplicate read -> not executed
        tc(g[1]["name"], {}),
        tc("banking.transfer", {**g[2]["arguments"], "beneficiary_id": "ben_999"}),  # unseen id -> warned
        tc("banking.transfer", {**g[2]["arguments"], "amount": f"{amt:,}"}),        # "1,200,000" string -> cast int
    ]
    calls, trace, _ = drive(it, env, cat, script)
    check("duplicate read skipped", [c["name"] for c in calls].count(g[0]["name"]) == 1)
    check("hallucinated id not executed", all(c["arguments"].get("beneficiary_id") != "ben_999" for c in calls))
    check("amount string cast to int, call matches gold", calls == g)

    # schema error: missing required -> never logged
    env = ToolEnv("train", it["id"], root=root)
    calls, trace, msgs = drive(it, env, cat, [tc("banking.transfer", {"amount": 5}), tc("tool.khong_ton_tai", {})])
    check("schema-invalid calls not logged", calls == [])
    check("schema error fed back", any("LỖI" in (m.get("content") or "") for m in msgs))

    # malformed JSON -> retry, then a valid call
    env = ToolEnv("train", it["id"], root=root)
    calls, trace, _ = drive(it, env, cat, ['<tool_call>{"name": "banking.get_balance", "arguments": {</tool_call>', tc("banking.get_balance", {})])
    check("malformed output recovered", [c["name"] for c in calls] == ["banking.get_balance"])

    # ask_missing stops the loop
    env = ToolEnv("train", it["id"], root=root)
    calls, trace, _ = drive(it, env, cat, [tc("sys.ask_missing_info", {"tool_name": "banking.transfer", "params": ["amount"]}),
                                           tc("banking.get_balance", {})])
    check("stop after ask_missing_info", [c["name"] for c in calls] == ["sys.ask_missing_info"])

    # fresh history read is not repeated; find a sample whose history has a fresh read with results
    from lifemate.agent import history_reads, call_key
    sid = next(s for s, r in rows.items() if history_reads(r, cat))
    it = rows[sid]
    k = next(iter(history_reads(it, cat)))
    name, args = k.split("{", 1)[0], json.loads("{" + k.split("{", 1)[1])
    env = ToolEnv("train", sid, root=root)
    calls, trace, _ = drive(it, env, cat, [tc(name, args)])
    check(f"fresh history read reused ({sid} {name})", calls == [])

    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
